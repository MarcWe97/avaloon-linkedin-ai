#!/usr/bin/env python3
"""
Valoon LinkedIn AI Reply Automation
- Receives Lemlist webhook for LinkedIn replies
- Calls Claude API with web_search and web_fetch tools
- Logs responses for review (2-week review mode)
- After review: can switch to auto-send via Lemlist API
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import anthropic

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LEMLIST_API_KEY = os.getenv("LEMLIST_API_KEY")
LEMLIST_SENDER_USER_ID = os.getenv("LEMLIST_SENDER_USER_ID")
REVIEW_MODE = os.getenv("REVIEW_MODE", "true").lower() == "true"  # Switch to false for auto-send
CALENDLY_LINK = "https://calendly.com/valoon-team/kennenlerntermin-45min-ll"
VALOON_WEBSITE = "https://valoon.chat"

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not set")
if not LEMLIST_API_KEY:
    raise ValueError("LEMLIST_API_KEY not set")

app = FastAPI()
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Store responses for logging (in-memory for 2-week review)
responses_log = []


def detect_language(text: str) -> str:
    """Simple language detection based on common words"""
    text_lower = text.lower()
    de_words = ["ich", "du", "das", "die", "und", "aber", "wenn", "können"]
    en_words = ["i", "you", "the", "and", "but", "if", "can", "your"]
    
    de_count = sum(1 for word in de_words if word in text_lower)
    en_count = sum(1 for word in en_words if word in text_lower)
    
    return "de" if de_count >= en_count else "en"


def build_system_prompt(language: str) -> str:
    """Build the system prompt for Claude"""
    if language == "de":
        return f"""Du bist ein freundlicher und professioneller Sales-Assistent für Valoon, eine innovative Plattform.

Deine Aufgabe:
1. Lese die Antwort des Leads sorgfältig
2. Verstehe was der Lead braucht oder fragt
3. Suche bei Bedarf auf der Valoon-Website nach relevanten Informationen
4. Schreibe eine kurze, natürliche LinkedIn-Antwort auf Deutsch
5. Wenn relevant und passend: Schlage den Kennenlerntermin vor: {CALENDLY_LINK}

Anforderungen:
- Antworte IMMER auf Deutsch (da der Lead auf Deutsch geantwortet hat)
- Max. 3-4 Sätze, natürlicher Ton
- Keine generischen Floskeln ("herzlichen Dank für deine Nachricht")
- Personalisiert auf das was der Lead gefragt/gesagt hat
- Der Calendly-Link sollte organisch in die Antwort passen, nicht erzwungen

Du hast Zugriff auf die Web-Search und Web-Fetch Tools. 
Nutze sie um auf valoon.chat nach aktuellen Informationen zu suchen.
Beispiele: Features, Preise, Case Studies, Integrationen, Blog-Posts."""
    else:
        return f"""You are a friendly and professional sales assistant for Valoon, an innovative platform.

Your task:
1. Read the lead's reply carefully
2. Understand what the lead needs or is asking
3. Search the Valoon website for relevant information if needed
4. Write a short, natural LinkedIn reply in English
5. If relevant and fitting: Suggest the introductory call: {CALENDLY_LINK}

Requirements:
- Always reply in English (since the lead replied in English)
- Max. 3-4 sentences, natural tone
- No generic phrases ("thank you for reaching out")
- Personalized to what the lead asked/said
- The Calendly link should fit naturally, not forced

You have access to Web-Search and Web-Fetch tools.
Use them to search valoon.chat for current information.
Examples: Features, Pricing, Case Studies, Integrations, Blog Posts."""


def generate_ai_response(
    lead_name: str,
    company_name: str,
    job_title: str,
    original_message: str,
    reply_text: str,
    language: str
) -> str:
    """Call Claude API with web search/fetch tools"""
    
    logger.info(f"Generating response for {lead_name} from {company_name}")
    logger.info(f"Language detected: {language}")
    logger.info(f"Reply text: {reply_text[:100]}...")
    
    system_prompt = build_system_prompt(language)
    
    user_message = f"""Lead-Infos:
- Name: {lead_name}
- Unternehmen: {company_name}
- Position: {job_title}

Unsere ursprüngliche Nachricht:
{original_message}

Antwort des Leads:
{reply_text}

Generiere jetzt eine passende LinkedIn-Antwort."""
    
    # Call Claude with tools
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system_prompt,
        tools=[
            {
                "name": "web_search",
                "description": "Search the web for information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "web_fetch",
                "description": "Fetch content from a specific URL",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Full URL to fetch"
                        }
                    },
                    "required": ["url"]
                }
            }
        ],
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    # Process response blocks
    final_text = ""
    tool_use_blocks = []
    
    for block in response.content:
        if block.type == "text":
            final_text = block.text
        elif block.type == "tool_use":
            tool_use_blocks.append(block)
    
    # If Claude used tools, we need to do a follow-up (agentic loop)
    if tool_use_blocks:
        logger.info(f"Claude requested {len(tool_use_blocks)} tool calls")
        
        # Build tool results
        tool_results = []
        for tool_block in tool_use_blocks:
            tool_name = tool_block.name
            tool_input = tool_block.input
            
            logger.info(f"Tool: {tool_name}, Input: {tool_input}")
            
            try:
                if tool_name == "web_search":
                    # For now, just log that search was requested
                    # In production: use actual web search API
                    result = f"Search results for: {tool_input.get('query', '')} (simulated)"
                elif tool_name == "web_fetch":
                    # For now, just log that fetch was requested
                    result = f"Fetched content from: {tool_input.get('url', '')} (simulated)"
                else:
                    result = "Tool not recognized"
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result
                })
                logger.info(f"Tool result: {result[:100]}")
            except Exception as e:
                logger.error(f"Tool execution error: {str(e)}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": f"Error: {str(e)}"
                })
        
        # Follow-up message with tool results
        messages_with_tools = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": tool_results}
        ]
        
        # Get final response
        final_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=messages_with_tools
        )
        
        for block in final_response.content:
            if block.type == "text":
                final_text = block.text
    
    return final_text.strip()


async def send_to_lemlist_api(
    lead_id: str,
    contact_id: str,
    message_text: str
) -> bool:
    """Send reply via Lemlist API (only in auto-send mode)"""
    if REVIEW_MODE:
        logger.info("REVIEW MODE: Not sending to Lemlist API")
        return False
    
    if not LEMLIST_SENDER_USER_ID:
        logger.error("LEMLIST_SENDER_USER_ID not set")
        return False
    
    try:
        import httpx
        async with httpx.AsyncClient() as client_http:
            response = await client_http.post(
                "https://api.lemlist.com/api/inbox/linkedin",
                headers={
                    "Authorization": f"Basic {LEMLIST_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "sendUserId": LEMLIST_SENDER_USER_ID,
                    "leadId": lead_id,
                    "contactId": contact_id,
                    "message": message_text
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Lemlist API success for lead {lead_id}")
                return True
            else:
                logger.error(f"Lemlist API error: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logger.error(f"Lemlist API exception: {str(e)}")
        return False


@app.post("/webhook")
async def lemlist_webhook(request: Request):
    """Receive Lemlist webhook for LinkedIn replies"""
    try:
        payload = await request.json()
        logger.info(f"Webhook received: {json.dumps(payload, indent=2)}")
        
        # Extract data from Lemlist webhook
        lead_id = payload.get("leadId")
        contact_id = payload.get("contactId")
        lead_name = payload.get("firstName", "Lead")
        company_name = payload.get("companyName", "Unknown")
        job_title = payload.get("jobTitle", "")
        reply_text = payload.get("messageBody", "")
        original_message = payload.get("originalMessage", "")
        
        if not reply_text:
            logger.warning("No reply text in webhook")
            return JSONResponse({"status": "error", "message": "No reply text"}, status_code=400)
        
        # Detect language from reply
        language = detect_language(reply_text)
        
        # Generate AI response
        ai_response = generate_ai_response(
            lead_name=lead_name,
            company_name=company_name,
            job_title=job_title,
            original_message=original_message,
            reply_text=reply_text,
            language=language
        )
        
        # Log response for review
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "lead_name": lead_name,
            "company": company_name,
            "position": job_title,
            "lead_reply": reply_text,
            "ai_response": ai_response,
            "language": language,
            "status": "review"
        }
        responses_log.append(log_entry)
        
        logger.info(f"Response generated: {ai_response[:100]}...")
        logger.info(f"REVIEW MODE: Response logged, not sent to Lemlist")
        
        # In auto-send mode: send via Lemlist API
        if not REVIEW_MODE and lead_id and contact_id:
            success = await send_to_lemlist_api(lead_id, contact_id, ai_response)
            log_entry["status"] = "sent" if success else "failed"
        
        return JSONResponse({
            "status": "success",
            "mode": "review" if REVIEW_MODE else "auto-send",
            "response": ai_response,
            "language": language
        })
    
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


@app.get("/logs")
async def get_logs():
    """Return all logged responses for review"""
    return JSONResponse({
        "mode": "review" if REVIEW_MODE else "auto-send",
        "total_responses": len(responses_log),
        "responses": responses_log[-50:]  # Last 50
    })


@app.get("/health")
async def health():
    """Health check for Railway"""
    return JSONResponse({
        "status": "ok",
        "mode": "review" if REVIEW_MODE else "auto-send",
        "logged_responses": len(responses_log)
    })


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
