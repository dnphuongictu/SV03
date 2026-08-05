// Cổng JavaScript của src/vidroid_validator.py — phải giữ đúng cùng luật
// kiểm định để CLI (Python) và web tool (JS) không lệch nhau. Có test
// tương ứng ở tests/test_validate_web.mjs.

export const INTENTS = new Set([
  "set_alarm", "set_timer", "call_contact", "send_sms",
  "open_map", "open_app", "unsupported", "clarify",
]);

export const REQUIRED_ARGS = {
  set_alarm: [["hour"]],
  set_timer: [["duration_minutes", "seconds"]],
  call_contact: [["contact"]],
  send_sms: [["contact"], ["message"]],
  open_map: [["destination"]],
  open_app: [["app_name"]],
};

export const ARG_FIELDS = {
  set_alarm: [
    { key: "hour", label: "Giờ (0-23)", type: "number" },
    { key: "minute", label: "Phút (0-59)", type: "number" },
    { key: "date", label: "Ngày (vd today/tomorrow)", type: "text" },
    { key: "label", label: "Ghi chú báo thức", type: "text" },
  ],
  set_timer: [
    { key: "duration_minutes", label: "Số phút", type: "number" },
    { key: "seconds", label: "Số giây (thay thế)", type: "number" },
    { key: "label", label: "Ghi chú hẹn giờ", type: "text" },
  ],
  call_contact: [{ key: "contact", label: "Người nhận cuộc gọi", type: "text" }],
  send_sms: [
    { key: "contact", label: "Người nhận SMS", type: "text" },
    { key: "message", label: "Nội dung SMS", type: "text" },
  ],
  open_map: [{ key: "destination", label: "Điểm đến", type: "text" }],
  open_app: [{ key: "app_name", label: "Tên ứng dụng", type: "text" }],
  unsupported: [],
  clarify: [{ key: "missing", label: "Trường còn thiếu (cách nhau bởi dấu phẩy)", type: "text" }],
};

const REQUIRED_FIELDS = ["id", "utterance", "language", "intent", "arguments", "risk_level", "split"];

export function normalizeUtterance(text) {
  return String(text).toLowerCase().replace(/[^a-z0-9 ]/g, "").trim();
}

export function validateRows(rows) {
  const errors = [];
  const ids = new Set();
  const utteranceSplits = new Map();

  rows.forEach((r, idx) => {
    const n = idx + 1;
    const missingFields = REQUIRED_FIELDS.filter((f) => !(f in r));
    missingFields.forEach((f) => errors.push(`Dong ${n}: thieu ${f}`));
    if (missingFields.length) return;

    if (ids.has(r.id)) errors.push(`Dong ${n}: trung id ${r.id}`);
    ids.add(r.id);

    if (!INTENTS.has(r.intent)) errors.push(`Dong ${n}: intent khong hop le`);

    if (typeof r.arguments !== "object" || r.arguments === null || Array.isArray(r.arguments)) {
      errors.push(`Dong ${n}: arguments phai la object`);
      return;
    }

    for (const alternatives of REQUIRED_ARGS[r.intent] || []) {
      const hasOne = alternatives.some((key) => {
        const v = r.arguments[key];
        return v !== undefined && v !== null && v !== "";
      });
      if (!hasOne) errors.push(`Dong ${n}: ${r.intent} thieu ${alternatives.join("/")}`);
    }

    if (r.intent === "clarify") {
      const missing = r.arguments.missing;
      const hasMissing = Array.isArray(missing) ? missing.length > 0 : Boolean(missing);
      if (!hasMissing) errors.push(`Dong ${n}: clarify can danh sach missing`);
    }

    const key = normalizeUtterance(r.utterance);
    const old = utteranceSplits.get(key);
    if (old && old !== r.split) errors.push(`Dong ${n}: ro ri utterance giua split ${old} va ${r.split}`);
    utteranceSplits.set(key, r.split);
  });

  return errors;
}

export function summarize(rows) {
  const count = (values) => values.reduce((acc, v) => {
    acc[v] = (acc[v] || 0) + 1;
    return acc;
  }, {});
  const uniqueUtterances = new Set(rows.map((r) => normalizeUtterance(r.utterance)));
  return {
    n: rows.length,
    intent_counts: count(rows.map((r) => r.intent)),
    split_counts: count(rows.map((r) => r.split)),
    risk_counts: count(rows.map((r) => r.risk_level)),
    unique_utterance_rate: rows.length ? Math.round((uniqueUtterances.size / rows.length) * 1000) / 1000 : 0,
  };
}
