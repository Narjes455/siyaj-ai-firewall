from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Siyaj Firewall is running 🚀"}

@app.post("/analyze")
def analyze(prompt: str):
    if "@" in prompt:
        return {"status": "blocked", "reason": "Email detected"}

    if "ignore previous instructions" in prompt.lower():
        return {"status": "blocked", "reason": "Prompt Injection detected"}

    return {"status": "safe", "clean_prompt": prompt}
