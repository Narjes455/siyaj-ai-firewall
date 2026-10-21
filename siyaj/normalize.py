# -*- coding: utf-8 -*-
"""
الطبقة 1: توحيد النص وكشف التمويه.

الفكرة: المهاجم يغيّر "شكل" النص بدون ما يغيّر "معناه" (مسافات بين الحروف،
حروف شبيهة من لغات ثانية، أرقام بدل حروف، تشكيل وتطويل، نص مقلوب، تشفير).
هذي الطبقة ترجّع النص لشكله الأساسي وتولّد "مناظير" (views) متعددة منه،
وتسجّل كل أسلوب تمويه اكتشفته كدليل إضافي على سوء النية.
"""
import base64
import binascii
import re
import unicodedata

# حروف لا تُرى (zero-width, bidi controls, BOM)
INVISIBLE = re.compile(r"[​-‏‪-‮⁠-⁤﻿­]")
# التشكيل العربي + الألف الخنجرية
TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
TATWEEL = "ـ"

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

ARABIC_LETTERS = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ى": "ي", "ئ": "ي", "ؤ": "و", "ة": "ه",
})

# حروف سيريلية/يونانية تشبه اللاتينية (homoglyphs)
HOMOGLYPHS = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x",
    "і": "i", "ј": "j", "ѕ": "s", "ԁ": "d", "ɡ": "g", "һ": "h", "ӏ": "l",
    "А": "a", "В": "b", "Е": "e", "К": "k", "М": "m", "Н": "h", "О": "o",
    "Р": "p", "С": "c", "Т": "t", "Х": "x", "Ү": "y",
    "α": "a", "ο": "o", "ν": "v", "ι": "i", "κ": "k", "τ": "t", "ρ": "p",
    "Ο": "o", "Α": "a", "Ε": "e", "Ι": "i",
})

LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
                      "7": "t", "@": "a", "$": "s", "!": "i", "|": "l"})


def to_ascii_digits(text: str) -> str:
    return text.translate(ARABIC_DIGITS)


def base_normalize(text: str):
    """توحيد أساسي. يرجّع (النص الموحّد، قائمة أساليب التمويه المكتشفة)."""
    found = []
    t = unicodedata.normalize("NFKC", text)

    if INVISIBLE.search(t):
        found.append("invisible_chars")
        t = INVISIBLE.sub("", t)

    if TATWEEL in t:
        # التطويل بين حروف كل كلمة تقريباً = تمويه؛ مرة وحدة ممكن تكون زخرفة عادية
        if t.count(TATWEEL) >= 3:
            found.append("arabic_tatweel")
        t = t.replace(TATWEEL, "")

    if TASHKEEL.search(t):
        t = TASHKEEL.sub("", t)  # التشكيل مو بالضرورة تمويه، نزيله بصمت

    if any(ch in t for ch in "аеорсухіјѕАВЕКМНОРСТХαονικτρ"):
        if re.search(r"[a-zA-Z]", t):  # خلط لاتيني + سيريلي/يوناني داخل نص لاتيني
            found.append("homoglyphs")
        t = t.translate(HOMOGLYPHS)

    # إزالة علامات الحروف اللاتينية (précédentes -> precedentes) بدون لمس العربي
    t = "".join(ch for ch in unicodedata.normalize("NFKD", t)
                if not (unicodedata.combining(ch) and ord(ch) < 0x0600))
    t = unicodedata.normalize("NFC", t)
    t = to_ascii_digits(t)
    t = t.translate(ARABIC_LETTERS)
    t = t.lower()
    t = re.sub(r"[_\-\.\*~`'\"]+", " ", t)

    # "I g n o r e   p r e v" -> "ignore   prev"  (حروف مفردة بينها مسافة وحدة)
    spaced = re.sub(r"(?<=\b\w) (?=\w\b)", "", t)
    if spaced != t and re.search(r"(?:\b\w ){4,}\w\b", t):
        found.append("letter_spacing")
        t = spaced

    t = re.sub(r"\s+", " ", t).strip()
    return t, found


LEET_L = str.maketrans({"1": "l"})


def leet_views(t: str):
    """منظوران يحوّلان الأرقام داخل الكلمات لحروف (1gn0r3 -> ignore).
    الرقم 1 غامض (i أو l) فنولّد الاحتمالين."""
    outs = []
    for pre in (None, LEET_L):
        def fix(m):
            w = m.group(0)
            if re.search(r"[a-z]", w) and re.search(r"[0-9@$!|]", w):
                return (w.translate(pre) if pre else w).translate(LEET)
            return w
        o = re.sub(r"[a-z0-9@$!|]+", fix, t)
        if o != t and o not in outs:
            outs.append(o)
    return outs


def collapsed_view(raw_norm: str):
    """للنص اللي كل حروفه مفصولة (i.g.n.o.r.e a.l.l) فتضيع حدود الكلمات:
    نلصق كل شي ونحلل بدون حدود كلمات."""
    return re.sub(r"\s+", "", raw_norm)


def reversed_view(t: str) -> str:
    return t[::-1]


B64_TOKEN = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")
HEX_TOKEN = re.compile(r"\b(?:[0-9a-fA-F]{2}){10,}\b")


def _printable_ratio(s: str) -> float:
    if not s:
        return 0.0
    ok = sum(ch.isprintable() or ch.isspace() for ch in s)
    return ok / len(s)


def decoded_views(raw: str):
    """يحاول فك Base64 و Hex المضمّنة في النص."""
    out = []
    for tok in B64_TOKEN.findall(raw):
        try:
            padded = tok + "=" * (-len(tok) % 4)
            s = base64.b64decode(padded, validate=True).decode("utf-8")
            if _printable_ratio(s) > 0.95 and re.search(r"[a-zA-Z؀-ۿ]{3}", s):
                out.append(("base64", s))
        except (binascii.Error, UnicodeDecodeError, ValueError):
            pass
    for tok in HEX_TOKEN.findall(raw):
        try:
            s = bytes.fromhex(tok).decode("utf-8")
            if _printable_ratio(s) > 0.95:
                out.append(("hex", s))
        except (ValueError, UnicodeDecodeError):
            pass
    return out
