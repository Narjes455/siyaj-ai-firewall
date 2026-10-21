# Siyaj - AI-Powered Firewall for LLM Security

## Project Overview
Siyaj is a lightweight AI security firewall designed to inspect user prompts before they are processed by an AI system.  
It helps detect and block:

- Sensitive data leakage (PII)
- Prompt Injection attacks

## Features
- Detects email addresses
- Detects Saudi phone numbers
- Detects prompt injection attempts
- Logs blocked threats into `logs.txt`
- Provides threat statistics through `/stats`
- Displays recorded logs through `/logs`

## How Siyaj v2 Works (multi-layer, not keyword matching)
1. **Normalization layer** – undoes obfuscation: letter spacing, leetspeak, Cyrillic homoglyphs, zero-width chars, Arabic tatweel/tashkeel, fullwidth/math fonts, Arabic-Indic digits.
2. **Multi-view analysis** – the prompt is also checked reversed, leet-decoded, and Base64/Hex-decoded. Attacks hidden only in a decoded view get a higher risk score.
3. **Concept-based intent analysis (Arabic + English)** – detects *combinations* of concepts (override verb + model instructions + scope, role-play + no restrictions, leak verb + self-instructions) within a word window, with downgrades for discussion context and reported speech to avoid false positives.
4. **Validated PII detection** – Saudi phones in all formats, National ID / Iqama (Luhn), Saudi IBAN (ISO 13616 mod-97), payment cards (Luhn), plain and obfuscated emails. Logs store the redacted prompt.

Every decision returns a `risk_score` (0–100) and human-readable `evidence`.

## Benchmark (see BENCHMARK.md)
| Test set (first run, never tuned on) | Original | Siyaj v2 | False positives |
|---|---|---|---|
| Held-out (73 cases) | 2.1% | 79.2% | 2/25 |
| Blind round 2 (43 cases) | 3.8% | 38.5% | 0/17 |

Known gaps: Arabic dialect phrasings, uncovered languages, hypothetical framing, indirect leak requests.

## Tech Stack
- Python
- FastAPI
- Pydantic
- Pure-Python detection engine (`siyaj/`), no external dependencies

## API Endpoints

### `GET /`
Checks whether the API is running.

### `POST /analyze`
Analyzes user prompts and blocks suspicious or sensitive input.

Example request:
```json
{
  "prompt": "my email is test@gmail.com"
}

GET /stats

Returns the number of detected threats.

GET /logs

Returns logged blocked attempts from logs.txt.

Threat Types
	•	PII: Sensitive data such as email or phone number
	•	Prompt Injection: Attempts to manipulate AI instructions

Example Output

{
  "status": "blocked",
  "threat_type": "PII",
  "reason": "Email detected"
}

Future Improvements
	•	Add support for more PII types
	•	Add risk scoring for each prompt
	•	Build a web dashboard for visualization
	•	Integrate with real LLM APIs

Author

Developed by Narjes Hassan Al-Amri