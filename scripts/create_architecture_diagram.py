from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import TABLOID
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from pathlib import Path

OUT = Path('output/pdf')
OUT.mkdir(parents=True, exist_ok=True)
pdf_path = OUT / 'paper-mill-predictive-decision-support-architecture.pdf'

W, H = TABLOID  # 11 x 17 in portrait
c = canvas.Canvas(str(pdf_path), pagesize=(W, H))
c.setTitle('Paper Mill Predictive Decision Support System Architecture')
c.setAuthor('Grade Change Intelligence System')

BG = HexColor('#f9fafb'); TEXT = HexColor('#111827'); BORDER = HexColor('#d1d5db'); FLOW = HexColor('#374151')
BLUE = HexColor('#dbeafe'); PURPLE = HexColor('#e9d5ff'); YELLOW = HexColor('#fef3c7'); GREEN = HexColor('#dcfce7')

def text_center(value, x, y, font, size, color=TEXT):
    c.setFillColor(color); c.setFont(font, size); c.drawCentredString(x, y, value)

def arrow(x1, y1, x2, y2, head=7):
    c.setStrokeColor(FLOW); c.setFillColor(FLOW); c.setLineWidth(1.3)
    c.line(x1, y1, x2, y2)
    import math
    angle = math.atan2(y2-y1, x2-x1)
    for delta in (2.55, -2.55):
        c.line(x2, y2, x2-head*math.cos(angle+delta), y2-head*math.sin(angle+delta))

def module(x, y, title, lines, fill, width=208, height=63):
    c.setFillColor(fill); c.setStrokeColor(BORDER); c.setLineWidth(1)
    c.roundRect(x-width/2, y-height/2, width, height, 3, fill=1, stroke=1)
    text_center(title.upper(), x, y+13, 'Helvetica-Bold', 11)
    c.setFillColor(TEXT); c.setFont('Helvetica', 8.6)
    for i, line in enumerate(lines):
        c.drawCentredString(x, y-3-i*12, line)

def italic_note(value, x, y, max_width=None):
    c.setFillColor(FLOW); c.setFont('Helvetica-Oblique', 8.3)
    if max_width and stringWidth(value, 'Helvetica-Oblique', 8.3) > max_width:
        words, lines, current = value.split(), [], ''
        for word in words:
            test = (current + ' ' + word).strip()
            if stringWidth(test, 'Helvetica-Oblique', 8.3) <= max_width: current = test
            else: lines.append(current); current = word
        lines.append(current)
        for i, line in enumerate(lines): c.drawCentredString(x, y-i*10, line)
    else: c.drawCentredString(x, y, value)

c.setFillColor(BG); c.rect(0, 0, W, H, fill=1, stroke=0)
text_center('PAPER MILL PREDICTIVE DECISION SUPPORT SYSTEM', W/2, H-44, 'Helvetica-Bold', 17)
text_center('9-MODULE ARCHITECTURE FOR GRADE CHANGE OPERATIONS', W/2, H-61, 'Helvetica', 9, FLOW)
c.setStrokeColor(BORDER); c.setLineWidth(.8); c.line(54, H-73, W-54, H-73)

cx = W/2
# Center stack
module(cx, 1056, '1. Real-Time Process Data', ['Stock flow · steam · moisture · speed'], BLUE)
italic_note('Real-time process measurements continuously feed the prediction pipeline', cx, 1010, 300)
arrow(cx, 1024, cx, 989)
module(cx, 956, '2. Prediction Data Processing & Feature Generation', ['Velocity features · Stock × Steam interactions', 'Historical trajectory features'], PURPLE, 310)
arrow(cx, 924, cx, 889)
module(cx, 856, '3. Prediction Engine (XGBoost)', ['Risk score · basis weight forecast', 'Estimated time to deviation'], YELLOW, 290)

# Branch
split_y = 814; branch_y = 753; lx, rx = 218, W-218
c.setStrokeColor(FLOW); c.setLineWidth(1.3); c.line(cx, 824, cx, split_y); c.line(lx, split_y, rx, split_y)
arrow(lx, split_y, lx, 785); arrow(rx, split_y, rx, 785)
module(lx, branch_y, '4. Historical Evidence Engine', ['Similar transitions · outcomes', 'Safe operating range'], YELLOW)
module(rx, branch_y, '5. Constraint Validation', ['Recipe limits  ✓   Machine limits  ✓', 'Historical safe range  ✓'], YELLOW, 236)
italic_note('Three-layer safety check prevents unsafe recommendations', rx, 704, 245)

# Combine two branches
join_y = 670
c.setStrokeColor(FLOW); c.setLineWidth(1.3); c.line(lx, 721, lx, join_y); c.line(rx, 721, rx, join_y); c.line(lx, join_y, rx, join_y)
arrow(cx, join_y, cx, 635)
module(cx, 602, '6. Recommendation + Confidence', ['Recommended action · confidence score', 'Supporting evidence'], GREEN, 274)
italic_note('Evidence-based recommendations backed by historical data', cx, 554, 290)
arrow(cx, 570, cx, 535)
module(cx, 502, '7. Prediction Explanation (SHAP)', ['Feature contributions · prediction drivers', 'Decision trace'], PURPLE, 274)
arrow(cx, 470, cx, 435)
module(cx, 402, '8. Operator Dashboard', ['Risk indicator · basis weight trend · recommendation panel', 'Evidence card · SHAP · Accept / Reject / Explain'], GREEN, 340)
arrow(cx, 370, cx, 335)
module(cx, 302, '9. Feedback Logging', ['Operator accept / reject · recommendation outcome', 'Actual vs predicted'], GREEN, 300)

# Feedback loop back into historical evidence
c.setStrokeColor(FLOW); c.setLineWidth(1.3)
loop_x = 74
c.line(cx-150, 302, loop_x, 302); c.line(loop_x, 302, loop_x, 753); arrow(loop_x, 753, lx-104, 753)
italic_note('Continuous improvement through operator feedback loop', 165, 515, 180)

# Legend
c.setStrokeColor(BORDER); c.line(54, 170, W-54, 170)
legend = [(BLUE, 'INPUT DATA'), (PURPLE, 'PROCESSING & EXPLANATION'), (YELLOW, 'ML / DECISION'), (GREEN, 'OUTPUT & FEEDBACK')]
start = 107
for i, (color, label) in enumerate(legend):
    x = start + i*150
    c.setFillColor(color); c.setStrokeColor(BORDER); c.rect(x, 142, 16, 11, fill=1, stroke=1)
    c.setFillColor(FLOW); c.setFont('Helvetica', 7.6); c.drawString(x+22, 145, label)
text_center('All flows shown represent mock system interfaces and operator decision support pathways.', cx, 112, 'Helvetica-Oblique', 8, FLOW)
text_center('Grade Change Intelligence System · Architecture Overview', cx, 72, 'Helvetica', 8, FLOW)
c.showPage(); c.save()
print(pdf_path)
