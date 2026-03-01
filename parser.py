"""
parser.py
Step 2: Load raw JSON files from data/ and normalize them into a
standard list of Message dicts, ready for the analyzer.
"""

import os
import json
from datetime import datetime, timezone

DATA_DIR = "data"


def load_all_chats():
    """Load and normalize all chat JSON files from the data/ directory."""
    all_chats = []

    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)

        chat = parse_chat(raw)
        if chat:
            all_chats.append(chat)

    return all_chats


def parse_chat(raw: dict) -> dict | None:
    """Normalize a single raw chat dict into a structured format."""
    messages = []

    for msg in raw.get("messages", []):
        text = (msg.get("text") or "").strip()
        if not text:
            continue

        timestamp_str = msg.get("timestamp")
        try:
            ts = datetime.fromisoformat(timestamp_str)
            # Normalize to UTC
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except Exception:
            ts = None

        messages.append({
            "sender": (msg.get("sender") or "Unknown").strip(),
            "text": text,
            "timestamp": ts.isoformat() if ts else None,
            "is_outgoing": bool(msg.get("is_outgoing", False)),
        })

    if not messages:
        return None

    return {
        "chat_name": raw.get("chat_name", "Unknown"),
        "dialog_type": raw.get("dialog_type", "dm"),  # "dm" or "group"
        "avatar_url": raw.get("avatar_url"),
        "message_count": len(messages),
        "messages": messages,
        # Derived stats
        "first_message_at": messages[0]["timestamp"],
        "last_message_at": messages[-1]["timestamp"],
        "participants": sorted(set(m["sender"] for m in messages)),
        "outgoing_count": sum(1 for m in messages if m["is_outgoing"]),
        "incoming_count": sum(1 for m in messages if not m["is_outgoing"]),
    }


if __name__ == "__main__":
    chats = load_all_chats()
    print(f"\n✅ Parsed {len(chats)} chat(s) from data/\n")
    for chat in chats:
        print(f"  📂 {chat['chat_name']} [{chat['dialog_type']}]")
        print(f"     Participants : {', '.join(chat['participants'])}")
        print(f"     Messages     : {chat['message_count']} (out: {chat['outgoing_count']}, in: {chat['incoming_count']})")
        print(f"     From → To    : {chat['first_message_at']} → {chat['last_message_at']}")
        print()
        print("  --- First 3 messages ---")
        for msg in chat["messages"][:3]:
            direction = "→" if msg["is_outgoing"] else "←"
            print(f"  {direction} [{msg['timestamp']}] {msg['sender']}: {msg['text']}")
        print()
