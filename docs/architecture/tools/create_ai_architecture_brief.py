from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT = PROJECT_ROOT / "docs" / "finsight_ai_ai_architecture_brief.pdf"
PAGE_W, PAGE_H = letter
MARGIN = 0.55 * inch
NAVY = colors.HexColor("#102A43")
INK = colors.HexColor("#243B53")
MUTED = colors.HexColor("#627D98")
TEAL = colors.HexColor("#0F766E")
MINT = colors.HexColor("#DFF7F3")
ORANGE = colors.HexColor("#C2410C")
PEACH = colors.HexColor("#FFF1E8")
BLUE = colors.HexColor("#2563EB")
PALE_BLUE = colors.HexColor("#EAF2FF")
LINE = colors.HexColor("#D9E2EC")
WHITE = colors.white


def text(c, x, y, value, size=10, color=INK, font="Helvetica"):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, value)


def wrapped(c, x, y, value, width, size=10, leading=14, color=INK, font="Helvetica"):
    words = value.split()
    lines = []
    line = ""
    c.setFont(font, size)
    for word in words:
        candidate = f"{line} {word}".strip()
        if c.stringWidth(candidate, font, size) <= width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    for item in lines:
        text(c, x, y, item, size, color, font)
        y -= leading
    return y


def heading(c, kicker, title, subtitle=None):
    text(c, MARGIN, PAGE_H - 0.48 * inch, kicker.upper(), 8, TEAL, "Helvetica-Bold")
    text(c, MARGIN, PAGE_H - 0.82 * inch, title, 24, NAVY, "Helvetica-Bold")
    if subtitle:
        wrapped(c, MARGIN, PAGE_H - 1.08 * inch, subtitle, PAGE_W - 2 * MARGIN, 10, 14, MUTED)


def box(c, x, y, w, h, title, body, fill=PALE_BLUE, accent=BLUE, title_size=11):
    c.setFillColor(fill)
    c.setStrokeColor(fill)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    c.setFillColor(accent)
    c.rect(x, y, 5, h, fill=1, stroke=0)
    text(c, x + 14, y + h - 20, title, title_size, NAVY, "Helvetica-Bold")
    wrapped(c, x + 14, y + h - 39, body, w - 28, 9, 12, INK)


def pill(c, x, y, label, fill, width=None):
    width = width or c.stringWidth(label, "Helvetica-Bold", 8) + 18
    c.setFillColor(fill)
    c.roundRect(x, y, width, 18, 9, fill=1, stroke=0)
    text(c, x + 9, y + 6, label, 8, WHITE, "Helvetica-Bold")
    return width


def flow_box(c, x, y, w, h, title, body, fill, accent):
    c.setFillColor(fill)
    c.setStrokeColor(accent)
    c.setLineWidth(1.2)
    c.roundRect(x, y, w, h, 10, fill=1, stroke=1)
    text(c, x + 12, y + h - 20, title, 11, NAVY, "Helvetica-Bold")
    wrapped(c, x + 12, y + h - 39, body, w - 24, 8.5, 11, INK)


def arrow(c, x1, y1, x2, y2, color=TEAL):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.5)
    c.line(x1, y1, x2, y2)
    c.line(x2, y2, x2 - 6, y2 + 3)
    c.line(x2, y2, x2 - 6, y2 - 3)


def footer(c, page_num, total):
    c.setStrokeColor(LINE)
    c.line(MARGIN, 0.43 * inch, PAGE_W - MARGIN, 0.43 * inch)
    text(c, MARGIN, 0.25 * inch, "FinSight AI | AI architecture brief", 8, MUTED)
    text(c, PAGE_W - MARGIN - 55, 0.25 * inch, f"{page_num} / {total}", 8, MUTED)
    if page_num > 1:
        c.linkRect("Back to contents", "contents", (MARGIN, 0.18 * inch, MARGIN + 80, 0.36 * inch), relative=0, thickness=0)
        text(c, MARGIN + 12, 0.25 * inch, "Contents", 8, BLUE)


def page_one(c):
    c.bookmarkPage("contents")
    c.addOutlineEntry("Contents", "contents", level=0, closed=False)
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    text(c, MARGIN, PAGE_H - 0.75 * inch, "FINSIGHT AI", 11, colors.HexColor("#7DD3C7"), "Helvetica-Bold")
    text(c, MARGIN, PAGE_H - 1.55 * inch, "From discrepancy", 29, WHITE, "Helvetica-Bold")
    text(c, MARGIN, PAGE_H - 1.98 * inch, "to defensible action", 29, colors.HexColor("#7DD3C7"), "Helvetica-Bold")
    wrapped(c, MARGIN, PAGE_H - 2.35 * inch, "A concise architecture brief for explaining how FinSight combines financial truth, deterministic investigation, AI reasoning, and human control.", PAGE_W - 2 * MARGIN, 12, 17, colors.HexColor("#D9E2EC"))

    y = PAGE_H - 3.25 * inch
    pill(c, MARGIN, y, "FINANCIAL OPERATIONS", TEAL)
    pill(c, MARGIN + 146, y, "AI-ASSISTED", ORANGE)
    pill(c, MARGIN + 250, y, "HUMAN-CONTROLLED", BLUE)

    c.setFillColor(colors.HexColor("#193B5A"))
    c.roundRect(MARGIN, 1.02 * inch, PAGE_W - 2 * MARGIN, 2.35 * inch, 12, fill=1, stroke=0)
    text(c, MARGIN + 20, 2.95 * inch, "THE ONE-SENTENCE IDEA", 8, colors.HexColor("#7DD3C7"), "Helvetica-Bold")
    wrapped(c, MARGIN + 20, 2.62 * inch, "FinSight detects and investigates financial discrepancies using trusted database evidence, then uses AI to explain the finding and recommend next steps without allowing AI to alter financial records.", PAGE_W - 2 * MARGIN - 40, 15, 21, WHITE, "Helvetica-Bold")
    text(c, MARGIN + 20, 1.42 * inch, "CONTENTS", 8, colors.HexColor("#7DD3C7"), "Helvetica-Bold")
    links = [("01  System map", "flow"), ("02  AI layer", "ai"), ("03  Guardrails", "controls"), ("04  Delivery plan", "roadmap")]
    link_x = MARGIN + 20
    for label, destination in links:
        text(c, link_x, 1.18 * inch, label, 9, WHITE, "Helvetica-Bold")
        c.linkRect(label, destination, (link_x, 1.10 * inch, link_x + 105, 1.30 * inch), relative=0, thickness=0)
        link_x += 120
    footer(c, 1, 5)
    c.showPage()


def page_two(c):
    c.bookmarkPage("flow")
    c.addOutlineEntry("01 / System map", "flow", level=0, closed=False)
    heading(c, "01 / System map", "How the platform works", "The system separates facts, reasoning, and decisions so every AI explanation can be traced back to financial evidence.")
    y = PAGE_H - 1.65 * inch
    x = MARGIN
    w = PAGE_W - 2 * MARGIN
    h = 0.64 * inch
    stages = [
        ("1. Financial database", "PostgreSQL stores settlements, transactions, orders, executions, and cash movements.", PALE_BLUE, BLUE),
        ("2. Reconciliation", "Deterministic code compares expected cash with completed cash movements.", MINT, TEAL),
        ("3. Investigation engine", "Rules classify root causes, impact, severity, evidence, and recommended action.", PEACH, ORANGE),
        ("4. AI explanation layer", "AI translates the structured finding into a clear business explanation and confidence statement.", PALE_BLUE, BLUE),
        ("5. Human decision", "An authorized reviewer approves, rejects, or requests more evidence for critical actions.", MINT, TEAL),
    ]
    for index, (title, body, fill, accent) in enumerate(stages):
        flow_box(c, x, y - index * 0.88 * inch, w, h, title, body, fill, accent)
        if index < len(stages) - 1:
            arrow(c, PAGE_W / 2, y - index * 0.88 * inch - h, PAGE_W / 2, y - index * 0.88 * inch - 0.80 * inch)

    box(c, MARGIN, 0.83 * inch, (w - 14) / 2, 0.82 * inch, "AI is not the source of truth", "It cannot invent evidence or replace reconciliation. It receives a structured finding produced from database facts.", fill=PEACH, accent=ORANGE)
    box(c, MARGIN + (w + 14) / 2, 0.83 * inch, (w - 14) / 2, 0.82 * inch, "AI is an explanation layer", "It helps an operations professional understand the issue faster and decide what to do next.", fill=MINT, accent=TEAL)
    footer(c, 2, 5)
    c.showPage()


def page_three(c):
    c.bookmarkPage("ai")
    c.addOutlineEntry("02 / AI layer", "ai", level=0, closed=False)
    heading(c, "02 / AI layer", "What the AI actually does", "The first AI capability is an investigation explanation agent. More agents can be added later, but each must have a narrow responsibility and structured output.")
    cols = [MARGIN, MARGIN + 2.45 * inch, MARGIN + 4.9 * inch]
    titles = ["INPUT", "REASONING", "OUTPUT"]
    bodies = [
        "Investigation ID\nSettlement ID\nDiscrepancy\nRoot causes\nSeverity\nEvidence\nDeterministic recommendation",
        "Summarize the business impact\nExplain each root cause\nConnect claims to evidence\nState uncertainty\nFlag human review",
        "Executive summary\nCause-by-cause explanation\nImpact statement\nConfidence\nReview requirement\nSuggested next step",
    ]
    fills = [PALE_BLUE, PEACH, MINT]
    accents = [BLUE, ORANGE, TEAL]
    for x, title, body, fill, accent in zip(cols, titles, bodies, fills, accents):
        c.setFillColor(fill)
        c.roundRect(x, PAGE_H - 3.05 * inch, 2.15 * inch, 1.35 * inch, 10, fill=1, stroke=0)
        text(c, x + 14, PAGE_H - 1.98 * inch, title, 10, accent, "Helvetica-Bold")
        yy = PAGE_H - 2.24 * inch
        for line in body.split("\n"):
            text(c, x + 14, yy, line, 9, INK)
            yy -= 14
    arrow(c, 2.7 * inch, PAGE_H - 2.38 * inch, 3.05 * inch, PAGE_H - 2.38 * inch)
    arrow(c, 5.15 * inch, PAGE_H - 2.38 * inch, 5.5 * inch, PAGE_H - 2.38 * inch)

    text(c, MARGIN, PAGE_H - 3.55 * inch, "Agent roadmap", 14, NAVY, "Helvetica-Bold")
    agents = [
        ("Explanation agent", "Explains the deterministic finding in plain business language.", TEAL),
        ("Evidence agent", "Organizes supporting records and identifies missing or conflicting evidence.", BLUE),
        ("Policy/RAG agent", "Retrieves relevant operating procedures and control policies.", ORANGE),
        ("Recommendation agent", "Suggests next steps, but never executes a financial correction.", TEAL),
    ]
    y = PAGE_H - 3.9 * inch
    for title, body, accent in agents:
        c.setFillColor(WHITE)
        c.setStrokeColor(LINE)
        c.roundRect(MARGIN, y - 0.42 * inch, PAGE_W - 2 * MARGIN, 0.55 * inch, 7, fill=1, stroke=1)
        c.setFillColor(accent)
        c.circle(MARGIN + 17, y - 0.145 * inch, 5, fill=1, stroke=0)
        text(c, MARGIN + 32, y - 0.12 * inch, title, 10, NAVY, "Helvetica-Bold")
        text(c, MARGIN + 145, y - 0.12 * inch, body, 8.5, INK)
        y -= 0.68 * inch
    box(c, MARGIN, 0.84 * inch, PAGE_W - 2 * MARGIN, 0.75 * inch, "Structured output is mandatory", "The model response must validate against a schema. Free-form text alone is not sufficient for an auditable financial workflow.", fill=PEACH, accent=ORANGE)
    footer(c, 3, 5)
    c.showPage()


def page_four(c):
    c.bookmarkPage("controls")
    c.addOutlineEntry("03 / Guardrails", "controls", level=0, closed=False)
    heading(c, "03 / Guardrails", "What AI cannot do", "FinSight is designed as AI-assisted operations, not autonomous financial mutation.")
    left = MARGIN
    right = PAGE_W / 2 + 0.12 * inch
    box(c, left, PAGE_H - 3.1 * inch, 3.25 * inch, 1.48 * inch, "Allowed", "Explain a stored finding\nSummarize evidence\nCompare evidence with policy\nState confidence and uncertainty\nSuggest a review path", fill=MINT, accent=TEAL)
    box(c, right, PAGE_H - 3.1 * inch, 3.25 * inch, 1.48 * inch, "Blocked", "Change cash amounts\nModify settlement records\nClose an investigation alone\nInvent missing evidence\nBypass permissions or approval", fill=PEACH, accent=ORANGE)

    text(c, MARGIN, PAGE_H - 3.65 * inch, "Control loop", 14, NAVY, "Helvetica-Bold")
    loop = [
        ("Evidence", "Database records are the source of truth."),
        ("AI explanation", "The model interprets only the supplied evidence."),
        ("Human review", "A reviewer approves critical actions."),
        ("Audit trail", "Inputs, output, user, and decision are recorded."),
    ]
    y = PAGE_H - 4.0 * inch
    for i, (title, body) in enumerate(loop):
        c.setFillColor(PALE_BLUE if i % 2 == 0 else MINT)
        c.roundRect(MARGIN, y - 0.47 * inch, PAGE_W - 2 * MARGIN, 0.62 * inch, 7, fill=1, stroke=0)
        text(c, MARGIN + 14, y - 0.08 * inch, title, 10, NAVY, "Helvetica-Bold")
        text(c, MARGIN + 125, y - 0.08 * inch, body, 9, INK)
        if i < len(loop) - 1:
            arrow(c, PAGE_W / 2, y - 0.52 * inch, PAGE_W / 2, y - 0.72 * inch)
        y -= 0.82 * inch
    box(c, MARGIN, 0.85 * inch, PAGE_W - 2 * MARGIN, 0.78 * inch, "Security follows the same boundary", "JWT authentication identifies the caller. Role/permission checks authorize actions. AI output is never a permission bypass.", fill=PALE_BLUE, accent=BLUE)
    footer(c, 4, 5)
    c.showPage()


def page_five(c):
    c.bookmarkPage("roadmap")
    c.addOutlineEntry("04 / Delivery plan", "roadmap", level=0, closed=False)
    heading(c, "04 / Delivery plan", "How we will build it", "Each milestone produces something demonstrable, testable, and safe to explain to stakeholders.")
    milestones = [
        ("NOW", "Explanation agent", "Input: persisted deterministic finding. Output: validated explanation, impact, confidence, and human-review flag.", TEAL),
        ("NEXT", "Audit and traceability", "Record prompt version, evidence IDs, model output, user, timestamp, and approval decision.", BLUE),
        ("THEN", "RAG and policy context", "Retrieve approved procedures and historical cases to ground recommendations in organizational knowledge.", ORANGE),
        ("LATER", "Multi-agent workflow", "Split explanation, evidence, policy, and recommendation responsibilities with explicit handoffs.", TEAL),
    ]
    y = PAGE_H - 1.62 * inch
    for label, title, body, accent in milestones:
        pill(c, MARGIN, y - 0.04 * inch, label, accent, 54)
        text(c, MARGIN + 70, y, title, 12, NAVY, "Helvetica-Bold")
        wrapped(c, MARGIN + 70, y - 19, body, PAGE_W - MARGIN - (MARGIN + 70), 9, 12, INK)
        c.setStrokeColor(LINE)
        c.line(MARGIN, y - 0.72 * inch, PAGE_W - MARGIN, y - 0.72 * inch)
        y -= 0.94 * inch

    text(c, MARGIN, 2.05 * inch, "Discussion notes", 13, NAVY, "Helvetica-Bold")
    text(c, MARGIN, 1.84 * inch, "Use these fields while presenting the idea.", 9, MUTED)
    form = c.acroForm
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.setStrokeColor(LINE)
    c.roundRect(MARGIN, 0.82 * inch, PAGE_W - 2 * MARGIN, 0.78 * inch, 6, fill=1, stroke=1)
    form.textfield(
        name="discussion_notes",
        tooltip="Discussion notes",
        x=MARGIN + 8,
        y=0.90 * inch,
        width=PAGE_W - 2 * MARGIN - 16,
        height=0.62 * inch,
        borderWidth=0,
        fillColor=colors.HexColor("#F8FAFC"),
        textColor=INK,
        fontName="Helvetica",
        fontSize=9,
        fieldFlags="multiline",
    )
    footer(c, 5, 5)
    c.showPage()


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=letter)
    c.setTitle("FinSight AI - AI Architecture Brief")
    c.setAuthor("FinSight AI")
    page_one(c)
    page_two(c)
    page_three(c)
    page_four(c)
    page_five(c)
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    build()
