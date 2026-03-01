"""
telegram_fetcher.py
Step 1: Connect to Telegram via Telethon and fetch all dialogs (DMs + groups).
Saves raw messages as JSON to the data/ folder.
"""

import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")
SESSION_NAME = "reflect_session"
DATA_DIR = "data"
MESSAGES_PER_DIALOG = 200
AVATAR_DIR = os.path.join("static", "avatars")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(AVATAR_DIR, exist_ok=True)


def get_dialog_name(dialog):
    entity = dialog.entity
    if isinstance(entity, User):
        parts = [entity.first_name or "", entity.last_name or ""]
        return " ".join(p for p in parts if p).strip() or f"user_{entity.id}"
    elif isinstance(entity, (Chat, Channel)):
        return entity.title or f"group_{entity.id}"
    return f"unknown_{dialog.id}"


def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip()


async def fetch_all_dialogs(client):
    print("\n📡 Fetching dialogs...\n")
    dialogs = await client.get_dialogs()
    print(f"Found {len(dialogs)} dialogs\n")

    fetched = []
    for dialog in dialogs:
        name = get_dialog_name(dialog)
        safe_name = sanitize_filename(name)
        avatar_path = os.path.join(AVATAR_DIR, f"{safe_name}.jpg")
        avatar_url = f"/static/avatars/{safe_name}.jpg"

        try:
            # Download profile photo
            print(f"  📸 Downloading PFP for {name}...")
            await client.download_profile_photo(dialog.entity, file=avatar_path)
            
            messages = []
            async for msg in client.iter_messages(dialog.entity, limit=MESSAGES_PER_DIALOG):
                if not msg.text:
                    continue  # skip non-text messages
                sender_name = "Unknown"
                try:
                    if msg.sender:
                        s = msg.sender
                        if isinstance(s, User):
                            sender_name = " ".join(
                                filter(None, [s.first_name, s.last_name])
                            ) or f"user_{s.id}"
                        else:
                            sender_name = getattr(s, "title", f"entity_{s.id}")
                except Exception:
                    pass

                messages.append({
                    "id": msg.id,
                    "sender": sender_name,
                    "text": msg.text,
                    "timestamp": msg.date.isoformat() if msg.date else None,
                    "is_outgoing": msg.out,
                })

            if not messages:
                print(f"  ⚠️  Skipped (no text messages): {name}")
                continue

            # Reverse so oldest first
            messages.reverse()

            data = {
                "chat_name": name,
                "dialog_type": "dm" if isinstance(dialog.entity, User) else "group",
                "avatar_url": avatar_url if os.path.exists(avatar_path) else None,
                "message_count": len(messages),
                "messages": messages,
            }

            out_path = os.path.join(DATA_DIR, f"{safe_name}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"  ✅  {name} ({len(messages)} msgs) → {out_path}")
            fetched.append(name)

        except Exception as e:
            print(f"  ❌  Failed for {name}: {e}")

    print(f"\n✅ Done! Fetched {len(fetched)} dialogs into '{DATA_DIR}/'")
    return fetched


async def main():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("✅ Logged in to Telegram!")
    await fetch_all_dialogs(client)
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
