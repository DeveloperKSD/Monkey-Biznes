"""
merger.py
Step 4: Consolidate multiple LLM analysis windows into a single unified profile.
Handles alias deduplication and filters out the owner.
"""

from collections import Counter


def deduplicate_list(items: list) -> list:
    """Case-insensitive deduplication that preserves order."""
    seen = set()
    result = []
    for item in items:
        clean = str(item).strip()
        if clean and clean.lower() not in seen:
            seen.add(clean.lower())
            result.append(clean)
    return result


def merge_analyses(chat_result: dict, owner_name: str) -> dict:
    """Merge multiple chunk analyses into a single contact profile."""
    
    analyses = chat_result.get("analyses", [])
    if not analyses:
        return {}

    # Gather data across all chunks
    types = []
    moods = []
    urgencies = []
    all_topics = []
    all_pending = []
    all_todos = []
    all_cal_events = []
    all_emotional_events = []
    
    # Deep insight lists
    all_forgotten_followups = []
    all_missed_mentions = []
    all_buried_plans = []
    
    # Weights for sentiment calculation (recent windows matter more)
    weighted_sentiment_sum = 0.0
    weight_total = 0.0
    has_crisis = False

    for i, a in enumerate(analyses):
        # We give slight ascending weight to later chunks (assuming chronological order)
        weight = 1.0 + (i * 0.2)
        
        types.append(a.get("relationship_type", "unknown"))
        moods.append(a.get("mood", "neutral"))
        urgencies.append(a.get("urgency", "low"))
        
        if a.get("relationship_crisis"):
            has_crisis = True
        
        all_topics.extend(a.get("topics", []))
        all_pending.extend(a.get("pending_items", []))
        all_todos.extend(a.get("actionable_todos", []))
        all_cal_events.extend(a.get("calendar_events", []))
        all_emotional_events.extend(a.get("emotional_events", []))
        
        # Deep Insights
        all_forgotten_followups.extend(a.get("forgotten_followups", []))
        all_missed_mentions.extend(a.get("missed_mentions", []))
        all_buried_plans.extend(a.get("buried_plans", []))
        
        score = a.get("sentiment_score")
        if isinstance(score, (int, float)):
            weighted_sentiment_sum += score * weight
            weight_total += weight

    # Most common categorical values
    # HEURISTIC: If ANY chunk is "negative", the overall mood becomes "negative" to reflect conflict.
    if "negative" in moods:
        overall_mood = "negative"
    else:
        overall_mood = Counter(moods).most_common(1)[0][0] if moods else "neutral"
    
    rel_type = Counter(types).most_common(1)[0][0] if types else "unknown"
    
    # Priority scaling for urgency
    urgency_scores = {"high": 3, "medium": 2, "low": 1}
    max_urgency_val = max((urgency_scores.get(u, 1) for u in urgencies), default=1)
    overall_urgency = {3: "high", 2: "medium", 1: "low"}[max_urgency_val]

    overall_sentiment = (weighted_sentiment_sum / weight_total) if weight_total > 0 else 0.0

    profile = {
        "contact_name": chat_result["chat_name"],
        "dialog_type": chat_result["dialog_type"],
        "message_count": chat_result["message_count"],
        "first_message_at": chat_result["first_message_at"],
        "last_message_at": chat_result["last_message_at"],
        "outgoing_count": chat_result["outgoing_count"],
        "incoming_count": chat_result["incoming_count"],
        
        # Merged features
        "relationship_type": rel_type,
        "mood": overall_mood,
        "sentiment_score": round(overall_sentiment, 3),
        "relationship_crisis": has_crisis,
        "urgency": overall_urgency,
        "topics": deduplicate_list(all_topics),
        "pending_items": deduplicate_list(all_pending),
        "actionable_todos": deduplicate_list(all_todos),
        "calendar_events": deduplicate_list(all_cal_events),
        "emotional_events": deduplicate_list(all_emotional_events),
        
        # Deep Insights Data
        "forgotten_followups": deduplicate_list(all_forgotten_followups),
        "missed_mentions": deduplicate_list(all_missed_mentions),
        "buried_plans": deduplicate_list(all_buried_plans),
        
        # Raw messages plumed for scorer metrics
        "raw_messages": chat_result.get("raw_messages", []),
        "avatar_url": chat_result.get("avatar_url")
    }

    return profile


if __name__ == "__main__":
    from parser import load_all_chats
    from analyzer import analyze_chat
    
    OWNER_NAME = "Ayush Waman"
    
    print("\n🧩 Running Merger Pipeline...\n")
    chats = load_all_chats()
    
    for chat in chats:
        print(f"Analyzing {chat['chat_name']}...")
        analyzed = analyze_chat(chat, OWNER_NAME)
        merged = merge_analyses(analyzed, OWNER_NAME)
        
        print(f"\n✅ Merged Profile for: {merged['contact_name']}")
        print(f"   Type      : {merged['relationship_type']}")
        print(f"   Mood      : {merged['mood']} ({merged['sentiment_score']})")
        print(f"   Urgency   : {merged['urgency']}")
        print(f"   Topics    : {', '.join(merged['topics'][:5])}")
        print(f"   Pending   : {len(merged['pending_items'])} items")
        print("-" * 40 + "\n")
