"""Renders the account one-pager as a real, TRACTIAN-branded PDF (blue/slate,
per brand.tractian.com/color) using fpdf2 — no external service, no template
lottery, identical every time. Served by the app and attachable to outreach.
"""
from fpdf import FPDF

# TRACTIAN brand palette (RGB)
NAVY = (23, 37, 84)       # blue-950
BLUE = (37, 99, 235)      # blue-600
BLUE_800 = (30, 64, 175)
SLATE_700 = (51, 65, 85)
SLATE_900 = (15, 23, 42)
SLATE_400 = (148, 163, 184)
SLATE_50 = (248, 250, 252)
SLATE_200 = (226, 232, 240)
LIGHT_BLUE = (199, 210, 254)

_SUBS = {
    "—": "-", "–": "-", "‘": "'", "’": "'",
    "“": '"', "”": '"', "…": "...", "→": "->",
    "≥": ">=", "×": "x", " ": " ",
}


def _ascii(text: str) -> str:
    for k, v in _SUBS.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")


def render_onepager_pdf(account: dict, brief: dict) -> bytes:
    pdf = FPDF(format="letter", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    W = pdf.w
    ML = 16
    CW = W - 2 * ML

    # ---- Masthead band ----
    band_h = 46
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, W, band_h, "F")
    pdf.set_xy(ML, 11)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 5, "TRACTIAN")
    pdf.set_xy(ML, 18)
    pdf.set_font("Helvetica", "B", 20)
    pdf.multi_cell(CW, 8, _ascii(brief["title"]))
    pdf.set_xy(ML, band_h - 9)
    pdf.set_text_color(*LIGHT_BLUE)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(0, 4, _ascii(brief["subtitle"]).upper())

    pdf.set_y(band_h + 8)

    # ---- Body sections ----
    for s in brief["sections"]:
        pdf.set_x(ML)
        pdf.set_text_color(*BLUE_800)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(0, 5, _ascii(s["heading"]).upper())
        pdf.ln(5.5)
        pdf.set_draw_color(*SLATE_200)
        pdf.set_line_width(0.4)
        pdf.line(ML, pdf.get_y(), ML + CW, pdf.get_y())
        pdf.ln(2.5)
        pdf.set_x(ML)
        pdf.set_text_color(*SLATE_700)
        pdf.set_font("Helvetica", "", 10.5)
        pdf.multi_cell(CW, 5.4, _ascii(s["body"]))
        pdf.ln(4)

    # ---- Case study callout ----
    case = brief["case_study"]
    pdf.ln(1)
    box_y = pdf.get_y()
    pdf.set_fill_color(*SLATE_50)
    pdf.set_draw_color(*SLATE_200)
    # measure text height by rendering into a temporary position later; use fixed padding
    pdf.set_x(ML)
    # left accent bar
    quote = f"{case['customer']} {case['result']}."
    # Estimate box height: label + quote lines + link
    pdf.set_font("Helvetica", "", 11)
    # Draw background box after computing height via split_only
    lines = pdf.multi_cell(CW - 12, 5.6, _ascii(quote), split_only=True)
    box_h = 10 + len(lines) * 5.6 + 8
    pdf.set_fill_color(*SLATE_50)
    pdf.rect(ML, box_y, CW, box_h, "F")
    pdf.set_fill_color(*BLUE)
    pdf.rect(ML, box_y, 1.6, box_h, "F")
    pdf.set_xy(ML + 6, box_y + 4)
    pdf.set_text_color(*BLUE_800)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 4, "PROVEN IN YOUR INDUSTRY")
    pdf.set_xy(ML + 6, box_y + 9)
    pdf.set_text_color(*SLATE_900)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(CW - 12, 5.6, _ascii(quote))
    pdf.set_x(ML + 6)
    pdf.set_text_color(*BLUE)
    pdf.set_font("Helvetica", "", 9.5)
    link_label = case["url"].replace("https://", "")
    pdf.cell(0, 5, _ascii(f"Read the {case['customer']} case study: {link_label}"), link=case["url"])
    pdf.set_y(box_y + box_h + 8)

    # ---- Footer ----
    pdf.set_draw_color(*SLATE_200)
    pdf.line(ML, pdf.get_y(), ML + CW, pdf.get_y())
    pdf.ln(3)
    pdf.set_x(ML)
    pdf.set_text_color(*SLATE_700)
    pdf.set_font("Helvetica", "", 10)
    footer = (
        f"Next step: a focused 15-minute call mapping this against a specific asset class at one of "
        f"{account['company_name']}'s sites - your equipment against the platform, no slideshow."
    )
    pdf.multi_cell(CW - 26, 5.2, _ascii(footer))
    pdf.set_xy(ML + CW - 24, pdf.get_y() - 5)
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(24, 5, "TRACTIAN", align="R")

    out = pdf.output()
    return bytes(out)
