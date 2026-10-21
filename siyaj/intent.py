# -*- coding: utf-8 -*-
"""
الطبقة 2: تحليل النية (Intent Analysis) بالعربي والإنجليزي.

بدل ما نحظر عبارات ثابتة، نقسّم الهجوم لـ "مفاهيم" (فعل إلغاء، هدف = التعليمات،
لعب دور، رفع القيود، تسريب ...). الهجوم يُكتشف لما تجتمع مفاهيم معينة
قريبة من بعض داخل النص، مهما كانت الصياغة أو اللغة.
مثال: "تجاهل" لحالها سليمة ("كيف أتجاهل الناس السلبيين")،
و"التعليمات" لحالها سليمة ("تعليمات السلامة")، لكن الاثنين معاً = حقن أوامر.
"""
import re

AR_PFX = r"(?:و|ف|ب|ل|ك)?(?:ال|لل)?"  # بادئات عربية شائعة

CONCEPTS = {
    # فعل إلغاء/تجاوز
    "OVERRIDE": [
        r"ignor\w*", r"disregard\w*", r"forget\w*", r"overrid\w*", r"bypass\w*",
        r"skip\w*", r"neglect\w*", r"discard\w*", r"abandon\w*", r"drop",
        r"(?:stop|quit|cease) (?:follow|obey|using|apply)\w*",
        r"(?:do not|don t|dont|never|not|no longer) (?:follow|obey|respect|adhere|comply|stick)\w*",
        r"break (?:free|out)", r"set aside", r"throw away", r"pay no attention",
        r"تجاهل\w*", r"اتجاهل", r"انس(?:ى|ي|وا)?", r"تناس\w*", r"تخط(?:ى|ي|ا)\w*",
        r"تجاوز\w*", r"اهمل\w*", r"الغ(?:ي|ى)?\b", r"احذف", r"اترك",
        r"(?:لا|ما|بلاش) (?:تلتزم|تتبع|تطبق|تنفذ|تمشي علي|تهتم)\w*",
        r"(?:اعتبر|افترض) (?:ان|انه)? ?(?:ما ?في(?:ه)?|لا يوجد|مافي|ما عندك|ليس هناك|ما كان في(?:ه)?)",
    ],
    # الهدف: تعليمات/قواعد النموذج
    "TARGET": [
        r"instruct\w*", r"direction\w*", r"rule\w*", r"guideline\w*", r"prompt\w*",
        r"polic(?:y|ies)", r"restriction\w*", r"constraint\w*", r"filter\w*",
        r"guardrail\w*", r"programming", r"directive\w*",
        r"(?:everything|all|anything) (?:you (?:were|have been|ve been|are) )?(?:told|taught|given|said)",
        r"safety (?:settings|measures)", r"content policy",
        AR_PFX + r"تعليمات\w*", AR_PFX + r"(?:ا)?وامر\w*", AR_PFX + r"قواعد\w*",
        AR_PFX + r"قيود\w*", AR_PFX + r"ارشادات\w*", AR_PFX + r"ضوابط\w*",
        AR_PFX + r"سياس(?:ه|ات)\w*", AR_PFX + r"فلاتر\w*", AR_PFX + r"توجيهات\w*",
        AR_PFX + r"برومبت\w*", AR_PFX + r"برمجه\w*", AR_PFX + r"حدود\w*",
        r"كل (?:اللي|ما) (?:قيل|قالوا|انقال) ?(?:لك)?",
    ],
    # تحديد زمني/نطاق يقوّي الهجوم
    "SCOPE": [
        r"previous\w*", r"prior", r"above", r"before", r"earlier", r"preceding",
        r"initial", r"original", r"all", r"every\w*", r"your", r"system",
        r"from now on", r"new task", r"new instructions", r"instead",
        AR_PFX + r"سابق\w*", r"قبل", r"كل", r"جميع", AR_PFX + r"اولي\w*",
        r"\w*ك\b", r"من الحين", r"من الان", r"مهمه جديده",
    ],
    # لعب أدوار
    "ROLEPLAY": [
        r"pretend\w*", r"act(?:ing)? as", r"you are now", r"you re now", r"from now on you",
        r"role ?play\w*", r"play (?:a|the) (?:game|role)", r"imagine (?:you|that you)",
        r"simulat\w*", r"behave (?:as|like)", r"become", r"persona",
        r"تقمص\w*", r"مثل دور", r"(?:العب|خذ) دور", r"تخيل (?:انك|نفسك)",
        r"تظاهر\w*", r"صرت", r"انت الحين", r"انت الان", r"افترض انك",
    ],
    # رفع القيود
    "UNRESTRICTED": [
        r"no (?:restrictions?|rules?|limits?|limitations?|filters?|ethics|morals?|boundaries|guidelines|censorship)",
        r"without (?:any )?(?:restrictions?|rules?|limits?|filters?|ethics|censorship|guidelines)",
        r"unfilter\w*", r"uncensor\w*", r"unrestrict\w*", r"unlimited", r"unbound\w*",
        r"evil (?:ai|assistant|bot)", r"anything goes", r"no holds barred",
        r"(?:بدون|بلا|من غير|مافي|ما فيه) (?:اي )?(?:قيود|قواعد|فلاتر|حدود|اخلاق|ضوابط|رقابه)",
        r"غير مقيد", r"متحرر من",
    ],
    # كلمات كسر حماية معروفة (قوية لوحدها)
    "JAILBREAK_TOKEN": [
        r"\bdan\b", r"do anything now", r"developer mode", r"dev mode", r"jailbreak\w*",
        r"god mode", r"sudo mode", r"admin mode", r"maintenance mode", r"stan\b", r"aim mode",
        r"وضع المطور", r"وضع المسؤول", r"جيلبريك", r"كسر الحمايه",
    ],
    # أفعال التسريب
    "LEAK_VERB": [
        r"repeat\w*", r"print\w*", r"show\w*", r"reveal\w*", r"output\w*", r"display\w*",
        r"tell me", r"what (?:were|are|is)", r"give me", r"share", r"spell out", r"leak\w*",
        r"dump", r"copy", r"write (?:out|down)", r"recite",
        r"اطبع\w*", r"اعرض\w*", r"اظهر\w*", r"كرر\w*", r"اكتب\w*", r"قول لي", r"قل لي",
        r"وش (?:هي|كانت)", r"ما (?:هي|هو)", r"عطني", r"اعطني", r"ورني", r"ارسل\w*",
    ],
    # الهدف في التسريب: تعليمات النموذج نفسه (مو مفهوم عام)
    "SELF_INSTR": [
        r"(?:your|the hidden|the secret|the above|initial|original|internal|underlying|pre) ?(?:system )?(?:prompt|instructions|rules|directives|configuration)",
        r"system (?:prompt|message|instructions)(?! is)",
        r"(?:prompt|instructions|text) (?:above|before) (?:this|the) (?:conversation|chat|message)",
        r"what you were (?:told|given|instructed)",
        r"تعليماتك", r"اوامرك", r"قواعدك", r"تعليمات النظام", r"برومبت النظام",
        r"(?:التعليمات|الاوامر|البرومبت) (?:اللي|التي|الي) (?:عطاك|اعطاك|عطوك|اعطيت|وصلتك|كتبها)",
        r"(?:التعليمات|البرومبت) (?:المخفي|السري)\w*",
        r"(?:عطاك|اعطاك)\w* (?:اياها )?المطور",
    ],
    # يطلب تنفيذ محتوى مشفّر
    "EXEC_ENCODED": [
        r"(?:decode|decrypt|translate|read|convert)\w* (?:this|the following|it)?.{0,20}(?:follow|execute|do|obey|run|then)",
        r"follow (?:it|this|the decoded)", r"backwards", r"reverse\w*",
        r"(?:فك|ترجم) .{0,20}(?:نفذ|طبق|اتبع)", r"بالمقلوب",
    ],
}

COMPILED = {k: [re.compile(p) for p in v] for k, v in CONCEPTS.items()}


def _hits(text: str, concept: str):
    """يرجّع مواقع الكلمات (word index) لكل تطابق للمفهوم."""
    idx = []
    for rx in COMPILED[concept]:
        for m in rx.finditer(text):
            # نتأكد إن التطابق يبدأ عند بداية كلمة
            if m.start() > 0 and text[m.start() - 1].isalnum():
                continue
            word_pos = text.count(" ", 0, m.start())
            idx.append((word_pos, m.group(0)))
    return idx


def _near(a, b, window):
    for ia, ta in a:
        for ib, tb in b:
            if 0 <= ib - ia <= window:
                return (ta, tb)
    return None


def analyze_intent(text: str):
    """
    يحلل نص موحّد ويرجّع (درجة الخطورة 0..1، التصنيف، الأدلة).
    """
    h = {c: _hits(text, c) for c in COMPILED}
    signals = []
    score = 0.0
    category = None

    # 1) حقن أوامر: فعل إلغاء + هدف (التعليمات) خلال 8 كلمات
    pair = _near(h["OVERRIDE"], h["TARGET"], 8)
    if pair:
        s = 0.5          # لوحده مشبوه فقط ("how to ignore a rule in eslint")
        if h["SCOPE"]:
            s = 0.9      # مع نطاق (السابقة/كل/your/system) = حقن واضح
        signals.append(f"override→target: '{pair[0]}' … '{pair[1]}'")
        if s > score:
            score, category = s, "Prompt Injection"

    # 2) كسر حماية: لعب دور + رفع قيود، أو كلمة كسر حماية معروفة
    if h["JAILBREAK_TOKEN"]:
        signals.append(f"jailbreak token: '{h['JAILBREAK_TOKEN'][0][1]}'")
        if 0.8 > score:
            score, category = 0.8, "Jailbreak"
    pair = _near(h["ROLEPLAY"], h["UNRESTRICTED"], 14)
    if pair:
        signals.append(f"roleplay→unrestricted: '{pair[0]}' … '{pair[1]}'")
        if 0.85 > score:
            score, category = 0.85, "Jailbreak"
    elif h["UNRESTRICTED"]:
        # رفع قيود بدون لعب دور: يرفع الخطورة، ومع فعل إلغاء أو أمر تنفيذ يصير هجوم
        signals.append(f"unrestricted request: '{h['UNRESTRICTED'][0][1]}'")
        s = 0.45 + (0.25 if h["OVERRIDE"] or h["ROLEPLAY"] else 0)
        if s > score:
            score, category = s, "Jailbreak"

    # 3) تسريب تعليمات النظام: فعل تسريب + إشارة لتعليمات النموذج نفسه
    pair = _near(h["LEAK_VERB"], h["SELF_INSTR"], 10)
    if not pair:
        pair = _near(h["SELF_INSTR"], h["LEAK_VERB"], 6)
    if pair:
        signals.append(f"leak→self-instructions: '{pair[0]}' … '{pair[1]}'")
        if 0.85 > score:
            score, category = 0.85, "Prompt Leaking"

    # إشارات ضعيفة (ما تحظر لحالها)
    if score == 0 and h["OVERRIDE"] and h["SCOPE"] and h["ROLEPLAY"]:
        score, category = 0.5, "Suspicious"
        signals.append("weak: override + scope + roleplay")

    exec_enc = bool(h["EXEC_ENCODED"])
    return min(score, 1.0), category, signals, exec_enc
