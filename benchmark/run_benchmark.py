# -*- coding: utf-8 -*-
"""
يشغّل مجموعة الاختبار على أي محرك كشف ويطلع تقرير دقة.
الاستخدام:
    python benchmark/run_benchmark.py            # المحرك الحالي (engine)
    python benchmark/run_benchmark.py --legacy   # النسخة القديمة (مطابقة نصية فقط)
    python benchmark/run_benchmark.py --set heldout
"""
import os
import sys
import json
import argparse
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "benchmark"))


def legacy_detector(prompt: str) -> str:
    """نسخة طبق الأصل من منطق main.py الأصلي (قبل التطوير)."""
    import re
    if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+", prompt):
        return "blocked"
    if re.search(r"\b05\d{8}\b", prompt):
        return "blocked"
    if "ignore previous instructions" in prompt.lower():
        return "blocked"
    return "safe"


def engine_detector(prompt: str) -> str:
    from siyaj.engine import analyze_prompt
    return analyze_prompt(prompt)["status"]


def evaluate(cases, detector):
    per_cat = defaultdict(lambda: {"total": 0, "correct": 0, "failures": []})
    tp = fp = tn = fn = 0
    for cat, text, expected in cases:
        got = detector(text)
        ok = got == expected
        per_cat[cat]["total"] += 1
        per_cat[cat]["correct"] += int(ok)
        if not ok:
            per_cat[cat]["failures"].append(text)
        if expected == "blocked":
            tp += got == "blocked"
            fn += got != "blocked"
        else:
            tn += got == "safe"
            fp += got != "safe"
    attacks = tp + fn
    benign = tn + fp
    summary = {
        "attacks_total": attacks,
        "attacks_blocked": tp,
        "detection_rate": round(100 * tp / attacks, 1) if attacks else None,
        "benign_total": benign,
        "false_positives": fp,
        "false_positive_rate": round(100 * fp / benign, 1) if benign else None,
        "per_category": {k: {"correct": v["correct"], "total": v["total"],
                             "failures": v["failures"]} for k, v in per_cat.items()},
    }
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy", action="store_true")
    ap.add_argument("--set", default="dev", choices=["dev", "heldout"])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.set == "dev":
        from dev_set import DEV_CASES as cases
    else:
        from heldout_set import HELDOUT_CASES as cases

    detector = legacy_detector if args.legacy else engine_detector
    s = evaluate(cases, detector)
    if args.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return
    name = "النسخة القديمة" if args.legacy else "سياج v2"
    print(f"=== {name} | مجموعة: {args.set} ===")
    print(f"نسبة صد الهجمات: {s['attacks_blocked']}/{s['attacks_total']} = {s['detection_rate']}%")
    print(f"إنذارات كاذبة:   {s['false_positives']}/{s['benign_total']} = {s['false_positive_rate']}%")
    for cat, v in s["per_category"].items():
        print(f"  {cat:14s} {v['correct']}/{v['total']}")
        for f in v["failures"]:
            print(f"      ✗ {f}")


if __name__ == "__main__":
    main()
