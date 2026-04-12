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

## Tech Stack
- Python
- FastAPI
- Pydantic
- Regex-based threat detection

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