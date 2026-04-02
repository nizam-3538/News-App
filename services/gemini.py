from google import genai
from google.genai import types
from config import GEMINI_API_KEY

_GROUNDED_SYSTEM_PROMPT = """\
You are a "Domain Expert & Historian" AI for a premium news application.
Your goal is to provide deep historical context, explain what events likely led up to this news, and discuss the broader impact on the global or local stage.

Instructions:
1. Use the "ARTICLE TEXT" provided below as your primary source of current events.
2. Even if you cannot access external links, use the topic of the article to provide your expert historical perspective.
3. If the answer is not in the article and not in your historical knowledge, say "I don't have enough context to discuss that."
4. Maintain a professional, intellectual, yet accessible tone.
5. Keep answers insightful but concise (under 400 words).
6. CRITICAL: You MUST respond entirely in the [LANGUAGE] specified below.
"""

_FALLBACK_RESPONSES = [
    "I'm having trouble processing that right now. Could you try rephrasing your question?",
    "I'm unable to provide a detailed response at the moment. Please try again shortly.",
]


async def grounded_chat(article_text: str, question: str, language: str = "English") -> dict:
    """
    Send a grounded Q&A request to Gemini using the modern google-genai SDK.
    Returns: { answer: str, model: str, grounded: bool }
    """
    if not GEMINI_API_KEY:
        return {
            "answer": "AI chat is not configured. Please set GEMINI_API_KEY.",
            "model": "none",
            "grounded": False,
        }

    # Initialize client (reused or re-created per request)
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = (
        f"[LANGUAGE]: {language}\n"
        f"--- ARTICLE TEXT ---\n{article_text}\n--- END ARTICLE ---\n\n"
        f"User question: {question}"
    )

    try:
        # Using the new google-genai SDK async call
        # System instructions are part of the GenerateContentConfig in the new SDK
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_GROUNDED_SYSTEM_PROMPT,
                temperature=0.2,
                top_p=0.8,
                max_output_tokens=500,
            ),
        )

        answer = response.text.strip() if response.text else _FALLBACK_RESPONSES[0]
        return {"answer": answer, "model": "gemini-2.5-flash", "grounded": True}

    except Exception as exc:
        print(f"[Gemini] Error: {exc}")
        return {
            "answer": _FALLBACK_RESPONSES[0],
            "model": "fallback",
            "grounded": False,
        }
