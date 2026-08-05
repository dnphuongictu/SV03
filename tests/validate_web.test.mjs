import test from "node:test";
import assert from "node:assert/strict";
import { validateRows, summarize, normalizeUtterance } from "../demo/validate.js";

function item(overrides = {}) {
  return {
    id: "V1",
    utterance: "Goi cho me",
    language: "vi",
    intent: "call_contact",
    arguments: { contact: "me" },
    risk_level: "medium",
    split: "train",
    ...overrides,
  };
}

test("valid row has no errors", () => {
  assert.deepEqual(validateRows([item()]), []);
});

test("missing required argument is caught", () => {
  assert.ok(validateRows([item({ arguments: {} })]).length > 0);
});

test("split leakage across normalized utterance is caught", () => {
  const errors = validateRows([item(), item({ id: "V2", split: "test" })]);
  assert.ok(errors.some((e) => e.includes("ro ri utterance")));
});

test("duplicate id is caught", () => {
  const errors = validateRows([item(), item()]);
  assert.ok(errors.some((e) => e.includes("trung id")));
});

test("invalid intent is caught", () => {
  const errors = validateRows([item({ intent: "delete_everything" })]);
  assert.ok(errors.some((e) => e.includes("intent khong hop le")));
});

test("clarify without missing list is caught", () => {
  const errors = validateRows([
    item({ id: "V3", intent: "clarify", arguments: {}, utterance: "Nhan cho Nam" }),
  ]);
  assert.ok(errors.some((e) => e.includes("clarify can danh sach missing")));
});

test("unsupported needs no arguments", () => {
  const errors = validateRows([
    item({ id: "V4", intent: "unsupported", arguments: {}, utterance: "Dat ve may bay re nhat" }),
  ]);
  assert.deepEqual(errors, []);
});

test("normalizeUtterance strips punctuation/case like the Python validator", () => {
  assert.equal(normalizeUtterance("Đặt báo thức 6 giờ!"), "t bo thc 6 gi");
});

test("summarize matches the shape produced by vidroid_validator.py", () => {
  const summary = summarize([item(), item({ id: "V2", utterance: "Mo ban do", intent: "open_map", arguments: { destination: "truong" }, split: "validation" })]);
  assert.equal(summary.n, 2);
  assert.equal(summary.unique_utterance_rate, 1);
  assert.deepEqual(summary.intent_counts, { call_contact: 1, open_map: 1 });
});
