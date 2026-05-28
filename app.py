#!/usr/bin/env python3
import os, logging
from datetime import datetime
import google.generativeai as genai
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LEMLIST_API_KEY = os.getenv("LEMLIST_API_KEY")
if not GEMINI_API_KEY: raise ValueError("GEMINI_API_KEY not set")
    if not LEMLIST_API_KEY: raise ValueError("LEMLIST_API_KEY not set")
        genai.configure(api_key=GEMINI_API_KEY)
app = FastAPI()
responses_log = []
def detect_language(text):
     de_words = ["ich","du","das","die","und"]
     en_words = ["i","you","the","and"]
     return "de" if sum(1 for w in de_words if w in text.lower()) >= sum(1 for w in en_words if w in text.lower()) else "en"
    def generate_ai_response(lead_name, company, reply_text, language):
         try:
               model = genai.GenerativeModel("gemini-2.0-flash")
               prompt = f"Generate a short LinkedIn reply to: {reply_text}\n\nLead: {lead_name} at {company}"
               response = model.generate_content(prompt)
               return response.text.strip() if response.text else "Could not generate"
except Exception as e:
  return str(e)
@app.post("/webhook")
async def webhook(request: Request):
     try:
           payload = await request.json()
           reply = payload.get("messageBody", "")
           if not reply: return JSONResponse({"status": "error"}, status_code=400)
                 lang = detect_language(reply)
           resp = generate_ai_response(payload.get("firstName", "Lead"), payload.get("companyName", ""), reply, lang)
           responses_log.append({"timestamp": datetime.now().isoformat(), "lead": payload.get("firstName"), "reply": reply, "response": resp, "language": lang})
           return JSONResponse({"status": "success", "response": resp})
except Exception as e:
  return JSONResponse({"status": "error"}, status_code=500)
@app.get("/logs")
async def logs():
     return JSONResponse({"total": len(responses_log), "responses": responses_log[-50:]})
    @app.get("/health")
async def health():
     return JSONResponse({"status": "ok"})
    if __name__ == "__main__":
         import uvicorn
         port = int(os.getenv("PORT", 8000))
         uvicorn.run(app, host="0.0.0.0", port=port)
