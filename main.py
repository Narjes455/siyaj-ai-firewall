from fastapi import FastAPI
from pydantic import BaseModel
import re
import datetime

app = FastAPI()


class PromptRequest(BaseModel):
    prompt: str


def log_threat(threat_type: str, reason: str, prompt: str):
    with open("logs.txt", "a", encoding="utf-8") as f:
        f.write(
            f"{datetime.datetime.now()} | {threat_type} | {reason} | {prompt}\n"
        )


def get_log_stats():
    stats = {
        "total_threats": 0,
        "pii_threats": 0,
        "prompt_injection_threats": 0
    }

    try:
        with open("logs.txt", "r", encoding="utf-8") as f:
            for line in f:
                stats["total_threats"] += 1

                if "| PII |" in line:
                    stats["pii_threats"] += 1

                if "| Prompt Injection |" in line:
                    stats["prompt_injection_threats"] += 1
    except FileNotFoundError:
        pass

    return stats


@app.get("/")
def home():
    return {"message": "Siyaj Firewall is running 🚀"}


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
    prompt = request.prompt
    prompt_lower = prompt.lower()

    if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+", prompt):
        log_threat("PII", "Email detected", prompt)
        return {
            "status": "blocked",
            "threat_type": "PII",
            "reason": "Email detected"
        }

    if re.search(r"\b05\d{8}\b", prompt):
        log_threat("PII", "Phone number detected", prompt)
        return {
            "status": "blocked",
            "threat_type": "PII",
            "reason": "Phone number detected"
        }

    if "ignore previous instructions" in prompt_lower:
        log_threat("Prompt Injection", "Prompt Injection detected", prompt)
        return {
            "status": "blocked",
            "threat_type": "Prompt Injection",
            "reason": "Prompt Injection detected"
        }

    return {
        "status": "safe",
        "threat_type": "None",
        "clean_prompt": prompt
    }