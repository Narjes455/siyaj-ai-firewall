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
from .normalize import base_normalize, leet_views, reversed_view, decoded_views, collapsed_view
from .intent import analyze_intent
from .pii import find_pii, redact

BLOCK_THRESHOLD = 0.6

# أسماء التهديدات بالعربي (threat_type يبقى رمز إنجليزي ثابت للبرامج والإحصائيات)
THREAT_AR = {
    "PII": "بيانات شخصية",
    "Prompt Injection": "حقن أوامر",
    "Jailbreak": "كسر حماية",
    "Prompt Leaking": "تسريب تعليمات النظام",
    "Suspicious": "مشبوه",
}
OBF_AR = {
    "invisible_chars": "حروف مخفية",
    "arabic_tatweel": "تطويل عربي",
    "homoglyphs": "حروف أجنبية شبيهة",
    "letter_spacing": "مسافات بين الحروف",
}
VIEW_AR = {
    "normalized": "النص بعد التوحيد",
    "leet": "بعد تحويل الأرقام لحروف",
    "collapsed": "بعد لصق الحروف المفصولة",
    "reversed": "النص مقلوب",
    "base64": "بعد فك تشفير Base64",
    "hex": "بعد فك تشفير Hex",
}
OBFUSCATION_BONUS = 0.1


def _mask(value: str) -> str:
    """نعرض أول وآخر جزء فقط عشان الرد نفسه ما يسرّب البيانات."""
    v = value.strip()
    if len(v) <= 6:
        return "****"
    return v[:3] + "****" + v[-2:]


def analyze_prompt(prompt: str) -> dict:
    # --- PII ---
    pii = find_pii(prompt)
    if pii:
        return {
            "status": "blocked",
            "threat_type": "PII",
            "threat_type_ar": THREAT_AR["PII"],
            "reason": "تم اكتشاف: " + "، ".join(sorted({k for k, _ in pii})),
            "risk_score": 100,
            "evidence": [f"{k}: {_mask(v)}" for k, v in pii],
            "redacted_prompt": redact(prompt, pii),
        }

    # --- مناظير النص ---
    norm, obfuscations = base_normalize(prompt)
    views = [("normalized", norm)]
    for lv in leet_views(norm):
        views.append(("leet", lv))
    if "letter_spacing" in obfuscations:
        views.append(("collapsed", collapsed_view(norm)))
    views.append(("reversed", reversed_view(norm)))
    for enc, decoded in decoded_views(prompt):
        dnorm, dob = base_normalize(decoded)
        views.append((enc, dnorm))
        obfuscations += dob

    best = (0.0, None, [], "normalized")
    exec_encoded = False
    for name, text in views:
        score, cat, signals, ex = analyze_intent(text, loose=(name == "collapsed"),
                                              skel=(name == "leet"))
        exec_encoded = exec_encoded or ex
        if score > best[0]:
            best = (score, cat, signals, name)

    score, category, signals, view = best
    evidence = list(signals)

    # الهجوم اللي ما يظهر إلا بعد فك التمويه = أخطر (تعمّد إخفاء)
    if view != "normalized" and score > 0:
        obfuscations.append(f"الهجوم ظهر فقط {VIEW_AR.get(view, view)}")
    if obfuscations and score > 0:
        score += OBFUSCATION_BONUS
        names = [OBF_AR.get(o, o) for o in obfuscations]
        evidence.append("تمويه: " + "، ".join(dict.fromkeys(names)))
    if view in ("base64", "hex", "reversed") and exec_encoded:
        score += 0.1
        evidence.append("يطلب من النموذج فك محتوى مخفي وتنفيذه")

    score = min(score, 1.0)
    risk = round(score * 100)

    if score >= BLOCK_THRESHOLD:
        return {
            "status": "blocked",
            "threat_type": category,
            "threat_type_ar": THREAT_AR.get(category, category),
            "reason": f"تم اكتشاف {THREAT_AR.get(category, category)}",
            "risk_score": risk,
            "evidence": evidence,
            "detected_in_view": VIEW_AR.get(view, view),
        }
    return {
        "status": "safe",
        "threat_type": "None",
        "threat_type_ar": "لا يوجد",
        "reason": "الطلب سليم",
        "risk_score": risk,
        "evidence": evidence,
        "clean_prompt": prompt,
    }
