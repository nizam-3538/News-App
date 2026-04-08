from groq import AsyncGroq
from config import GROQ_API_KEY

# Initialize the AsyncGroq client once at the global level
client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

_GROUNDED_SYSTEM_PROMPT = """\
You are a "Domain Expert & Historian" AI for a premium news application.
Your goal is to provide deep historical context, explain what events likely led up to this news, and discuss the broader impact on the global or local stage.

Instructions:
1. Use the "ARTICLE TEXT" provided below as your primary source of current events.
2. Even if you cannot access external links, use the topic of the article to provide your expert historical perspective.
3. If the answer is not in the article and not in your historical knowledge, say "I don't have enough context to discuss that."
4. Maintain a professional, intellectual, yet accessible tone.
5. Keep answers insightful but concise (under 300 words).
6. CRITICAL: You MUST respond entirely in the [LANGUAGE] specified below.
"""

_FALLBACK_RESPONSES = [
    "I'm having trouble processing that right now. Could you try rephrasing your question?",
    "I'm unable to provide a detailed response at the moment. Please try again shortly.",
]


from typing import Optional, List
import json

async def grounded_chat(
    article_text: str, 
    question: str, 
    language: str = "English",
    history: Optional[List[dict]] = None
) -> dict:
    """
    Send a grounded Q&A request to the Groq API.
    If 'history' is provided and 'question' contains translation keywords,
    it returns the history with an error message on failure.
    """
    if not client:
        return {
            "answer": "AI chat is not configured. Please set GROQ_API_KEY.",
            "model": "none",
            "grounded": False,
        }

    # Detect if this is a translation request
    is_translation = "Translate" in question and "chat history" in question.lower()

    # 🛡️ DATA PAYLOAD PATTERN: Isolate translation from conversation
    if is_translation:
        # Serialize history as a raw JSON string payload
        history_payload = json.dumps(history or [])

        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a strict data processing engine. Your ONLY job is to translate "
                    f"the 'content' fields of the provided JSON array into {language}. "
                    "DO NOT answer the questions in the chat. DO NOT add conversational filler. "
                    "DO NOT summarize, combine, or skip any messages. "
                    "Translate each message exactly 1-to-1, preserving the order and count. "
                    "Return ONLY a valid JSON object with exactly one key: 'translated_history'. "
                    "Its value must be an array of objects, each with exactly two keys: 'role' and 'content'. "
                    "DO NOT use keys like 'user', 'assistant', or 'message'."
                )
            },
            {
                "role": "user",
                "content": f"TRANSLATE THIS JSON PAYLOAD:\n{history_payload}"
            }
        ]
    else:
        # Standard Q&A: use the grounded system prompt + conversational history
        user_prompt = (
            f"[LANGUAGE]: {language}\n"
            f"--- ARTICLE TEXT ---\n{article_text}\n--- END ARTICLE ---\n\n"
            f"User question: {question}"
        )

        messages = [
            {"role": "system", "content": _GROUNDED_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        # Add history if it exists, and normalize roles for Groq
        if history:
            for message in history:
                incoming_role = message.get("role")

                # Normalize the role for Groq API
                if incoming_role in ["ai", "model", "assistant"]:
                    valid_role = "assistant"
                elif incoming_role == "user":
                    valid_role = "user"
                else:
                    continue  # Skip system prompts or other roles

                # Create a new message dict to avoid modifying the original history object
                messages.append({"role": valid_role, "content": message.get("content", "")})


    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.1 if is_translation else 0.2,
            max_tokens=2000 if is_translation else 1000,
            top_p=0.8,
            # 🛡️ REVERT TO JSON_OBJECT: llama-3.3-70b-versatile does not support json_schema
            response_format={"type": "json_object"} if is_translation else None,
        )

        answer = response.choices[0].message.content.strip()
        print(f"🚨 RAW AI OUTPUT:\n{answer}")

        # 🛡️ BACKEND EXTRACTION: Extract array from root object so frontend still receives []
        if is_translation:
            try:
                # Strip markdown backticks if AI included them (e.g., ```json ... ```)
                cleaned_answer = answer.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(cleaned_answer)
                
                # 🛡️ DATA NORMALIZATION: Force AI output into the correct schema
                # (Prevents blank chat bubbles from hallucinated keys)
                raw_array = parsed.get("translated_history", [])
                normalized_history = []
                
                for item in raw_array:
                    role = "assistant"
                    content = ""
                    
                    # 1. Direct hit (Followed instructions)
                    if "role" in item and "content" in item:
                        role = item["role"]
                        content = item["content"]
                    # 2. Used "message" key
                    elif "message" in item:
                        # Extract role or fallback to user
                        role_raw = item.get("user", item.get("role", "user")).lower()
                        role = "user" if any(x in role_raw for x in ["user", "उपयोगकर्ता"]) else "assistant"
                        content = item["message"]
                    # 3. Used "user" key directly as content
                    elif "user" in item:
                        role = "user"
                        content = item["user"]
                    # 4. Used "assistant" key directly as content
                    elif "assistant" in item:
                        role = "assistant"
                        content = item["assistant"]
                    
                    normalized_history.append({"role": role, "content": content})

                answer = json.dumps(normalized_history)
            except json.JSONDecodeError as e:
                print(f"🚨 JSON Parse Error in translation: {e}")
                # Fallback to pure string if parsing fails
                pass

        return {"ok": True, "answer": answer, "model": "llama-3.3-70b-versatile", "grounded": True}

    except Exception as exc:
        print(f"🚨 AI Engine Error: {exc}")
        return {"ok": False, "answer": "The AI engine failed to process your request."}


async def generate_summary(history: List[dict], language: str = "English") -> dict:
    """
    Summarize a chat history into a concise paragraph.
    Uses the same Data Payload Pattern as translation.
    """
    if not client:
        return {
            "ok": False,
            "summary": "AI chat is not configured. Please set GROQ_API_KEY.",
        }

    history_payload = json.dumps(history or [])

    messages = [
        {
            "role": "system",
            "content": (
                f"You are an AI summarizer. Read the provided JSON chat payload. "
                f"Summarize the key takeaways of the conversation into a single, concise paragraph. "
                f"CRITICAL: The summary MUST be written in {language}. "
                "Return ONLY the raw summary text. No markdown, no json, no conversational filler."
            )
        },
        {
            "role": "user",
            "content": f"SUMMARIZE THIS CHAT PAYLOAD:\n{history_payload}"
        }
    ]

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=500,
            top_p=0.8,
        )

        summary = response.choices[0].message.content.strip()
        return {"ok": True, "summary": summary}

    except Exception as exc:
        print(f"🚨 SUMMARY BACKEND ERROR: {repr(exc)}")
        return {"ok": False, "summary": "Failed to generate summary."}


async def vault_rag_chat(context_text: str, question: str) -> dict:
    """
    Query the vault context using Groq (llama3-70b-8192) acting as an expert research assistant.
    """
    if not client:
        return {"ok": False, "answer": "AI chat is not configured. Please set GROQ_API_KEY."}

    system_prompt = (
        "You are PulseNews AI, an expert research assistant. "
        "Answer the user's question using ONLY the provided article summaries from their personal vault. "
        "If the answer is not in the summaries, say 'I cannot find the answer in your saved articles.' "
        "Always cite the article title you got the information from."
    )

    user_prompt = f"--- SAVED ARTICLES ---\n{context_text}\n\nUser Question: {question}"

    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
        )
        return {"ok": True, "answer": response.choices[0].message.content.strip()}
    except Exception as exc:
        print(f"🚨 Vault RAG Error: {exc}")
        return {"ok": False, "answer": "Failed to query vault."}
