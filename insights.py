"""
insights.py
Step 6: AI-driven Insights Engine (Pattern, Risk, Action).
Uses Groq to generate actionable insights and a drafted message based on the profile.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def generate_insights(profile: dict, owner_name: str) -> dict:
    """Takes a scored profile and uses LLM to generate Pattern, Risk, and Action insights."""
    
    # We only want to send relevant structured data to the LLM to save tokens and focus it
    context = f"""
Contact: {profile['contact_name']}
Owner (You): {owner_name}
Relationship Type: {profile['relationship_type']}
Current State: {profile.get('health_state', 'Unknown')} (Score: {profile.get('health_score', 0)}/100)
Urgency: {profile['urgency']}
Topics Discussed: {', '.join(profile.get('topics', []))}
Pending Items: {', '.join(profile.get('pending_items', []))}
Emotional Events: {', '.join(profile.get('emotional_events', []))}
"""

    prompt = f"""You are an advanced relationship intelligence engine. 
Based on the following contact profile, generate three distinct insights.

PROFILE:
{context}

Provide your response in exactly this format (do not include Markdown formatting or tags, just the raw text blocks separated by newlines):

PATTERN:
[1-2 sentences identifying the core communication habit, emotional tone, or topic focus.]

RISK:
[1-2 sentences identifying any risks like fading contact, unresolved pending items, or negative shifts. If none, say "Relationship is stable."]

ACTION:
[A precise, natural-sounding drafted message that {owner_name} could copy-paste and send to {profile['contact_name']} right now, based specifically on the topics or pending items. Do not use placeholders.]
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        
        raw = response.choices[0].message.content.strip()
        
        # Parse the output
        pattern = ""
        risk = ""
        action = ""
        
        current_section = None
        for line in raw.split("\n"):
            line = line.strip()
            if line.startswith("PATTERN:"):
                current_section = "pattern"
                pattern += line.replace("PATTERN:", "").strip() + " "
            elif line.startswith("RISK:"):
                current_section = "risk"
                risk += line.replace("RISK:", "").strip() + " "
            elif line.startswith("ACTION:"):
                current_section = "action"
                action += line.replace("ACTION:", "").strip() + " "
            elif current_section == "pattern":
                pattern += line + " "
            elif current_section == "risk":
                risk += line + " "
            elif current_section == "action":
                action += line + " "

        profile["insights"] = {
            "pattern": pattern.strip() or "No clear pattern identified.",
            "risk": risk.strip() or "No immediate risks.",
            "action": action.strip() or "Hey, just checking in!"
        }
        
    except Exception as e:
         profile["insights"] = {
            "pattern": "Insight generation failed.",
            "risk": str(e),
            "action": "Hey, it's been a while!"
        }

    return profile


if __name__ == "__main__":
    from parser import load_all_chats
    from analyzer import analyze_chat
    from merger import merge_analyses
    from scorer import calculate_score
    
    OWNER_NAME = "Ayush Waman"
    
    print("\n💡 Running Insights Engine...\n")
    chats = load_all_chats()
    
    for chat in chats:
        analyzed = analyze_chat(chat, OWNER_NAME)
        merged = merge_analyses(analyzed, OWNER_NAME)
        scored = calculate_score(merged)
        
        print(f"Generating insights for {scored['contact_name']}...")
        final_profile = generate_insights(scored, OWNER_NAME)
        
        print("\n" + "="*50)
        print(f"👤 {final_profile['contact_name']} | {final_profile['health_score']}/100")
        print("="*50)
        ins = final_profile["insights"]
        print(f"\n🔍 PATTERN: {ins['pattern']}")
        print(f"\n⚠️ RISK:    {ins['risk']}")
        print(f"\n✉️ ACTION:  {ins['action']}")
        print("="*50 + "\n")
