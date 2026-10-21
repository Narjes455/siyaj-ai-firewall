# -*- coding: utf-8 -*-
"""
محرك سياج v2 — يجمع الطبقات:

  النص الخام
     │
     ├─► طبقة PII (تحقق رياضي)  ─────────────────────────┐
     │                                                     │
     └─► طبقة التوحيد ► مناظير متعددة:                     │
            • موحّد      • leet      • مقلوب              │
            • مفكوك التشفير (Base64 / Hex)                 │
                 │                                         ▼
                 └─► طبقة تحليل النية ► درجة الخطورة ► القرار + الأدلة
"""
from .normalize import base_normalize, leet_view, reversed_view, decoded_views
from .intent import analyze_intent
from .pii import find_pii, redact

BLOCK_THRESHOLD = 0.6
OBFUSCATION_BONUS = 0.1


def analyze_prompt(prompt: str) -> dict:
    # --- PII ---
    pii = find_pii(prompt)
    if pii:
        return {
            "status": "blocked",
            "threat_type": "PII",
            "reason": ", ".join(sorted({k for k, _ in pii})) + " detected",
            "risk_score": 100,
            "evidence": [f"{k}: {v}" for k, v in pii],
            "redacted_prompt": redact(prompt, pii),
        }

    # --- مناظير النص ---
    norm, obfuscations = base_normalize(prompt)
    views = [("normalized", norm)]
    lv = leet_view(norm)
    if lv != norm:
        views.append(("leet", lv))
    views.append(("reversed", reversed_view(norm)))
    for enc, decoded in decoded_views(prompt):
        dnorm, dob = base_normalize(decoded)
        views.append((enc, dnorm))
        obfuscations += dob

    best = (0.0, None, [], "normalized")
    exec_encoded = False
    for name, text in views:
        score, cat, signals, ex = analyze_intent(text)
        exec_encoded = exec_encoded or ex
        if score > best[0]:
            best = (score, cat, signals, name)

    score, category, signals, view = best
    evidence = list(signals)

    # الهجوم اللي ما يظهر إلا بعد فك التمويه = أخطر (تعمّد إخفاء)
    if view != "normalized" and score > 0:
        obfuscations.append(f"payload_only_visible_in_{view}_view")
    if obfuscations and score > 0:
        score += OBFUSCATION_BONUS
        evidence.append("obfuscation: " + ", ".join(dict.fromkeys(obfuscations)))
    if view in ("base64", "hex", "reversed") and exec_encoded:
        score += 0.1
        evidence.append("asks model to decode/execute hidden content")

    score = min(score, 1.0)
    risk = round(score * 100)

    if score >= BLOCK_THRESHOLD:
        return {
            "status": "blocked",
            "threat_type": category,
            "reason": f"{category} detected",
            "risk_score": risk,
            "evidence": evidence,
            "detected_in_view": view,
        }
    return {
        "status": "safe",
        "threat_type": "None",
        "risk_score": risk,
        "evidence": evidence,
        "clean_prompt": prompt,
    }
