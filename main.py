from fastapi import FastAPI
from pydantic import BaseModel
import datetime

from siyaj import analyze_prompt, __version__

app = FastAPI(title="Siyaj AI Firewall", version=__version__)


class PromptRequest(BaseModel):
    prompt: str


def log_threat(threat_type: str, reason: str, risk: int, prompt: str):
    with open("logs.txt", "a", encoding="utf-8") as f:
        f.write(
            f"{datetime.datetime.now()} | {threat_type} | {reason} | risk={risk} | {prompt}\n"
        )


def get_log_stats():
    stats = {
        "total_threats": 0,
        "pii_threats": 0,
        "prompt_injection_threats": 0,
        "jailbreak_threats": 0,
        "prompt_leaking_threats": 0,
    }
    try:
        with open("logs.txt", "r", encoding="utf-8") as f:
            for line in f:
                stats["total_threats"] += 1
                if "| PII |" in line:
                    stats["pii_threats"] += 1
                elif "| Prompt Injection |" in line:
                    stats["prompt_injection_threats"] += 1
                elif "| Jailbreak |" in line:
                    stats["jailbreak_threats"] += 1
                elif "| Prompt Leaking |" in line:
                    stats["prompt_leaking_threats"] += 1
    except FileNotFoundError:
        pass
    return stats


@app.get("/")
def home():
    return {"message": "Siyaj Firewall is running 🚀", "version": __version__}


@app.get("/stats")
def stats():
    return get_log_stats()


@app.get("/logs")
def get_logs():
    try:
        with open("logs.txt", "r", encoding="utf-8") as f:
            return {"logs": f.readlines()}
    except FileNotFoundError:
        return {"logs": []}


@app.post("/analyze")
def analyze(request: PromptRequest):
    result = analyze_prompt(request.prompt)
    if result["status"] == "blocked":
        # نسجّل النسخة المحجوبة من البيانات الشخصية، مو الأصلية
        logged = result.get("redacted_prompt", request.prompt)
        log_threat(result["threat_type"], result["reason"], result["risk_score"], logged)
    return result
