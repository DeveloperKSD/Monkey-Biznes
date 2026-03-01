"""
analyzer.py
Step 3: Send conversation chunks to Groq LLM for structured relationship analysis.
Extracts: relationship_type, mood, urgency, topics, pending_items, participants.
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"
print("🚀 Reflect AI Analysis Engine v2.1 (Hostility-Aware, ChunkSize=15)")

CHUNK_SIZE = 15  # Smaller windows to catch rapid tone shifts

def format_messages_for_prompt(messages: list, owner_name: str) -> str:
    lines = []
    for msg in messages:
        direction = "You" if msg["is_outgoing"] else msg["sender"]
        lines.append(f"[{msg['timestamp'][:16]}] {direction}: {msg['text']}")
    return "\n".join(lines)


def analyze_chunk(chunk: list, chat_name: str, dialog_type: str, owner_name: str) -> dict:
    conversation_text = format_messages_for_prompt(chunk, owner_name)

    prompt = f"""You are a relationship intelligence and personal assistant engine. Analyze the following {dialog_type} conversation between {owner_name} and {chat_name}.

CONVERSATION:
{conversation_text}

Respond ONLY with a valid JSON object (no markdown, no explanation) with these EXACT fields in this order:
{{
  "mood": "positive|neutral|negative|mixed",
  "sentiment_score": 0.0,
  "relationship_crisis": true|false,
  "relationship_type": "friend|colleague|family|romantic|acquaintance|group",
  "urgency": "high|medium|low",
  "topics": ["topic1", "topic2"],
  "pending_items": ["item1"],
  "actionable_todos": ["Buy milk", "Call bank tomorrow"],
  "calendar_events": ["Dinner on Friday at 8 PM", "Meeting next week"],
  "emotional_events": ["event1"],
  "forgotten_followups": ["Question asked by other person that wasn't answered"],
  "missed_mentions": ["User mentioned they have an exam tomorrow"],
  "buried_plans": ["Let's catch up sometime soon"],
  "last_active_speaker": "name",
  "conversation_summary": "one sentence summary"
}}

Rules:
- mood: MUST be "negative" if there is ANY hostility, anger, "breakup" language, or explicit rejection (e.g., "I hate you", "done with you").
- sentiment_score: Float from -1.0 (hostile) to 1.0 (very positive). If the contact is hostile, this MUST be below -0.6.
- relationship_crisis: Set to TRUE if the contact explicitly expresses dislike or wants to end the relationship.
- CRITICAL: Pay 100% attention to the LATEST messages in the window. A sharp turn into hostility MUST dominate the entire analysis of this window.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=800,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "participants": [],
            "relationship_type": "unknown",
            "mood": "neutral",
            "sentiment_score": 0.0,
            "urgency": "low",
            "topics": [],
            "pending_items": [],
            "actionable_todos": [],
            "calendar_events": [],
            "emotional_events": [],
            "forgotten_followups": [],
            "missed_mentions": [],
            "buried_plans": [],
            "last_active_speaker": "",
            "conversation_summary": "Analysis failed.",
        }


def analyze_chat(chat: dict, owner_name: str) -> dict:
    """Analyze a full chat by chunking it and calling Groq on each chunk."""
    messages = chat["messages"]
    chunks = [messages[i:i + CHUNK_SIZE] for i in range(0, len(messages), CHUNK_SIZE)]

    analyses = []
    for i, chunk in enumerate(chunks):
        print(f"    🔍 Analyzing chunk {i+1}/{len(chunks)} for '{chat['chat_name']}'...")
        result = analyze_chunk(chunk, chat["chat_name"], chat["dialog_type"], owner_name)
        analyses.append(result)

    return {
        "chat_name": chat["chat_name"],
        "dialog_type": chat["dialog_type"],
        "message_count": chat["message_count"],
        "first_message_at": chat["first_message_at"],
        "last_message_at": chat["last_message_at"],
        "outgoing_count": chat["outgoing_count"],
        "incoming_count": chat["incoming_count"],
        "analyses": analyses,
        "raw_messages": chat["messages"]
    }


if __name__ == "__main__":
    from parser import load_all_chats

    OWNER_NAME = "Ayush Waman"  # The logged-in user's name

    chats = load_all_chats()
    print(f"\n🤖 Analyzing {len(chats)} chat(s) with Groq...\n")

    for chat in chats:
        print(f"📂 {chat['chat_name']}")
        result = analyze_chat(chat, OWNER_NAME)
        print(f"\n✅ Analysis for '{chat['chat_name']}':")
        for i, a in enumerate(result["analyses"]):
            print(f"\n  Window {i+1}:")
            print(f"    Relationship : {a.get('relationship_type')}")
            print(f"    Mood         : {a.get('mood')} (score: {a.get('sentiment_score')})")
            print(f"    Urgency      : {a.get('urgency')}")
            print(f"    Topics       : {', '.join(a.get('topics', []))}")
            print(f"    Pending      : {', '.join(a.get('pending_items', []))}")
            print(f"    Summary      : {a.get('conversation_summary')}")
        print()
