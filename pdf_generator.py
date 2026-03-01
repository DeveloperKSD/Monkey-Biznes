"""
pdf_generator.py
Step 7: Generate a minimalist PDF report for a given contact profile 
using FPDF2. Handles line wrapping and Unicode to prevent rendering errors.
"""

import os
from fpdf import FPDF

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        # Use built-in Helvetica which handles most standard characters well.
        # Alternatively, add a TTF font if we had one.
        pass

    def header(self):
        self.set_font("helvetica", "B", 16)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, "Reflect AI - Relationship Profile", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Generated automatically - Page {self.page_no()}", align="C")


def safe_text(text: str) -> str:
    """Strip or replace characters that standard Helvetica can't render. 
    Forces ASCII only to ensure zero crashes in the PDF engine."""
    if not text:
        return ""
    text = str(text)
    # Replace common typography quotes and characters first
    replacements = {
        '—': '-', '–': '-', 
        '“': '"', '”': '"', 
        '‘': "'", '’': "'", 
        '…': '...',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        'ñ': 'n', 'ç': 'c'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    # Final fallback: encode to ascii and ignore everything else
    return text.encode('ascii', 'ignore').decode('ascii')


def generate_pdf(profile: dict) -> str:
    """Takes a fully scored & analyzed profile and writes it to a PDF."""
    
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Clean data
    name = safe_text(profile.get("contact_name", "Unknown"))
    score = profile.get("health_score", 0)
    state = safe_text(profile.get("health_state", "Unknown"))
    rel_type = safe_text(profile.get("relationship_type", "Unknown").title())
    urgency = safe_text(profile.get("urgency", "Unknown").title())
    mood = safe_text(profile.get("mood", "Unknown").title())

    # Title section
    pdf.set_font("helvetica", "B", 24)
    pdf.set_text_color(0, 102, 204)  # Blue
    pdf.cell(0, 12, name, ln=True)

    pdf.set_font("helvetica", "B", 14)
    if state == "Active":
        pdf.set_text_color(34, 139, 34)  # Green
    elif state == "Cooling":
        pdf.set_text_color(255, 140, 0)  # Orange
    else:
        pdf.set_text_color(220, 20, 60)  # Red
        
    pdf.cell(0, 8, f"Health Score: {score}/100 ({state})", ln=True)
    pdf.ln(8)

    # Core details
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 6, f"Type: {rel_type}", ln=True)
    pdf.cell(0, 6, f"Mood: {mood}", ln=True)
    pdf.cell(0, 6, f"Urgency: {urgency}", ln=True)
    pdf.ln(5)

    # Topics & Pending
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "Key Topics", ln=True)
    pdf.set_font("helvetica", "", 11)
    
    topics = [safe_text(t) for t in profile.get("topics", [])]
    if topics:
        pdf.multi_cell(0, 6, "- " + "\n- ".join(topics))
    else:
        pdf.cell(0, 6, "None detected.", ln=True)
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Pending Action Items", ln=True)
    pdf.set_font("helvetica", "", 11)
    
    pending = [safe_text(p) for p in profile.get("pending_items", [])]
    if pending:
        pdf.multi_cell(0, 6, "- " + "\n- ".join(pending))
    else:
        pdf.cell(0, 6, "No pending items.", ln=True)
    pdf.ln(8)

    # Events & Todos
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Actionable Todos", ln=True)
    pdf.set_font("helvetica", "", 11)
    
    todos = [safe_text(t) for t in profile.get("actionable_todos", [])]
    if todos:
        pdf.multi_cell(0, 6, "- " + "\n- ".join(todos))
    else:
        pdf.cell(0, 6, "No pending tasks detected.", ln=True)
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Upcoming Events", ln=True)
    pdf.set_font("helvetica", "", 11)
    
    events = [safe_text(e) for e in profile.get("calendar_events", [])]
    if events:
        pdf.multi_cell(0, 6, "- " + "\n- ".join(events))
    else:
        pdf.cell(0, 6, "No upcoming events detected.", ln=True)
    pdf.ln(8)

    # Insights
    ins = profile.get("insights", {})
    
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 10, "Intelligence & Insights", ln=True)
    pdf.set_text_color(0, 0, 0)

    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, "Pattern Identified:", ln=True)
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(0, 6, safe_text(ins.get("pattern", "")))
    pdf.ln(4)

    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, "Risk Assessment:", ln=True)
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(0, 6, safe_text(ins.get("risk", "")))
    pdf.ln(4)

    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(34, 139, 34)
    pdf.cell(0, 6, "Suggested Message:", ln=True)
    pdf.set_font("helvetica", "I", 11)
    pdf.set_text_color(50, 50, 50)
    # Write the drafted message
    pdf.multi_cell(0, 6, f'"{safe_text(ins.get("action", ""))}"')

    # Save
    safe_filename = "".join(c if c.isalnum() else "_" for c in name).strip()
    out_path = os.path.join(REPORTS_DIR, f"{safe_filename}.pdf")
    pdf.output(out_path)
    
    return out_path


if __name__ == "__main__":
    from parser import load_all_chats
    from analyzer import analyze_chat
    from merger import merge_analyses
    from scorer import calculate_score
    from insights import generate_insights
    
    OWNER_NAME = "Ayush Waman"
    
    print("\n📄 Running PDF Generator...\n")
    chats = load_all_chats()
    
    if not chats:
        print("No chats found in data/")
    else:
        # Just run for the first chat to test
        chat = chats[0]
        print(f"Generating full profile for {chat['chat_name']}...")
        analyzed = analyze_chat(chat, OWNER_NAME)
        merged = merge_analyses(analyzed, OWNER_NAME)
        scored = calculate_score(merged)
        final_profile = generate_insights(scored, OWNER_NAME)
        
        pdf_path = generate_pdf(final_profile)
        print(f"✅ Success! Generated PDF: {pdf_path}")
