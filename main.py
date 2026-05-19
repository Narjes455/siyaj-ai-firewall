import streamlit as st
import re
import json
from datetime import datetime

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="SIYAJ AI Firewall",
    layout="wide"
)

# ==========================================
# THREAT RULES
# ==========================================

PROMPT_INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"reveal system prompt",
    r"bypass security",
    r"pretend you are not an ai",
    r"developer mode",
    r"disable safety",
]

DATA_EXTRACTION_PATTERNS = [
    r"show confidential information",
    r"export all records",
    r"leak data",
]

EMAIL_REGEX = r'\S+@\S+'
SAUDI_PHONE_REGEX = r'(05\d{8})'

# ==========================================
# DETECTION FUNCTION
# ==========================================

def detect_threats(text):

    threats = []
    score = 0

    lower_text = text.lower()

    # Prompt Injection Detection
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lower_text):
            threats.append("Prompt Injection")
            score += 70
            break

    # Data Extraction Detection
    for pattern in DATA_EXTRACTION_PATTERNS:
        if re.search(pattern, lower_text):
            threats.append("Data Extraction Attempt")
            score += 50
            break

    # Email Detection
    if re.search(EMAIL_REGEX, text):
        threats.append("Email Leakage")
        score += 20

    # Saudi Phone Detection
    if re.search(SAUDI_PHONE_REGEX, text):
        threats.append("Saudi Phone Leakage")
        score += 20

    # Severity Level
    if score >= 80:
        severity = "CRITICAL"

    elif score >= 50:
        severity = "HIGH"

    elif score >= 20:
        severity = "MEDIUM"

    else:
        severity = "LOW"

    return threats, score, severity

# ==========================================
# SANITIZATION FUNCTION
# ==========================================

def sanitize_text(text):

    # Hide emails
    text = re.sub(
        EMAIL_REGEX,
        "[REDACTED_EMAIL]",
        text
    )

    # Hide Saudi phone numbers
    text = re.sub(
        SAUDI_PHONE_REGEX,
        "[REDACTED_PHONE]",
        text
    )

    return text

# ==========================================
# SAVE LOGS
# ==========================================

def save_log(log_data):

    try:
        with open("logs.json", "r") as file:
            logs = json.load(file)

    except:
        logs = []

    logs.append(log_data)

    with open("logs.json", "w") as file:
        json.dump(logs, file, indent=4)

# ==========================================
# USER INTERFACE
# ==========================================

st.title("🛡️ SIYAJ - AI Security Firewall")

st.markdown("""
### Real-Time Protection Against AI Threats
SIYAJ protects AI systems from:
- Prompt Injection
- Sensitive Data Leakage
- Data Extraction Attempts
""")

# ==========================================
# INPUT SECTION
# ==========================================

col1, col2 = st.columns([2,1])

with col1:

    user_input = st.text_area(
        "Enter User Prompt",
        height=250,
        placeholder="Type suspicious prompt here..."
    )

    analyze_button = st.button("Analyze Prompt")

with col2:

    st.info("""
    ### Supported Detection

    ✅ Prompt Injection

    ✅ Email Leakage

    ✅ Saudi Phone Leakage

    ✅ Data Extraction Attempts
    """)

# ==========================================
# ANALYSIS SECTION
# ==========================================

if analyze_button and user_input:

    with st.spinner("Scanning Prompt..."):

        threats, score, severity = detect_threats(user_input)

        sanitized_output = sanitize_text(user_input)

    st.divider()

    # Threat Found
    if threats:

        st.error("🚨 Threat Detected")

        st.markdown(f"## Severity Level: `{severity}`")

        st.markdown(f"## Risk Score: `{score}`")

        st.markdown("## Detected Threats")

        for threat in threats:
            st.write(f"- {threat}")

        st.markdown("## Sanitized Output")

        st.code(sanitized_output)

        status = "BLOCKED"

    # Safe Prompt
    else:

        st.success("✅ Prompt is Safe")

        status = "ALLOWED"

    # ==========================================
    # SAVE LOG
    # ==========================================

    log_data = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "severity": severity,
        "score": score,
        "status": status,
        "threats": threats,
        "prompt": user_input
    }

    save_log(log_data)

# ==========================================
# DASHBOARD SECTION
# ==========================================

st.divider()

st.subheader("📊 Threat Dashboard")

try:

    with open("logs.json", "r") as file:
        logs = json.load(file)

    if logs:

        st.dataframe(
            logs,
            use_container_width=True
        )

        total_requests = len(logs)

        blocked_requests = len([
            x for x in logs
            if x["status"] == "BLOCKED"
        ])

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Requests",
            total_requests
        )

        c2.metric(
            "Blocked Threats",
            blocked_requests
        )

    else:

        st.warning("No logs yet.")

except:

    st.warning("No logs file found.")

# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "SIYAJ - Lightweight AI Security Gateway"
)
