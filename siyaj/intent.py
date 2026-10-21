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
        r"nullif\w*", r"void\w*", r"cancel\w*", r"revok\w*", r"invalidat\w*", r"suspend\w*",
        r"(?:ت|ي|ن|ا)?تجاهل\w*", r"انس(?:ى|ي|وا)?", r"تناس\w*", r"تخط(?:ى|ي|ا)\w*",
        r"(?:ت|ي|ن)?تجاوز\w*", r"(?:ت|ي)?همل\w*", r"اهمل\w*", r"الغ(?:ي|ى)?\b", r"احذف", r"اترك",
        r"(?:لا|ما|بلاش) (?:تلتزم|تتبع|تطبق|تنفذ|تمشي علي|تهتم)\w*",
        r"(?:اعتبر|افترض) (?:ان|انه)? ?(?:ما ?في(?:ه)?|لا يوجد|مافي|ما عندك|ليس هناك|ما كان في(?:ه)?)",
    ],
    # الهدف: تعليمات/قواعد النموذج
    "TARGET": [
        r"instruct\w*", r"direction\w*", r"rule\w*", r"guideline\w*", r"prompt\w*",
        r"polic(?:y|ies)", r"restriction\w*", r"constraint\w*", r"filter\w*",
        r"guardrail\w*", r"programming", r"directive\w*", r"guidance", r"configuration",
        r"safeguard\w*", r"protocol\w*", r"limitations?",
        r"(?:everything|all|anything) (?:you (?:were|have been|ve been|are) )?(?:told|taught|given|said)",
        r"safety (?:settings|measures)", r"content policy",
        AR_PFX + r"تعليمات\w*", AR_PFX + r"(?:ا)?وامر\w*", AR_PFX + r"قواعد\w*",
        AR_PFX + r"قيود\w*", AR_PFX + r"ارشادات\w*", AR_PFX + r"ضوابط\w*",
        AR_PFX + r"سياس(?:ه|ات)\w*", AR_PFX + r"فلاتر\w*", AR_PFX + r"توجيهات\w*",
        AR_PFX + r"برومبت\w*", AR_PFX + r"برمجه\w*", AR_PFX + r"حدود\w*",
        r"كل (?:شي|شيء|اللي|ما)\s?(?:\w+ )?(?:قيل|قال\w*|انقال|عطو\w*|اعطو\w*)",
    ],
    # تحديد زمني/نطاق يقوّي الهجوم
    "SCOPE": [
        r"previous\w*", r"prior", r"above", r"before", r"earlier", r"preceding",
        r"initial", r"original", r"all", r"every\w*", r"your", r"system",
        r"from now on", r"new task", r"new instructions", r"instead",
        r"preced\w*", r"preceden\w*", r"anterior\w*", r"vorherig\w*", r"toutes?", r"todas?", r"alle",
        AR_PFX + r"سابق\w*", r"قبل", r"كل", r"جميع", AR_PFX + r"اولي\w*",
        r"\w*ك\b", r"من الحين", r"من الان", r"مهمه جديده",
    ],
    # لعب أدوار
    "ROLEPLAY": [
        r"pretend\w*", r"act(?:ing)? as", r"you are now", r"you re now", r"from now on you",
        r"role ?play\w*", r"play (?:a|the) (?:game|role)", r"imagine (?:you|that you)",
        r"simulat\w*", r"behave (?:as|like)", r"become", r"persona",
        r"تقمص\w*", r"مثل دور", r"(?:العب|خذ) دور", r"تخيل (?:انك|نفسك)",
        r"(?:ن|ت)?(?:لعب|نسوي) لعبه", r"انت (?:ذكاء|بوت|مساعد|روبوت|نموذج)",
        r"تظاهر\w*", r"صرت", r"انت الحين", r"انت الان", r"افترض انك",
    ],
    # رفع القيود
    "UNRESTRICTED": [
        r"no (?:restrictions?|rules?|limits?|limitations?|filters?|ethics|morals?|boundaries|guidelines|censorship)",
        r"without (?:any )?(?:restrictions?|rules?|limits?|filters?|ethics|censorship|guidelines)",
        r"unfilter\w*", r"uncensor\w*", r"unrestrict\w*", r"unlimited", r"unbound\w*",
        r"evil (?:ai|assistant|bot)", r"anything goes", r"no holds barred",
        r"(?:بدون|بلا|من غير|مافي|ما فيه) (?:اي )?(?:قيود|قواعد|فلاتر|حدود|اخلاق|ضوابط|رقابه)",
        r"(?:ما|لا|ليس|مو) ?(?:عنده|لديه|عندك|لديك|له|لك|فيه) (?:اي )?(?:قيود|قواعد|فلاتر|حدود|اخلاق|ضوابط|رقابه)",
        r"(?:has|have|with) no (?:\w+ )?(?:restrictions?|rules?|limits?|filters?|ethics)",
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
    # إبطال صلاحية التعليمات بالادّعاء ("rules are outdated", "no longer apply")
    "INVALIDATE": [
        r"no longer (?:apply|valid|matter|in effect|relevant)", r"(?:are|is|were) (?:now )?(?:outdated|obsolete|void|invalid|cancelled|deprecated)",
        r"(?:don t|do not) apply anymore", r"ما عاد (?:لها|له) (?:داعي|قيمه)", r"(?:ملغيه|منتهيه|ما تنطبق)",
    ],
    # إعادة تأطير مهمة النموذج ("that was a test, your real job is ...")
    "REFRAME": [
        r"your (?:real|true|actual|new|only) (?:job|task|purpose|role|goal|mission|instructions?)",
        r"(?:was|were) (?:only|just|merely) (?:a )?(?:test|joke|example|decoy)",
        r"مهمتك (?:الحقيقيه|الفعليه|الجديده)", r"(?:كان|كانت) (?:مجرد )?(?:اختبار|تجربه)",
    ],
    # كلام عن الموضوع (مقال/شرح/سؤال) مو أمر للنموذج
    "DISCUSS": [
        r"what is", r"what are", r"explain\w*", r"article", r"essay", r"research", r"how (?:do|does|can) (?:companies|developers|we|i) (?:defend|protect|detect|prevent)",
        r"defen[cs]e", r"protect\w*", r"detect\w*", r"risk\w*", r"danger\w*",
        r"(?:اكتب|عطني|سو) (?:مقال|بحث|تقرير)", r"اشرح\w*", r"ما هو", r"ما هي", r"خطور\w*", r"حمايه من", r"كيف (?:نحمي|نكتشف|نمنع)",
    ],
    # كلام منقول عن طرف ثالث ("my teacher said to disregard ...")
    "REPORTED": [
        r"(?:said|told me|asked me|wants me|instructed me) to", r"(?:he|she|they|teacher|manager|boss) (?:said|told)",
        r"(?:قال|قالت|طلب|طلبت) (?:لي|مني|منا)", r"(?:المعلم|الاستاذ|المدير|المديره|المعلمه) (?:قال|قالت|طلب)\w*",
    ],
    # يطلب تنفيذ محتوى مشفّر
    "EXEC_ENCODED": [
        r"(?:decode|decrypt|translate|read|convert)\w* (?:this|the following|it)?.{0,20}(?:follow|execute|do|obey|run|then)",
        r"follow (?:it|this|the decoded)", r"backwards", r"reverse\w*",
        r"(?:فك|ترجم) .{0,20}(?:نفذ|طبق|اتبع)", r"بالمقلوب",
    ],
}

COMPILED = {k: [re.compile(p) for p in v] for k, v in CONCEPTS.items()}


def _skeleton(pattern: str) -> str:
    """في نص الـ leet الرقم 1 ممكن يكون i أو l، فنخلي الحرفين متكافئين في الأنماط."""
    return re.sub(r"(?<!\\)[il]", "[il]", pattern)


COMPILED_SKEL = {k: [re.compile(_skeleton(p)) for p in v] for k, v in CONCEPTS.items()}


def _hits(text: str, concept: str, loose: bool = False, skel: bool = False):
    """يرجّع مواقع الكلمات (word index) لكل تطابق للمفهوم.
    loose=True للنص الملصوق بدون مسافات (i.g.n.o.r.e a.l.l -> ignoreall):
    نتجاهل حدود الكلمات ونقدّر موقع الكلمة من موقع الحرف."""
    idx = []
    for rx in (COMPILED_SKEL if skel else COMPILED)[concept]:
        for m in rx.finditer(text):
            if not loose and m.start() > 0 and text[m.start() - 1].isalnum():
                continue
            word_pos = m.start() // 6 if loose else text.count(" ", 0, m.start())
            idx.append((word_pos, m.group(0)))
    return idx


def _near(a, b, window, both_ways=False):
    for ia, ta in a:
        for ib, tb in b:
            d = ib - ia
            if 0 <= d <= window or (both_ways and -window <= d < 0):
                return (ta, tb)
    return None


def analyze_intent(text: str, loose: bool = False, skel: bool = False):
    """
    يحلل نص موحّد ويرجّع (درجة الخطورة 0..1، التصنيف، الأدلة).
    """
    h = {c: _hits(text, c, loose, skel) for c in COMPILED}
    signals = []
    score = 0.0
    category = None

    # 1) حقن أوامر: فعل إلغاء + هدف (التعليمات) خلال 8 كلمات
    pair = _near(h["OVERRIDE"], h["TARGET"], 8, both_ways=True)
    if not pair:
        pair = _near(h["INVALIDATE"], h["TARGET"], 8, both_ways=True)
    if pair:
        s = 0.5          # لوحده مشبوه فقط ("how to ignore a rule in eslint")
        if h["SCOPE"]:
            s = 0.9      # مع نطاق (السابقة/كل/your/system) = حقن واضح
        signals.append(f"فعل إلغاء مع تعليمات النموذج: '{pair[0]}' … '{pair[1]}'")
        # كلام منقول عن طرف ثالث ("my teacher said to disregard the homework instructions")
        if h["REPORTED"] and _near(h["REPORTED"], h["OVERRIDE"] or h["INVALIDATE"], 3):
            s = min(s, 0.45)
            signals.append(f"خُفّضت الخطورة: كلام منقول عن طرف ثالث '{h['REPORTED'][0][1]}'")
        if s > score:
            score, category = s, "Prompt Injection"

    # 1b) إعادة تأطير المهمة
    if h["REFRAME"]:
        signals.append(f"محاولة إعادة تعريف مهمة النموذج: '{h['REFRAME'][0][1]}'")
        if 0.7 > score:
            score, category = 0.7, "Prompt Injection"

    # 2) كسر حماية: لعب دور + رفع قيود، أو كلمة كسر حماية معروفة
    if h["JAILBREAK_TOKEN"]:
        js = 0.8
        if h["DISCUSS"]:   # "اكتب مقال عن خطورة كسر الحماية" = موضوع، مو أمر
            js = 0.4
            signals.append(f"خُفّضت الخطورة: سياق نقاش أو شرح '{h['DISCUSS'][0][1]}'")
        signals.append(f"كلمة كسر حماية معروفة: '{h['JAILBREAK_TOKEN'][0][1]}'")
        if js > score:
            score, category = js, "Jailbreak"
    pair = _near(h["ROLEPLAY"], h["UNRESTRICTED"], 14)
    if pair:
        signals.append(f"لعب دور مع رفع القيود: '{pair[0]}' … '{pair[1]}'")
        if 0.85 > score:
            score, category = 0.85, "Jailbreak"
    elif h["UNRESTRICTED"]:
        # رفع قيود بدون لعب دور: يرفع الخطورة، ومع فعل إلغاء أو أمر تنفيذ يصير هجوم
        signals.append(f"طلب العمل بدون قيود: '{h['UNRESTRICTED'][0][1]}'")
        s = 0.45 + (0.25 if h["OVERRIDE"] or h["ROLEPLAY"] else 0)
        if s > score:
            score, category = s, "Jailbreak"

    # 3) تسريب تعليمات النظام: فعل تسريب + إشارة لتعليمات النموذج نفسه
    pair = _near(h["LEAK_VERB"], h["SELF_INSTR"], 10)
    if not pair:
        pair = _near(h["SELF_INSTR"], h["LEAK_VERB"], 6)
    if pair:
        signals.append(f"طلب كشف تعليمات النظام: '{pair[0]}' … '{pair[1]}'")
        if 0.85 > score:
            score, category = 0.85, "Prompt Leaking"

    # إشارات ضعيفة (ما تحظر لحالها)
    if score == 0 and h["OVERRIDE"] and h["SCOPE"] and h["ROLEPLAY"]:
        score, category = 0.5, "Suspicious"
        signals.append("إشارة ضعيفة: إلغاء + نطاق + لعب دور")

    exec_enc = bool(h["EXEC_ENCODED"])
    return min(score, 1.0), category, signals, exec_enc
