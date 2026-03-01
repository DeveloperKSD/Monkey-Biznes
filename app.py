"""
app.py
Step 8: Flask web dashboard for Reflect AI.
Serves the relationship profiles, insights, charts, and PDF downloads.
"""

from flask import Flask, render_template, jsonify, send_file, request
import os
import json

from parser import load_all_chats
from analyzer import analyze_chat
from merger import merge_analyses
from scorer import calculate_score
from insights import generate_insights
from pdf_generator import generate_pdf

app = Flask(__name__)
OWNER_NAME = "Ayush Waman"
COMPLETED_TODOS_FILE = os.path.join("data", "completed_todos.json")

# Simple in-memory cache so we don't re-run Groq on every refresh
cache = {
    "contacts": None
}


@app.route("/")
def index():
    return render_template("index.html", owner_name=OWNER_NAME)


@app.route("/api/contacts")
def get_contacts():
    global cache
    
    if cache["contacts"] is not None:
        return jsonify(cache["contacts"])

    print("--- Running Full Pipeline for Dashboard ---")
    chats = load_all_chats()
    contacts = []
    
    for chat in chats:
        try:
            analyzed = analyze_chat(chat, OWNER_NAME)
            merged = merge_analyses(analyzed, OWNER_NAME)
            scored = calculate_score(merged)
            final_profile = generate_insights(scored, OWNER_NAME)
            
            print(f"📊 {final_profile['contact_name']}: Mood={final_profile.get('mood')} | Sentiment={final_profile.get('sentiment_score')} | Score={final_profile.get('health_score')}")
            
            # Filter out completed todos
            final_profile["actionable_todos"] = _filter_completed_todos(
                final_profile["contact_name"], 
                final_profile.get("actionable_todos", [])
            )
            
            # We also generate the PDF right away so the download link is ready
            try:
                pdf_path = generate_pdf(final_profile)
                final_profile["pdf_url"] = f"/download_pdf/{os.path.basename(pdf_path)}"
            except Exception as pe:
                print(f"⚠️ PDF generation failed for {final_profile.get('contact_name')}: {pe}")
                final_profile["pdf_url"] = None
                
            contacts.append(final_profile)
            print(f"✅ Processed {final_profile['contact_name']}")
        except Exception as ce:
            print(f"❌ Failed to process chat {chat.get('chat_name')}: {ce}")

    # Sort by health score descending
    contacts.sort(key=lambda x: x["health_score"], reverse=True)
    
    # Add Mock Contacts
    mock_contacts = get_mock_contacts()
    for mc in mock_contacts:
        mc["actionable_todos"] = _filter_completed_todos(mc["contact_name"], mc.get("actionable_todos", []))
    contacts.extend(mock_contacts)
    
    cache["contacts"] = contacts
    return jsonify(contacts)


def _filter_completed_todos(contact_name, todos):
    """Removes todos that have been marked as completed."""
    if not os.path.exists(COMPLETED_TODOS_FILE):
        return todos
    try:
        with open(COMPLETED_TODOS_FILE, "r") as f:
            completed = json.load(f)
        contact_done = completed.get(contact_name, [])
        return [t for t in todos if t not in contact_done]
    except Exception:
        return todos


@app.route("/api/complete_todo", methods=["POST"])
def complete_todo():
    global cache
    data = request.json
    contact_name = data.get("contact_name")
    todo_text = data.get("todo_text")
    
    if not contact_name or not todo_text:
        return jsonify({"status": "error", "message": "Missing data"}), 400
        
    completed = {}
    if os.path.exists(COMPLETED_TODOS_FILE):
        try:
            with open(COMPLETED_TODOS_FILE, "r") as f:
                completed = json.load(f)
        except Exception:
            pass
            
    if contact_name not in completed:
        completed[contact_name] = []
    
    if todo_text not in completed[contact_name]:
        completed[contact_name].append(todo_text)
        
    try:
        with open(COMPLETED_TODOS_FILE, "w") as f:
            json.dump(completed, f, indent=2)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
        
    # Clear cache to reflect changes
    cache["contacts"] = None
    return jsonify({"status": "success"})


def get_mock_contacts():
    """Generates a list of mock contacts for demonstration."""
    import random
    
    mock_data = [
        {
            "contact_name": "Aarya Kadam",
            "health_score": 88.5,
            "health_state": "Active",
            "relationship_type": "Close Friend",
            "urgency": "low",
            "last_message_at": "2024-05-20T10:00:00Z",
            "insights": {
                "pattern": "Consistent daily morning updates and high emotional reciprocity.",
                "risk": "Relationship is stable.",
                "action": "Hey Aarya! Hope your day is going well. Any plans for the weekend?"
            },
            "components": {"recency": 0.95, "frequency": 0.9, "reciprocity": 0.85, "sentiment": 0.8},
            "engagement_ratio": 0.9,
            "is_low_effort": False,
            "actionable_todos": ["Plan coffee next Tuesday"],
            "calendar_events": ["Birthday (June 15th)"],
            "avatar_url": None
        },
        {
            "contact_name": "Akshay Damle",
            "health_score": 52.3,
            "health_state": "Cooling",
            "relationship_type": "Colleague",
            "urgency": "medium",
            "last_message_at": "2024-05-10T15:30:00Z",
            "insights": {
                "pattern": "Weekly professional check-ins, but the frequency has dropped lately.",
                "risk": "Fading contact. Gap between messages is increasing.",
                "action": "Hi Akshay, been a while since we caught up on the project. How's it going?"
            },
            "components": {"recency": 0.5, "frequency": 0.6, "reciprocity": 0.7, "sentiment": 0.6},
            "engagement_ratio": 0.6,
            "is_low_effort": False,
            "actionable_todos": ["Follow up on project X proposal"],
            "calendar_events": [],
            "avatar_url": None
        },
        {
            "contact_name": "Aaryan Shah",
            "health_score": 28.1,
            "health_state": "At Risk",
            "relationship_type": "Acquaintance",
            "urgency": "high",
            "last_message_at": "2024-04-15T09:00:00Z",
            "insights": {
                "pattern": "Sporadic and one-sided communication initiated mostly by you.",
                "risk": "High risk of churn. Very long silence detected.",
                "action": "Hey Aaryan! Just saw something that reminded me of you. Hope you're doing great!"
            },
            "components": {"recency": 0.2, "frequency": 0.3, "reciprocity": 0.4, "sentiment": 0.5},
            "engagement_ratio": 0.3,
            "is_low_effort": True,
            "actionable_todos": ["Decide whether to re-engage or let go"],
            "calendar_events": [],
            "avatar_url": None
        }
    ]
    
    # Add a few more random ones
    random_names = ["Sneha Rao", "Rohan Mehta", "Ishani Gupta", "Vikram Singh"]
    for name in random_names:
        score = random.uniform(20, 90)
        if score >= 70: state = "Active"
        elif score >= 40: state = "Cooling"
        else: state = "At Risk"
        
        mock_data.append({
            "contact_name": name,
            "health_score": round(score, 1),
            "health_state": state,
            "relationship_type": random.choice(["Friend", "Family", "Colleague"]),
            "urgency": random.choice(["low", "medium", "high"]),
            "insights": {
                "pattern": "Regular interaction detected.",
                "risk": "Relationship is stable." if state == "Active" else "Watch for silence.",
                "action": f"Hey {name.split()[0]}, how's everything?"
            },
            "components": {
                "recency": round(score/100, 2),
                "frequency": round(score/100 * 0.8, 2),
                "reciprocity": 0.5,
                "sentiment": 0.5
            },
            "engagement_ratio": 0.7,
            "is_low_effort": score < 30,
            "actionable_todos": [],
            "calendar_events": [],
            "avatar_url": None
        })
        
    return mock_data


@app.route("/download_pdf/<filename>")
def download_pdf(filename):
    pdf_path = os.path.join("reports", filename)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return "File not found", 404


@app.route("/api/refresh")
def refresh_cache():
    global cache
    
    error_msg = None
    # Run the fetcher to get the absolute latest messages
    try:
        print("\n📥 Refresh requested: Fetching latest Telegram data...")
        import asyncio
        from telegram_fetcher import main as fetch_main
        # Re-run the fetch main function
        asyncio.run(fetch_main())
        print("✅ Telegram fetch complete.")
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error fetching new data: {error_msg}")

    # Clear cache so it rebuilds the profiles from the new data
    cache["contacts"] = None
    
    if error_msg:
        return jsonify({"status": "error", "message": error_msg}), 500
    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
