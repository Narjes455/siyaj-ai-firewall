# -*- coding: utf-8 -*-
"""
الطبقة 3: كشف البيانات الشخصية (PII) مع تحقق رياضي.

بدل ما نحظر أي رقم من 10 خانات (يسبب إنذارات كاذبة كثيرة)، نتحقق من صحة الرقم:
- الهوية الوطنية/الإقامة: خوارزمية Luhn + تبدأ بـ 1 أو 2
- الآيبان السعودي: خوارزمية ISO 13616 (mod 97)
- البطاقات البنكية: خوارزمية Luhn + طول 13-19
- الجوال السعودي: كل الصيغ (05 / 5 / 966 / +966 / 00966) مع مسافات أو شرطات
- الإيميل: الصيغة العادية والمموّهة (name [at] gmail [dot] com)
"""
import re
from .normalize import to_ascii_digits, INVISIBLE

EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
EMAIL_OBF = re.compile(
    r"[a-zA-Z0-9._%+-]{2,}\s*[\[\(\{<]\s*(?:at|@|ات)\s*[\]\)\}>]\s*[a-zA-Z0-9-]+"
    r"\s*(?:[\[\(\{<]\s*(?:dot|\.|دوت)\s*[\]\)\}>]|\s+dot\s+)\s*[a-zA-Z]{2,6}\b",
    re.I,
)
EMAIL_WORDS = re.compile(
    r"\b[a-zA-Z0-9._%+-]{2,}\s+at\s+(?:gmail|hotmail|outlook|yahoo|icloud|live)\s+dot\s+[a-z]{2,6}\b",
    re.I,
)
DIGIT_RUN = re.compile(r"(?<![\d/])\+?\d(?:[ \-]?\d){8,22}(?![\d/])")
IBAN_SA = re.compile(r"\bSA\s?\d{2}(?:\s?[0-9A-Z]{4}){5}\b", re.I)
PHONE_SA = re.compile(r"^(?:\+?966|00966|0)?5\d{8}$")


def luhn_ok(num: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(num)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def iban_ok(iban: str) -> bool:
    s = re.sub(r"\s", "", iban).upper()
    if len(s) != 24:
        return False
    s = s[4:] + s[:4]
    num = "".join(str(int(c, 36)) for c in s)
    return int(num) % 97 == 1


def find_pii(raw: str):
    """يرجّع قائمة (النوع، القيمة) لكل بيانات شخصية مكتشفة."""
    text = to_ascii_digits(INVISIBLE.sub("", raw))
    found = []

    for m in EMAIL.finditer(text):
        found.append(("بريد إلكتروني", m.group(0)))
    for rx in (EMAIL_OBF, EMAIL_WORDS):
        for m in rx.finditer(text):
            found.append(("بريد إلكتروني مموّه", m.group(0)))

    for m in IBAN_SA.finditer(text):
        if iban_ok(m.group(0)):
            found.append(("آيبان سعودي", m.group(0)))

    for m in DIGIT_RUN.finditer(text):
        token = m.group(0)
        digits = re.sub(r"[^\d]", "", token)
        if PHONE_SA.match(re.sub(r"[ \-]", "", token)):
            found.append(("رقم جوال سعودي", token))
        elif len(digits) == 10 and digits[0] in "12" and luhn_ok(digits):
            kind = "رقم هوية وطنية" if digits[0] == "1" else "رقم إقامة"
            found.append((kind, token))
        elif 13 <= len(digits) <= 19 and luhn_ok(digits):
            found.append(("بطاقة دفع", token))

    return found


def redact(raw: str, items):
    out = raw
    for kind, value in items:
        out = out.replace(value, f"[تم إخفاء {kind}]")
    return out
