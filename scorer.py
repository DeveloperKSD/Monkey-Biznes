"""
scorer.py
Step 5: Compute a definitive Relationship Health Score (0-100) based on multiple factors.
Includes frequency, recency, reciprocity, sentiment, and drift.
"""

from datetime import datetime, timedelta
import math

# Baseline expectations for normalization
EXPECTED_MSGS_PER_WEEK = 20
MAX_SILENCE_DAYS = 30


def get_days_since(iso_timestamp_str: str) -> float:
    if not iso_timestamp_str:
        return MAX_SILENCE_DAYS
    try:
        dt = datetime.fromisoformat(iso_timestamp_str.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo) 
        return max(0.0, (now - dt).total_seconds() / 86400.0)
    except Exception:
        return MAX_SILENCE_DAYS


def compute_deep_metrics(messages: list) -> dict:
    """ Computes Average Response Time and Inactivity Drift metrics from raw message timestamps. """
    if not messages or len(messages) < 2:
        return {"avg_response_hours": 0.0, "avg_gap_days": 0.0, "delayed_replies": 0}

    response_times_hours = []
    session_gaps_days = []
    delayed_replies_count = 0
    
    # 1. Calculate Average Response Time (Incoming -> Outgoing)
    pending_incoming = None
    
    # 2. Calculate Average Gap between conversational sessions
    last_msg_time = None
    SESSION_THRESHOLD_HOURS = 12.0

    for msg in messages:
        try:
            ts = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
        except Exception:
            continue
            
        # Session Gap Logic
        if last_msg_time:
            gap_hours = (ts - last_msg_time).total_seconds() / 3600.0
            if gap_hours > SESSION_THRESHOLD_HOURS:
                session_gaps_days.append(gap_hours / 24.0)
        last_msg_time = ts

        # Response Time Logic
        if not msg["is_outgoing"]:
            if not pending_incoming:
                pending_incoming = ts # We received a message, clock starts
        else:
            if pending_incoming:
                # We replied! Clock stops.
                resp_hours = (ts - pending_incoming).total_seconds() / 3600.0
                response_times_hours.append(resp_hours)
                pending_incoming = None

    avg_resp = sum(response_times_hours) / len(response_times_hours) if response_times_hours else 0.0
    avg_gap = sum(session_gaps_days) / len(session_gaps_days) if session_gaps_days else 1.0 # default to 1 day if sparse
    
    # Second pass for delayed replies (> 2x average)
    if avg_resp > 0:
        for rt in response_times_hours:
            if rt > (avg_resp * 2.0):
                delayed_replies_count += 1

    # 3. Calculate Average Message Length (Engagement Depth)
    user_words = 0
    contact_words = 0
    user_msgs = 0
    contact_msgs = 0

    for msg in messages:
        txt = msg.get("text", "")
        words = len(txt.split())
        if msg["is_outgoing"]:
            user_words += words
            user_msgs += 1
        else:
            contact_words += words
            contact_msgs += 1

    avg_user_len = user_words / user_msgs if user_msgs > 0 else 0.0
    avg_contact_len = contact_words / contact_msgs if contact_msgs > 0 else 0.0
    
    # Engagement ratio: how much effort they put in relative to you
    # 1.0 means equal effort. 0.1 means they reply with 1/10th of your length.
    # We cap this at 1.0 to prevent scores > 100%
    engagement_ratio = 1.0
    if avg_user_len > 0:
        engagement_ratio = min(1.0, avg_contact_len / avg_user_len)
    
    # Flag "Low Effort" if ratio is low AND their average length is very short
    is_low_effort = False
    if contact_msgs > 3: # enough data to judge
        if engagement_ratio < 0.3 or avg_contact_len < 3.0:
            is_low_effort = True

    return {
        "avg_response_hours": round(avg_resp, 1),
        "avg_gap_days": round(avg_gap, 1),
        "delayed_replies": delayed_replies_count,
        "avg_user_len": round(avg_user_len, 1),
        "avg_contact_len": round(avg_contact_len, 1),
        "engagement_ratio": round(engagement_ratio, 2),
        "is_low_effort": is_low_effort
    }


def calculate_score(profile: dict) -> dict:
    """Takes a merged profile and computes health scores."""
    
    # -- Deep Insights Computation (Now first, so we can use them in scoring) --
    deep_metrics = compute_deep_metrics(profile.get("raw_messages", []))
    profile.update(deep_metrics) # Merge all deep metrics into profile
    
    days_since_last = get_days_since(profile.get("last_message_at"))
    
    # 1. Recency Score (Exponential Decay)
    # If drift is high (> 2.0), we accelerate the decay
    drift_factor = 1.0
    if deep_metrics["avg_gap_days"] > 0:
        drift_ratio = days_since_last / deep_metrics["avg_gap_days"]
        if drift_ratio > 2.0:
            drift_factor = 1.5 # Accelerate decay if habit is broken
    else:
        drift_ratio = 0.0
        
    profile["drift_score_ratio"] = round(drift_ratio, 2)
    
    recency_score = math.exp(-3.0 * drift_factor * (days_since_last / MAX_SILENCE_DAYS))
    recency_score = max(0.0, min(1.0, recency_score))

    # 2. Frequency Score
    days_active = 1.0
    if profile.get("first_message_at") and profile.get("last_message_at"):
        try:
            first = datetime.fromisoformat(profile["first_message_at"])
            last = datetime.fromisoformat(profile["last_message_at"])
            days_active = max(1.0, (last - first).total_seconds() / 86400.0)
        except Exception:
            pass
            
    msgs_per_week = (profile.get("message_count", 0) / days_active) * 7.0
    frequency_score = min(1.0, msgs_per_week / EXPECTED_MSGS_PER_WEEK)

    # 3. Reciprocity Score (Quantity Balance)
    out_c = profile.get("outgoing_count", 0)
    in_c = profile.get("incoming_count", 0)
    total = out_c + in_c
    if total == 0:
        reciprocity_score = 0.0
    else:
        out_ratio = out_c / total
        distance_from_perfect = abs(0.5 - out_ratio)
        reciprocity_score = 1.0 - (distance_from_perfect / 0.5)

    # 4. Sentiment Score
    raw_sentiment = profile.get("sentiment_score", 0.0)
    sentiment_score = (raw_sentiment + 1.0) / 2.0

    # 5. Engagement Score (Effort/Length Balance)
    # The engagement_ratio tells us how their length compares to ours.
    # 1.0 is perfect balance. 0.1 is 10% of our effort.
    engagement_score = min(1.0, deep_metrics["engagement_ratio"])

    # New Weights: Favor Sentiment and Engagement Balance
    w_recency = 0.20
    w_frequency = 0.15
    w_reciprocity = 0.10
    w_sentiment = 0.35 # Sentiment is now king
    w_engagement = 0.20 

    final_score = (
        (recency_score * w_recency) +
        (frequency_score * w_frequency) +
        (reciprocity_score * w_reciprocity) +
        (sentiment_score * w_sentiment) +
        (engagement_score * w_engagement)
    ) * 100.0

    # Hostile Mood Penalty
    # If the mood is explicitly negative, slash the score heavily.
    if profile.get("mood") == "negative":
        final_score -= 50.0  # Even harsher penalty
        
    # Sentiment Crisis Drop
    # If the raw sentiment is very low, apply another penalty.
    if raw_sentiment < -0.3:
        final_score -= 20.0

    # Low Effort Penalty
    if deep_metrics["is_low_effort"]:
        final_score -= 10.0

    # Urgency Bonus (up to +5 points)
    if profile.get("urgency") == "high":
        final_score += 5.0
    elif profile.get("urgency") == "medium":
        final_score += 2.0

    final_score = max(0.0, min(100.0, final_score))

    # Relationship Crisis Override
    # If the AI detected a crisis (hostility, breakup), force the score down.
    if profile.get("relationship_crisis"):
        final_score = max(0.0, min(final_score, 10.0)) # Force to near zero, but not negative
        state = "At Risk"
    else:
        # Determine State with Sentiment Overrides
        # If mood is negative OR sentiment is low, it MUST be At Risk
        if final_score >= 70 and profile.get("mood") != "negative" and raw_sentiment > 0.1:
            state = "Active"
        elif final_score >= 40 and profile.get("mood") != "negative" and raw_sentiment > -0.1:
            state = "Cooling"
        else:
            state = "At Risk"

    profile["health_score"] = round(final_score, 1)
    profile["health_state"] = state
    profile["components"] = {
        "recency": round(recency_score, 2),
        "frequency": round(frequency_score, 2),
        "reciprocity": round(reciprocity_score, 2),
        "sentiment": round(sentiment_score, 2),
        "engagement": round(engagement_score, 2)
    }

    return profile

    return profile


if __name__ == "__main__":
    from parser import load_all_chats
    from analyzer import analyze_chat
    from merger import merge_analyses
    
    OWNER_NAME = "Ayush Waman"
    
    print("\n⚖️ Running Scorer Pipeline...\n")
    chats = load_all_chats()
    
    for chat in chats:
        analyzed = analyze_chat(chat, OWNER_NAME)
        merged = merge_analyses(analyzed, OWNER_NAME)
        scored = calculate_score(merged)
        
        print(f"\n📊 Score for: {scored['contact_name']}")
        print(f"   Final Score : {scored['health_score']}/100 ({scored['health_state']})")
        comp = scored["components"]
        print(f"   Components  : Recency={comp['recency']} | Freq={comp['frequency']} | Recip={comp['reciprocity']} | Sent={comp['sentiment']}")
        print("-" * 50)
