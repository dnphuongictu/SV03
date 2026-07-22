"""Schema/business-rule validator for the student ViDroidCall dataset."""
import argparse, json, re
from collections import Counter
from pathlib import Path

INTENTS={"set_alarm","set_timer","call_contact","send_sms","open_map","open_app","unsupported","clarify"}
REQUIRED_ARGS={"set_alarm":[("hour",)],"set_timer":[("duration_minutes","seconds")],"call_contact":[("contact",)],"send_sms":[("contact",),("message",)],"open_map":[("destination",)],"open_app":[("app_name",)]}

def load(path):
    rows=[]
    for n,line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(),1):
        if line.strip():
            try: rows.append(json.loads(line))
            except json.JSONDecodeError as e: raise ValueError(f"Dong {n}: JSON loi: {e.msg}")
    return rows

def norm(text): return re.sub(r"[^a-z0-9 ]","",text.lower()).strip()
def validate(rows):
    errors=[]; ids=set(); utterance_splits={}
    for n,r in enumerate(rows,1):
        for f in ("id","utterance","language","intent","arguments","risk_level","split"):
            if f not in r: errors.append(f"Dong {n}: thieu {f}")
        if errors and any(x.startswith(f"Dong {n}:") for x in errors): continue
        if r["id"] in ids: errors.append(f"Dong {n}: trung id {r['id']}")
        ids.add(r["id"])
        if r["intent"] not in INTENTS: errors.append(f"Dong {n}: intent khong hop le")
        if not isinstance(r["arguments"],dict): errors.append(f"Dong {n}: arguments phai la object"); continue
        for alternatives in REQUIRED_ARGS.get(r["intent"],[]):
            if not any(r["arguments"].get(key) not in (None,"") for key in alternatives): errors.append(f"Dong {n}: {r['intent']} thieu {'/'.join(alternatives)}")
        if r["intent"]=="clarify" and not r["arguments"].get("missing"): errors.append(f"Dong {n}: clarify can danh sach missing")
        key=norm(r["utterance"]); old=utterance_splits.get(key)
        if old and old!=r["split"]: errors.append(f"Dong {n}: ro ri utterance giua split {old} va {r['split']}")
        utterance_splits[key]=r["split"]
    return errors

def summary(rows):
    return {"n":len(rows),"intent_counts":dict(Counter(r["intent"] for r in rows)),"split_counts":dict(Counter(r["split"] for r in rows)),"risk_counts":dict(Counter(r["risk_level"] for r in rows)),"unique_utterance_rate":round(len({norm(r['utterance']) for r in rows})/len(rows),3)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("--output",default="reports/student_dataset_summary.json"); a=ap.parse_args(); rows=load(a.input); errors=validate(rows)
    if errors: raise SystemExit("Du lieu loi:\n- "+"\n- ".join(errors))
    result=summary(rows); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8"); print(f"Hop le: {result['n']} cau, {len(result['intent_counts'])} intent")
if __name__=="__main__": main()
