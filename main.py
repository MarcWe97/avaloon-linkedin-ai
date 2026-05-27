#!/usr/bin/env python3
import os, json, logging
from datetime import datetime
import google.generativeai as genai
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LEMLIST_API_KEY = os.getenv("LEMLIST_API_KEY")
LEMLIST_SENDER_USER_ID = os.getenv("LEMLIST_SENDER_USER_ID")
REVIEW_MODE = os.getenv("REVIEW_MODE", "true").lower() == "true"
CALENDLY = "https://calendly.com/valoon-team/kennenlerntermin-45min-ll"

if not GEMINI_API_KEY: raise ValueError("GEMINI_API_KEY not set")
if not LEMLIST_API_KEY: raise ValueError("LEMLIST_API_KEY not set")

genai.configure(api_key=GEMINI_API_KEY)
app = FastAPI()
responses_log = []

def detect_language(text):
    de_words = ["ich", "du", "das", "die", "und"]
    en_words = ["i", "you", "the", "and"]
    return "de" if sum(1 for w in de_words if w in text.lower()) >= sum(1 for w in en_words if w in text.lower()) else "en"

def generate_ai_response(lead_name, company, job_title, original, reply_text, language):
    prompt = f"Generate a LinkedIn reply to: {reply_text}\n\nLead: {lead_name} at {company}"
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "Could not generate response"
    except Exception as e:
        logger.error(f"Gemini error: {str(e)}")
        return f"Error: {str(e)}"

@app.post("/webhook")
async def webhook(request: Request):
    try:
        payload = await request.json()
        reply_text = payload.get("messageBody", "")
        if not reply_text:
            return JSONResponse({"status": "error"}, status_code=400)
        language = detect_language(reply_text)
        ai_response = generate_ai_response(
            payload.get("firstName", "Lead"),
            payload.get("companyName", ""),
            payload.get("jobTitle", ""),
            payload.get("originalMessage", ""),
            reply_text,
            language
        )
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "lead": payload.get("firstName"),
            "reply": reply_text,
            "response": ai_response,
            "language": language
        }
        responses_log.append(log_entry)
        return JSONResponse({"status": "success", "mode": "review" if REVIEW_MODE else "auto", "response": ai_response})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/logs")
async def logs():
    return JSONResponse({"total": len(responses_log), "responses": responses_log[-50:]})

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "logged": len(responses_log)})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
