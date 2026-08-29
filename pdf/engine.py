"""
PDF Engine — reportlab Platypus, distinct template rendering
Each template varies: fonts, colors, spacing, cover, headers, cards
"""
import os, textwrap, datetime, html
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph as _OrigParagraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image as RLImage, HRFlowable, ListFlowable, ListItem

def _safe_para(text, style, **kwargs):
    # Try original, on paraparser error fallback to escaped text
    try:
        return _OrigParagraph(text, style, **kwargs)
    except Exception as e:
        # Escape and retry stripping problematic tags, keep br
        try:
            # Escape then restore allowed tags
            safe = html.escape(str(text), quote=False)
            # Restore simple allowed tags if they were intended: <b>, </b>, <i>, </i>, <br/>, <br>, &nbsp;
            # Our esc will have escaped them, so we need to unescape our intentional tags? But _safe_para is called with already-escaped content, so we should not double-escape.
            # Instead, try with fully escaped text (no html)
            return _OrigParagraph(safe, style, **kwargs)
        except Exception:
            # Last resort: strip all tags
            import re as _re
            stripped = _re.sub(r'<[^>]+>', '', str(text))
            return _OrigParagraph(html.escape(stripped, quote=False), style, **kwargs)

# Alias Paragraph to safe version for all later uses
Paragraph = _safe_para
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
import io

# Helper to convert hex
def hc(hexstr): return HexColor(hexstr)
def esc(s):
    return html.escape(str(s), quote=False)


# We'll attempt to register nicer fonts if available, else fallback to Helvetica/Times/Courier
# ReportLab built-ins: Helvetica, Helvetica-Bold, Times-Roman, Times-Bold, Courier, Courier-Bold

PAGE_SIZES = {"A4": A4, "Letter": LETTER}

def _add_or_replace(styles, ps: ParagraphStyle):
    if ps.name in styles:
        # update existing style in-place (StyleSheet1 doesn't support __setitem__ in some versions)
        existing = styles[ps.name]
        for k, v in ps.__dict__.items():
            setattr(existing, k, v)
    else:
        styles.add(ps)

def _styles(template):
    colors=template["colors"]
    fonts=template["fonts"]
    spacing=template["spacing"]
    # spacing multipliers
    sp = {"compact":6, "comfortable":10, "airy":14}.get(spacing, 10)
    styles=getSampleStyleSheet()
    # Heading
    _add_or_replace(styles, ParagraphStyle(
        name="CoverTitle",
        parent=styles["Title"],
        fontName=fonts["heading"],
        fontSize=32,
        leading=36,
        textColor=hc(colors["primary"]),
        alignment=TA_LEFT,
        spaceAfter=sp,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="CoverSub",
        parent=styles["Normal"],
        fontName=fonts["body"],
        fontSize=11,
        leading=14,
        textColor=hc(colors["muted"]),
        spaceAfter=sp,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="H1",
        parent=styles["Heading1"],
        fontName=fonts["heading"],
        fontSize=16,
        leading=18,
        textColor=hc(colors["primary"]),
        spaceBefore=sp+4,
        spaceAfter=sp,
        keepWithNext=True,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="H2",
        parent=styles["Heading2"],
        fontName=fonts["heading"],
        fontSize=12,
        leading=14,
        textColor=hc(colors["secondary"] if template["cover_style"]!="terminal" else colors["primary"]),
        spaceBefore=sp,
        spaceAfter=sp-2,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="H3",
        parent=styles["Heading3"],
        fontName=fonts["heading"],
        fontSize=10,
        leading=12,
        textColor=hc(colors["text"]),
        spaceBefore=6,
        spaceAfter=4,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="Body",
        parent=styles["Normal"],
        fontName=fonts["body"],
        fontSize=8.5,
        leading=12,
        textColor=hc(colors["text"]),
        spaceAfter=4,
        alignment=TA_JUSTIFY if template["category"]=="Academic" else TA_LEFT,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="Caption",
        parent=styles["Normal"],
        fontName=fonts["body"],
        fontSize=7,
        leading=9,
        textColor=hc(colors["muted"]),
        spaceAfter=2,
        alignment=TA_LEFT,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="Mono",
        parent=styles["Normal"],
        fontName=fonts["mono"],
        fontSize=7,
        leading=9,
        textColor=hc(colors["text"]),
        backColor=hc(colors["card"]),
        borderPadding=(4,4,6),
        spaceAfter=4,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="Bullet",
        parent=styles["Normal"],
        fontName=fonts["body"],
        fontSize=8.5,
        leading=11,
        textColor=hc(colors["text"]),
        leftIndent=12,
        spaceAfter=2,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="Meta",
        parent=styles["Normal"],
        fontName=fonts["body"],
        fontSize=7,
        leading=9,
        textColor=hc(colors["muted"]),
        alignment=TA_RIGHT if template["id"] in ["executive","corporate"] else TA_LEFT,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="CardTitle",
        parent=styles["Normal"],
        fontName=fonts["heading"],
        fontSize=9,
        leading=11,
        textColor=hc(colors["primary"]),
        spaceAfter=2,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="CardBody",
        parent=styles["Normal"],
        fontName=fonts["body"],
        fontSize=7.5,
        leading=10,
        textColor=hc(colors["text"]),
        spaceAfter=2,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="KPIValue",
        parent=styles["Normal"],
        fontName=fonts["heading"],
        fontSize=18,
        leading=18,
        textColor=hc(colors["primary"]),
        alignment=1,  # center
        spaceAfter=2,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="KPILabel",
        parent=styles["Normal"],
        fontName=fonts["body"],
        fontSize=7,
        leading=8,
        textColor=hc(colors["muted"]),
        alignment=1,
        spaceAfter=0,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="Tag",
        parent=styles["Normal"],
        fontName=fonts["body"],
        fontSize=6,
        leading=7,
        textColor=hc(colors["muted"]),
        backColor=hc(colors["card"]),
        borderPadding=(2,4,4),
        alignment=0,
    ))
    _add_or_replace(styles, ParagraphStyle(
        name="Footer",
        parent=styles["Normal"],
        fontName=fonts["body"],
        fontSize=6,
        leading=7,
        textColor=hc(colors["muted"]),
        alignment=TA_CENTER,
    ))
    return styles

def _cover_background(canvas, doc, template):
    colors = template["colors"]
    w, h = doc.pagesize
    cid = template["id"]
    canvas.saveState()
    try:
        if cid in ["terminal","cyber","neon"]:
            # dark full bleed cover
            canvas.setFillColor(HexColor(colors["bg"]))
            canvas.rect(0, 0, w, h, stroke=0, fill=1)
            # subtle grid
            canvas.setStrokeColor(HexColor(colors["line"]))
            canvas.setLineWidth(0.18)
            step = 22
            for x in range(0, int(w), step):
                canvas.line(x, 0, x, h)
            for y in range(0, int(h), step):
                canvas.line(0, y, w, y)
            # accent corner
            canvas.setFillColor(HexColor(colors["primary"]))
            canvas.setStrokeColor(HexColor(colors["primary"]))
            canvas.rect(w-14, 14, 10, 10, stroke=1, fill=0)
            canvas.rect(w-18, 18, 6, 6, stroke=0, fill=1)
        elif cid in ["corporate","executive"]:
            # top navy bar + gold line
            canvas.setFillColor(HexColor(colors["primary"]))
            canvas.rect(0, h-10, w, 10, stroke=0, fill=1)
            if cid == "corporate":
                canvas.setFillColor(HexColor(colors["secondary"]))
                canvas.rect(0, h-14, w, 4, stroke=0, fill=1)
            # bottom thin line
            canvas.setFillColor(HexColor(colors["line"]))
            canvas.rect(36, 36, w-72, 0.6, stroke=0, fill=1)
        elif cid in ["college","internship","research"]:
            # academic crest placeholder + double rule
            canvas.setStrokeColor(HexColor(colors["primary"]))
            canvas.setLineWidth(0.6)
            canvas.line(36, h-46, w-36, h-46)
            canvas.line(36, h-48, w-36, h-48)
            # subtle watermark circle
            canvas.setStrokeColor(HexColor(colors["line"]))
            canvas.setLineWidth(0.25)
            canvas.circle(w/2, h/2, 90, stroke=1, fill=0)
        elif cid in ["architecture"]:
            # blueprint faint grid already in header, add title block border
            canvas.setStrokeColor(HexColor(colors["primary"]))
            canvas.setLineWidth(0.7)
            canvas.rect(24, 24, w-48, h-48, stroke=1, fill=0)
            canvas.setLineWidth(0.3)
            canvas.rect(26, 26, w-52, h-52, stroke=1, fill=0)
        elif cid in ["glass","modern-portfolio"]:
            # soft gradient simulation via overlapping rects
            canvas.setFillColor(HexColor(colors["bg"]))
            canvas.rect(0,0,w,h, stroke=0, fill=1)
            canvas.setFillColor(HexColor(colors["card"]))
            canvas.setStrokeColor(HexColor(colors["line"]))
            canvas.roundRect(28, h-160, w-56, 120, 12, stroke=1, fill=1)
        elif cid in ["magazine","editorial"]:
            # bold left rule
            canvas.setFillColor(HexColor(colors["primary"]) if cid=="magazine" else HexColor("#DC2626"))
            canvas.rect(0,0,8,h, stroke=0, fill=1)
        elif cid == "chatgpt":
            # ChatGPT light sidebar + main chat area
            # Sidebar
            canvas.setFillColor(HexColor("#F7F7F8"))
            canvas.rect(0, 0, 150, h, stroke=0, fill=1)
            canvas.setStrokeColor(HexColor("#E5E5E5"))
            canvas.setLineWidth(0.4)
            canvas.line(150, 0, 150, h)
            # Sidebar header
            canvas.setFillColor(HexColor("#202123"))
            canvas.setFont("Helvetica-Bold", 6)
            canvas.drawString(14, h-18, "ChatGPT")
            canvas.setFillColor(HexColor("#6E6E80"))
            canvas.setFont("Helvetica", 5)
            canvas.drawString(14, h-28, "History")
            # history items
            canvas.setFont("Helvetica", 5)
            for i, label in enumerate(["Project analysis", "Tech stack", "Architecture", "Security"]):
                y = h-44 - i*14
                canvas.setFillColor(HexColor("#FFFFFF"))
                canvas.roundRect(10, y-4, 130, 10, 2, stroke=0, fill=1)
                canvas.setFillColor(HexColor("#343541"))
                canvas.drawString(14, y, label)
            # main top bar
            canvas.setFillColor(HexColor("#FFFFFF"))
            canvas.setStrokeColor(HexColor("#E5E5E5"))
            canvas.rect(150, h-36, w-150, 36, stroke=1, fill=1)
            canvas.setFillColor(HexColor("#343541"))
            canvas.setFont("Helvetica-Bold", 7)
            canvas.drawCentredString(150 + (w-150)/2, h-22, "ChatGPT  •  Project Documentation")
            canvas.setFillColor(HexColor("#10A37F"))
            canvas.circle(150 + (w-150)/2 - 62, h-22, 3, stroke=0, fill=1)
        elif cid == "timeline":
            # timeline dots line at bottom of cover
            canvas.setStrokeColor(HexColor(colors["primary"]))
            canvas.setLineWidth(1.2)
            y = 88
            canvas.line(48, y, w-48, y)
            for x in [48, w*0.33, w*0.66, w-48]:
                canvas.setFillColor(HexColor(colors["bg"]))
                canvas.circle(x, y, 5, stroke=1, fill=1)
                canvas.setFillColor(HexColor(colors["primary"]))
                canvas.circle(x, y, 2.2, stroke=0, fill=1)
    except:
        pass
    canvas.restoreState()

def _header_footer(canvas, doc, template, project_name):
    canvas.saveState()
    colors=template["colors"]
    w, h = doc.pagesize
    # subtle page background for light templates (keep white, but add faint grid for Architecture)
    if template["id"] == "architecture" and doc.page > 1:
        canvas.setStrokeColor(HexColor("#E0F2FE"))
        canvas.setLineWidth(0.15)
        for x in range(36, int(w-36), 24):
            canvas.line(x, 36, x, h-48)
        for y in range(36, int(h-36), 24):
            canvas.line(36, y, w-36, y)
    if doc.page > 1:
        # header
        canvas.setStrokeColor(hc(colors["line"]))
        canvas.setLineWidth(0.5)
        # style-dependent header
        if template["header_style"] == "mono_line":
            canvas.setStrokeColor(hc(colors["primary"]))
            canvas.setLineWidth(1)
            canvas.line(36, h-36, w-36, h-36)
            canvas.setFont("Courier", 6)
            canvas.setFillColor(hc(colors["muted"]))
            canvas.drawString(36, h-28, f"0xPDFForge  —  {project_name}  —  {template['name'].upper()}")
        elif template["header_style"] in ["neon","glow"]:
            canvas.setStrokeColor(hc(colors["primary"]))
            canvas.setLineWidth(1.2)
            canvas.line(36, h-36, w-36, h-36)
            canvas.setFont("Helvetica-Bold", 6)
            canvas.setFillColor(hc(colors["primary"]))
            canvas.drawString(36, h-28, project_name.upper())
            canvas.setFillColor(hc(colors["muted"]))
            canvas.setFont("Helvetica", 6)
            canvas.drawRightString(w-36, h-28, "CONFIDENTIAL  •  AUTO-GENERATED")
        elif template["header_style"] == "academic":
            canvas.setFont("Times-Roman", 7)
            canvas.setFillColor(hc(colors["muted"]))
            canvas.drawCentredString(w/2, h-28, f"{project_name}  —  Project Documentation  •  {datetime.date.today().isoformat()}")
            canvas.line(36, h-32, w-36, h-32)
        elif template["header_style"] == "chatgpt":
            # ChatGPT minimal header: thin line + centered model name + left project
            canvas.setStrokeColor(HexColor("#E5E5E5"))
            canvas.setLineWidth(0.4)
            canvas.line(36, h-32, w-36, h-32)
            canvas.setFont("Helvetica", 6)
            canvas.setFillColor(HexColor("#6E6E80"))
            canvas.drawString(36, h-26, project_name)
            canvas.setFont("Helvetica-Bold", 6)
            canvas.setFillColor(HexColor("#343541"))
            canvas.drawCentredString(w/2, h-26, "ChatGPT")
            canvas.setFont("Helvetica", 5)
            canvas.setFillColor(HexColor("#10A37F"))
            canvas.drawRightString(w-36, h-26, "GPT-4  •  deterministic")
        elif template["header_style"] == "left_rule":
            canvas.setStrokeColor(hc(colors["primary"]))
            canvas.setLineWidth(2)
            canvas.line(36, h-36, 38, h-36)
            canvas.setFont("Helvetica-Bold", 7)
            canvas.setFillColor(hc(colors["primary"]))
            canvas.drawString(44, h-30, project_name)
        else:
            canvas.setFont(template["fonts"]["body"] if template["fonts"]["body"] in ["Helvetica","Times-Roman","Courier","Helvetica-Bold","Times-Bold","Courier-Bold"] else "Helvetica", 6)
            canvas.setFillColor(hc(colors["muted"]))
            canvas.drawString(36, h-28, f"{project_name}")
            canvas.drawRightString(w-36, h-28, template["name"])

        # footer
        canvas.setFont("Helvetica", 6)
        canvas.setFillColor(hc(colors["muted"]))
        canvas.drawCentredString(w/2, 24, f"—  {doc.page}  —")
        # small line at bottom
        canvas.setStrokeColor(hc(colors["line"]))
        canvas.setLineWidth(0.4)
        canvas.line(36, 32, w-36, 32)
        canvas.setFont("Helvetica", 5)
        canvas.setFont("Helvetica", 5)
        canvas.setFillColor(hc(colors["muted"]))
        canvas.drawString(36, 18, f"0xPDFForge • {template['name']} • deterministic • AI_DISABLED=true • Confidential")
        canvas.drawRightString(w-36, 18, datetime.date.today().strftime("%Y-%m-%d"))
    canvas.restoreState()

def _cover_elements(template, project, styles):
    """Return list of Platypus elements for cover page — style varies heavily per template"""
    colors=template["colors"]
    cid=template["id"]
    els=[]
    data=project
    name=data.get("project_name","0xProject")
    langs=data.get("languages",[])
    fws=data.get("frameworks",[])
    stats=data.get("statistics",{})
    top_lang = langs[0]["language"] if langs else "Mixed"
    primary_fw = fws[0]["name"] if fws else "Custom Stack"

    if cid=="terminal":
        # Dark cover via table background
        els.append(Spacer(1, 30))
        # Big ASCII-ish box
        els.append(Paragraph(f'<font color="{colors["primary"]}">0xPDFForge</font>', styles["Caption"]))
        els.append(Paragraph(f'<font color="{colors["text"]}" size=26><b>{esc(name)}</b></font>', ParagraphStyle("ct2", parent=styles["CoverTitle"], textColor=hc(colors["text"]), fontName="Courier-Bold", fontSize=26, leading=28)))
        els.append(HRFlowable(width="100%", thickness=1, lineCap='square', color=hc(colors["primary"]), spaceAfter=12, spaceBefore=6))
        els.append(Paragraph(f'<font color="{colors["muted"]}">$ analyse --project . --output docs.pdf</font>', styles["Mono"]))
        els.append(Paragraph(f'Project documentation — deterministic static analysis • {len(data.get("flat_files",[]))} files • {stats.get("total_loc",0)} LOC • {top_lang} • {primary_fw}', styles["CoverSub"]))
        els.append(Spacer(1, 18))
        # stats grid mono
        grid_data=[
            [Paragraph(f'<b>Files</b><br/>{stats.get("total_files",0)}', styles["CardBody"]), Paragraph(f'<b>Languages</b><br/>{len(langs)}', styles["CardBody"]), Paragraph(f'<b>Frameworks</b><br/>{len(fws)}', styles["CardBody"])],
            [Paragraph(f'<b>Deps</b><br/>{stats.get("dependencies_count",0)}', styles["CardBody"]), Paragraph(f'<b>LOC</b><br/>{stats.get("total_loc",0)}', styles["CardBody"]), Paragraph(f'<b>Analyzed</b><br/>{data.get("analyzed_at","")[:10]}', styles["CardBody"])],
        ]
        t=Table(grid_data, colWidths=[150,150,150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), hc(colors["card"])),
            ('BOX', (0,0), (-1,-1), 0.5, hc(colors["line"])),
            ('INNERGRID', (0,0), (-1,-1), 0.25, hc(colors["line"])),
            ('LEFTPADDING',(0,0),(-1,-1),8),
            ('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,-1),8),
            ('BOTTOMPADDING',(0,0),(-1,-1),8),
        ]))
        els.append(t)
        els.append(Spacer(1, 20))
        els.append(Paragraph(f'Classification: <b>{data.get("architecture",{}).get("type","generic").upper()}</b>  •  Confidence: deterministic  •  Template: {template["name"]}', styles["Caption"]))

    elif cid=="github":
        els.append(Spacer(1, 14))
        els.append(Paragraph('<font color="#656D76">0xPDFForge  •  Project Documentation</font>', styles["Caption"]))
        els.append(Spacer(1, 8))
        # repo header imitation
        els.append(Paragraph(f'<font color="#24292F" size=28><b>{esc(name)}</b></font> <font color="#656D76">• public</font>', ParagraphStyle("ghtt", parent=styles["CoverTitle"], textColor=hc("#24292F"), fontSize=28, leading=32)))
        els.append(Paragraph(f'<font color="#656D76">{data.get("metadata",{}).get("readme_excerpt","Deterministic analysis of codebase. Static scan, no execution.")[:180]}...</font>', styles["Body"]))
        els.append(Spacer(1, 12))
        # badges row
        badges=[
            Paragraph(f'<font backColor="#0969DA" color="white">  {top_lang}  </font>', styles["Caption"]),
            Paragraph(f'<font backColor="#1F883D" color="white">  {primary_fw}  </font>', styles["Caption"]),
            Paragraph(f'<font backColor="#8250DF" color="white">  {stats.get("total_files",0)} files  </font>', styles["Caption"]),
        ]
        els.append(Table([[b for b in badges]], colWidths=[90,90,90]))
        els.append(Spacer(1, 16))
        els.append(HRFlowable(width="100%", thickness=0.6, color=hc("#D0D7DE"), spaceAfter=12))
        els.append(Paragraph(f'<b>About</b><br/><font color="#656D76">Auto-generated documentation from static analysis. Commit <b>{data.get("analyzed_at","")[:10]}</b> • This PDF was generated locally without AI.</font>', styles["Body"]))
        els.append(Spacer(1, 12))
        els.append(Paragraph(f'<font color="#0969DA">README.md</font>  •  <font color="#0969DA">package.json</font>  •  <font color="#0969DA">{len(fws)} frameworks detected</font>', styles["Caption"]))

    elif cid=="cyber":
        els.append(Spacer(1, 20))
        els.append(Paragraph('<font color="#06FFA5" size=7>▣ 0xPDFForge  //  CYBER EDITION</font>', styles["Caption"]))
        els.append(Paragraph(f'<font color="white" size=30><b>{esc(name.upper())}</b></font>', ParagraphStyle("cybt", parent=styles["CoverTitle"], textColor=white, fontSize=30, leading=32)))
        els.append(Paragraph(f'<font color="#FF00A0">/// PROJECT DOSSIER — {data.get("architecture",{}).get("type","").upper()} ARCHITECTURE</font>', ParagraphStyle("cybs", parent=styles["CoverSub"], textColor=hc("#FF00A0"))))
        els.append(HRFlowable(width="100%", thickness=1.5, color=hc("#06FFA5"), spaceBefore=8, spaceAfter=12))
        els.append(Paragraph(f'<font color="#CBD5E1">Deterministic scan • {stats.get("total_loc",0)} LOC • {len(data.get("frameworks",[]))} frameworks • {top_lang} dominant • Generated {data.get("analyzed_at","")[:10]}</font>', styles["CoverSub"]))
        # neons cards
        row=[
            Paragraph(f'<font color="#06FFA5"><b>{stats.get("total_files",0)}</b></font><br/><font color="#94A3B8">files</font>', styles["CardBody"]),
            Paragraph(f'<font color="#FF00A0"><b>{len(langs)}</b></font><br/><font color="#94A3B8">languages</font>', styles["CardBody"]),
            Paragraph(f'<font color="#06FFA5"><b>{len(fws)}</b></font><br/><font color="#94A3B8">stack</font>', styles["CardBody"]),
        ]
        tt=Table([row], colWidths=[150,150,150])
        tt.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), hc("#0F172A")),
            ('BOX',(0,0),(-1,-1),0.7, hc("#06FFA5")),
            ('INNERGRID',(0,0),(-1,-1),0.4, hc("#1E293B")),
            ('LEFTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
        ]))
        els.append(tt)

    elif cid=="architecture":
        els.append(Spacer(1, 18))
        els.append(Paragraph('<font color="#0284C7">— BLUEPRINT • TECHNICAL DOCUMENTATION —</font>', styles["Caption"]))
        els.append(Paragraph(f'<font color="#0B3D5F" size=28><b>{esc(name)}</b></font>', ParagraphStyle("archt", parent=styles["CoverTitle"], textColor=hc("#0B3D5F"), fontSize=28)))
        els.append(HRFlowable(width="100%", thickness=0.7, color=hc("#38BDF8"), spaceAfter=8))
        els.append(Paragraph(f'<font color="#64748B">Architecture: {data.get("architecture",{}).get("description","")[:160]}</font>', styles["Body"]))
        # grid blueprint fake
        els.append(Spacer(1, 12))
        els.append(Paragraph('<font face="Courier" color="#0284C7" size=6>+—————————————————————————————————————————————+<br/>|   [USER]  →  [FRONTEND]  →  [ API ]  →  [BACKEND]  →  [ DB ]   |<br/>+—————————————————————————————————————————————+</font>', styles["Mono"]))
        els.append(Spacer(1, 12))
        els.append(Paragraph(f'SCALE 1:1 • DWG NO. PDF-{data.get("analyzed_at","")[:10].replace("-","")} • {top_lang} / {primary_fw} • {stats.get("total_files",0)} files', styles["Caption"]))

    elif cid=="minimal-code":
        els.append(Spacer(1, 50))
        els.append(Paragraph(f'<font color="#9CA3AF" size=7>0xPDFForge — Minimal Code</font>', styles["Caption"]))
        els.append(Paragraph(f'<font color="#111111" size=30>{esc(name)}</font>', ParagraphStyle("minit", parent=styles["CoverTitle"], fontName="Helvetica", fontSize=32, textColor=hc("#111111"))))
        els.append(Paragraph(f'<font color="#6B7280">A minimal record of a codebase.<br/>{stats.get("total_loc",0)} lines • {len(langs)} languages • {len(fws)} frameworks</font>', ParagraphStyle("minis", parent=styles["CoverSub"], alignment=TA_LEFT, fontSize=10)))
        els.append(Spacer(1, 24))
        els.append(HRFlowable(width="20%", thickness=1, color=hc("#111111"), hAlign='LEFT', spaceAfter=12))
        els.append(Paragraph(f'{data.get("analyzed_at","")[:10]} &nbsp; • &nbsp; {template["name"]}', styles["Caption"]))

    elif cid=="corporate":
        els.append(Spacer(1, 18))
        els.append(Paragraph('<font color="#C9A86A">0xPDFForge  •  CORPORATE DOSSIER</font>', styles["Caption"]))
        # gold rule
        els.append(HRFlowable(width="100%", thickness=2, color=hc("#C9A86A"), spaceAfter=14))
        els.append(Paragraph(f'<font color="#0F1E3A" size=30><b>{esc(name)}</b></font>', ParagraphStyle("cort", parent=styles["CoverTitle"], textColor=hc("#0F1E3A"), fontSize=30)))
        els.append(Paragraph(f'<font color="#475569"><i>Confidential Project Documentation</i> — Prepared for stakeholders &amp; engineering leadership</font>', styles["CoverSub"]))
        els.append(Spacer(1, 18))
        # executive summary box
        box_data=[[Paragraph(f'<b><font color="#0F1E3A">Executive Summary</font></b><br/><font color="#475569">This document provides a deterministic, evidence-based overview of the {name} codebase. Analysis is static, reproducible, and does not execute project code.</font>', styles["Body"])]]
        bt=Table(box_data, colWidths=[460])
        bt.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), hc("#F8FAFC")),
            ('BOX',(0,0),(-1,-1),0.6, hc("#C9A86A")),
            ('LEFTPADDING',(0,0),(-1,-1),14),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),
        ]))
        els.append(bt)
        els.append(Spacer(1, 12))
        els.append(Paragraph(f'DOCUMENT DATE: {data.get("analyzed_at","")[:10]} &nbsp;&nbsp;|&nbsp;&nbsp; CLASSIFICATION: INTERNAL &nbsp;&nbsp;|&nbsp;&nbsp; VERSION 1.0', styles["Caption"]))

    elif cid=="college":
        els.append(Spacer(1, 10))
        els.append(Paragraph('<font color="#1E3A8A">A PROJECT REPORT</font>', ParagraphStyle("colcap", parent=styles["Caption"], alignment=TA_CENTER, textColor=hc("#1E3A8A"))))
        els.append(Paragraph(f'<font color="#1E3A8A"><b>{esc(name.upper())}</b></font>', ParagraphStyle("colt", parent=styles["CoverTitle"], alignment=TA_CENTER, fontSize=24, textColor=hc("#1E3A8A"))))
        els.append(Paragraph('<font color="#6B7280"><i>Submitted in partial fulfillment of the requirements</i></font>', ParagraphStyle("cols", parent=styles["CoverSub"], alignment=TA_CENTER)))
        els.append(HRFlowable(width="60%", thickness=1, color=hc("#FBBF24"), spaceAfter=12, hAlign='CENTER'))
        els.append(Paragraph(f'<b>Department of Computer Science &amp; Engineering</b><br/>0xPDFForge • Auto-Generated Documentation<br/><br/>Academic Year {datetime.date.today().year}', ParagraphStyle("colb", parent=styles["Body"], alignment=TA_CENTER, fontSize=9)))
        els.append(Spacer(1, 20))
        # info table
        info=[
            [Paragraph('<b>Project Type</b>', styles["Body"]), Paragraph(data.get("architecture",{}).get("type","Software Project").title(), styles["Body"])],
            [Paragraph('<b>Primary Language</b>', styles["Body"]), Paragraph(top_lang, styles["Body"])],
            [Paragraph('<b>Frameworks</b>', styles["Body"]), Paragraph(", ".join([f["name"] for f in fws[:4]]) or "—", styles["Body"])],
            [Paragraph('<b>Date</b>', styles["Body"]), Paragraph(data.get("analyzed_at","")[:10], styles["Body"])],
        ]
        it=Table(info, colWidths=[140,320])
        it.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,-1), hc("#F3F4F6")),
            ('BOX',(0,0),(-1,-1),0.5, hc("#D1D5DB")),
            ('INNERGRID',(0,0),(-1,-1),0.25, hc("#D1D5DB")),
            ('LEFTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ]))
        els.append(it)

    elif cid=="magazine":
        els.append(Spacer(1, 0))
        # huge magazine cover
        els.append(Paragraph('<font color="#DC2626" size=7><b>0xPDFForge</b> — DOCUMENTATION MAGAZINE</font>', styles["Caption"]))
        els.append(Paragraph(f'<font color="#171717" size=42><b>{esc(name.upper())}</b></font>', ParagraphStyle("magt", parent=styles["CoverTitle"], fontSize=42, leading=42, textColor=hc("#171717"))))
        els.append(HRFlowable(width="100%", thickness=3, color=hc("#DC2626"), spaceAfter=10))
        els.append(Paragraph(f'<font color="#52525B" size=11><i>The codebase, decoded. A deterministic audit of {stats.get("total_files",0)} files, {len(langs)} languages, {len(fws)} technologies.</i></font>', ParagraphStyle("mags", parent=styles["Body"], fontSize=11, textColor=hc("#52525B"))))
        els.append(Spacer(1, 14))
        els.append(Paragraph(f'<b>INSIDE:</b> Architecture • Tech Stack • Security • API Map • File Tree  —  <b>{data.get("analyzed_at","")[:10]}</b>  •  #{template["name"].upper()}', styles["Caption"]))

    elif cid=="neon":
        els.append(Spacer(1, 24))
        els.append(Paragraph('<font color="#FF0080">▰▰▰ 0xPDFForge NEON</font>', styles["Caption"]))
        els.append(Paragraph(f'<font color="white" size=30><b>{esc(name)}</b></font>', ParagraphStyle("neont", parent=styles["CoverTitle"], textColor=white, fontSize=30)))
        els.append(Paragraph(f'<font color="#00FFFF"><b>SYNTHWAVE DOCUMENTATION</b> — GLOW EDITION</font>', ParagraphStyle("neons", parent=styles["CoverSub"], textColor=hc("#00FFFF"))))
        els.append(HRFlowable(width="100%", thickness=2, color=hc("#FF0080"), spaceAfter=12))
        els.append(Paragraph(f'<font color="#A1A1AA">{stats.get("total_loc",0)} LINES • {top_lang.upper()} • {primary_fw.upper()} • STATIC ANALYSIS</font>', styles["Caption"]))

    elif cid=="glass":
        els.append(Spacer(1, 16))
        els.append(Paragraph('<font color="#6366F1">◈ 0xPDFForge — Glass</font>', styles["Caption"]))
        els.append(Paragraph(f'<font color="#1E1B4B" size=28><b>{esc(name)}</b></font>', ParagraphStyle("glasst", parent=styles["CoverTitle"], textColor=hc("#1E1B4B"), fontSize=28)))
        els.append(Paragraph(f'<font color="#6B7280">Translucent documentation — light, airy, modern. Project analyzed on {data.get("analyzed_at","")[:10]}</font>', styles["CoverSub"]))
        els.append(Spacer(1, 12))
        # glass cards
        cards=[
            [Paragraph(f'<b>{stats.get("total_files",0)}</b><br/>files', styles["CardBody"]), Paragraph(f'<b>{len(langs)}</b><br/>languages', styles["CardBody"]), Paragraph(f'<b>{len(fws)}</b><br/>frameworks', styles["CardBody"])],
        ]
        ct=Table(cards, colWidths=[150,150,150])
        ct.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), white),
            ('ROUNDEDCORNERS', [4,4,4,4]),
            ('BOX',(0,0),(-1,-1),0.6, hc("#DDD6FE")),
            ('INNERGRID',(0,0),(-1,-1),0.3, hc("#DDD6FE")),
            ('LEFTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
        ]))
        els.append(ct)

    elif cid=="chatgpt":
        # ChatGPT conversational cover — mimics ChatGPT web UI
        els.append(Spacer(1, 18))
        # Top model badge
        els.append(Paragraph('<font color="#6E6E80" size=6>ChatGPT  &nbsp;|&nbsp;  <font color="#10A37F"><b>GPT-4</b></font>  &nbsp;•&nbsp;  Deterministic docs</font>', ParagraphStyle("gptBadge", parent=styles["Caption"], alignment=TA_CENTER, textColor=hc("#6E6E80"))))
        els.append(Spacer(1, 6))
        # Project as user prompt bubble (right-aligned simulation via table)
        # User bubble
        user_bubble = [
            [Paragraph(f'<font color="#343541" size=9><b>{esc(name)}</b></font><br/><font color="#6E6E80" size=6>Analyze this codebase and generate beautiful docs — {stats.get("total_files",0)} files • {top_lang} • {primary_fw}</font>', styles["Body"])]
        ]
        ut = Table(user_bubble, colWidths=[360])
        ut.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), hc("#F7F7F8")),
            ('ROUNDEDCORNERS',[8,8,8,8]),
            ('BOX',(0,0),(-1,-1),0.4, hc("#E5E5E5")),
            ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
        ]))
        # Avatar row: user avatar + bubble
        avatar_user = Table([
            [Paragraph('<font color="#FFFFFF" size=7><b>U</b></font>', ParagraphStyle("avU", parent=styles["Body"], alignment=TA_CENTER, textColor=white)), ut]
        ], colWidths=[28, 360])
        avatar_user.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,0), hc("#5436DA")),
            ('ROUNDEDCORNERS',[6,6,6,6]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),4),
            ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ]))
        els.append(avatar_user)
        els.append(Spacer(1, 8))
        # Assistant response bubble
        ass_text = f'<font color="#343541" size=8>Got it — I analyzed <b>{esc(name)}</b> deterministically. No hallucination, just evidence. Here’s the documentation.</font><br/><br/><font color="#6E6E80" size=7>Architecture: {esc(data.get("architecture",{}).get("type","generic").upper())} • {esc(data.get("architecture",{}).get("description","")[:120])}</font>'
        ass_bubble = [[Paragraph(ass_text, styles["Body"])]]
        at = Table(ass_bubble, colWidths=[360])
        at.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), hc("#FFFFFF")),
            ('ROUNDEDCORNERS',[8,8,8,8]),
            ('BOX',(0,0),(-1,-1),0.4, hc("#E5E5E5")),
            ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
        ]))
        avatar_ass = Table([
            [Paragraph('<font color="#FFFFFF" size=7><b>AI</b></font>', ParagraphStyle("avA", parent=styles["Body"], alignment=TA_CENTER, textColor=white)), at]
        ], colWidths=[28, 360])
        avatar_ass.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,0), hc("#10A37F")),
            ('ROUNDEDCORNERS',[6,6,6,6]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),4),
            ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ]))
        els.append(avatar_ass)
        els.append(Spacer(1, 12))
        # Code block like ChatGPT
        code_lines = f"project: {esc(name)}\nfiles: {stats.get('total_files',0)}  •  loc: {stats.get('total_loc',0)}  •  langs: {len(langs)}  •  frameworks: {len(fws)}"
        els.append(Paragraph(f'<font face="Courier" size=6 color="#ECECF1">{code_lines}</font>', ParagraphStyle("gptCode", parent=styles["Mono"], backColor=hc("#343541"), textColor=hc("#ECECF1"), borderPadding=(8,8,8), fontSize=6, leading=8)))
        els.append(Spacer(1, 8))
        # Action bar like ChatGPT (copy, regenerate)
        els.append(Paragraph('<font color="#6E6E80" size=6>┌  Copy  &nbsp;|&nbsp;  Regenerate  &nbsp;|&nbsp;  Share  &nbsp;&nbsp;  <font color="#10A37F">● Deterministic</font></font>', ParagraphStyle("gptAct", parent=styles["Caption"], alignment=TA_LEFT, leftIndent=32)))
        els.append(Spacer(1, 12))
        els.append(HRFlowable(width="100%", thickness=0.4, color=hc("#E5E5E5"), spaceAfter=8))
        els.append(Paragraph(f'<font color="#6E6E80" size=6>Generated locally by 0xPDFForge  •  ChatGPT style  •  {data.get("analyzed_at","")[:10]}  •  AI_DISABLED=true</font>', ParagraphStyle("gptFoot", parent=styles["Caption"], alignment=TA_CENTER)))
    elif cid=="editorial":
        els.append(Spacer(1, 30))
        els.append(Paragraph(f'<font color="#A16207">— ISSUE 01 • 0xPDFForge EDITORIAL —</font>', styles["Caption"]))
        els.append(Paragraph(f'<font color="#1C1917" size=34><b><i>{esc(name)}</i></b></font>', ParagraphStyle("editt", parent=styles["CoverTitle"], fontName="Times-Bold", textColor=hc("#1C1917"), fontSize=34)))
        els.append(Paragraph(f'<font color="#78716C"><i>An editorial examination of a codebase — through static analysis, not speculation.</i></font>', styles["CoverSub"]))
        els.append(Spacer(1, 12))
        els.append(HRFlowable(width="15%", thickness=1, color=hc("#1C1917"), hAlign='LEFT', spaceAfter=10))
        els.append(Paragraph(f'Words by 0xPDFForge  •  Analysis date {data.get("analyzed_at","")[:10]}  •  {stats.get("total_loc",0)} lines', styles["Caption"]))

    else:
        # generic fallback — elegant centered
        els.append(Spacer(1, 26))
        els.append(Paragraph(f'<font color="{colors["muted"]}">0xPDFForge  •  {template["name"]}  •  {template["category"]}</font>', ParagraphStyle("genCap", parent=styles["Caption"], alignment=TA_CENTER)))
        els.append(Paragraph(f'<font color="{colors["primary"]}"><b>{esc(name)}</b></font>', ParagraphStyle("genT", parent=styles["CoverTitle"], alignment=TA_CENTER, fontSize=28)))
        els.append(HRFlowable(width="30%", thickness=1, color=hc(colors["primary"]), hAlign='CENTER', spaceAfter=10))
        els.append(Paragraph(f'<font color="{colors["muted"]}">{data.get("architecture",{}).get("description","Deterministic project documentation.")[:160]}</font>', ParagraphStyle("genS", parent=styles["CoverSub"], alignment=TA_CENTER)))
        els.append(Spacer(1, 14))
        # stats 3col centered
        sdata=[[Paragraph(f'<b>{stats.get("total_files",0)}</b><br/><font color="{colors["muted"]}">files</font>', ParagraphStyle("gs", parent=styles["CardBody"], alignment=TA_CENTER)),
                Paragraph(f'<b>{len(langs)}</b><br/><font color="{colors["muted"]}">languages</font>', ParagraphStyle("gs2", parent=styles["CardBody"], alignment=TA_CENTER)),
                Paragraph(f'<b>{len(fws)}</b><br/><font color="{colors["muted"]}">frameworks</font>', ParagraphStyle("gs3", parent=styles["CardBody"], alignment=TA_CENTER))]]
        tt=Table(sdata, colWidths=[150,150,150])
        tt.setStyle(TableStyle([
            ('BOX',(0,0),(-1,-1),0.5, hc(colors["line"])),
            ('INNERGRID',(0,0),(-1,-1),0.25, hc(colors["line"])),
            ('BACKGROUND',(0,0),(-1,-1), hc(colors["card"])),
            ('LEFTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
        ]))
        els.append(tt)

    # Methodology box for professional credibility (only for Corporate/College/Research)
    if cid in ["corporate","executive","college","research","internship"]:
        els.append(Spacer(1, 10))
        meth = [
            [Paragraph('<b>Methodology</b><br/><font color="{muted}" size=6>Static scan only — no code execution • Evidence levels: Confirmed (manifest), Detected (import/config), Inferred (pattern) • Redacted secrets • Reproducible locally</font>'.format(muted=colors["muted"]), styles["CardBody"])],
        ]
        mt = Table(meth, colWidths=[460])
        mt.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), hc(colors["card"])),
            ('BOX',(0,0),(-1,-1),0.4, hc(colors["line"])),
            ('LEFTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ]))
        els.append(mt)
    # Common footer for cover
    els.append(Spacer(1, 18))
    els.append(Paragraph(f'<font color="{colors["muted"]}" size=6>Generated locally by 0xPDFForge — deterministic • evidence-based • no hallucination • {data.get("analyzed_at","")[:10]} • AI_DISABLED=true compatible</font>', styles["Caption"]))
    return els

def _section_title(title, subtitle, template, styles):
    els=[]
    colors=template["colors"]
    # distinct header per template
    if template["header_style"]=="mono_line":
        els.append(HRFlowable(width="100%", thickness=1, color=hc(colors["primary"]), spaceBefore=6, spaceAfter=6))
        els.append(Paragraph(f'<font color="{colors["primary"]}"><b>{title.upper()}</b></font> <font color="{colors["muted"]}">— {subtitle}</font>', styles["H1"]))
    elif template["header_style"]=="left_rule":
        # left thick rule
        data=[[Paragraph(f'<font color="{colors["primary"]}" size=14><b>{title}</b></font><br/><font color="{colors["muted"]}" size=7>{subtitle}</font>', styles["Body"])]]
        t=Table(data, colWidths=[470])
        t.setStyle(TableStyle([
            ('LINEBELOW',(0,0),(-1,-1),0.5, hc(colors["line"])),
            ('LINEBEFORE',(0,0),(0,0), 3, hc(colors["primary"])),
            ('LEFTPADDING',(0,0),(-1,-1),10),
            ('BOTTOMPADDING',(0,0),(-1,-1),6),
        ]))
        els.append(t)
        els.append(Spacer(1,6))
    elif template["header_style"]=="academic":
        els.append(Paragraph(f'<font color="{colors["primary"]}"><b>{title}</b></font>', ParagraphStyle("acH1", parent=styles["H1"], alignment=TA_CENTER)))
        els.append(Paragraph(f'<font color="{colors["muted"]}"><i>{subtitle}</i></font>', ParagraphStyle("acSub", parent=styles["Caption"], alignment=TA_CENTER)))
        els.append(HRFlowable(width="20%", thickness=0.6, color=hc(colors["primary"]), hAlign='CENTER', spaceAfter=6))
    elif template["header_style"]=="chatgpt":
        # ChatGPT style: user prompt bubble + assistant label
        # User prompt
        els.append(Spacer(1, 4))
        prompt = [[Paragraph(f'<font color="#343541" size=8><b>{esc(title)}</b></font>  <font color="#6E6E80" size=6>— {esc(subtitle)}</font>', styles["Body"])]]
        pt = Table(prompt, colWidths=[420])
        pt.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), hc("#F7F7F8")),
            ('ROUNDEDCORNERS',[10,10,10,10]),
            ('BOX',(0,0),(-1,-1),0.35, hc("#E5E5E5")),
            ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
        ]))
        # avatar + prompt
        row = Table([
            [Paragraph('<font color="#FFFFFF" size=6><b>U</b></font>', ParagraphStyle("avSecU", parent=styles["Body"], alignment=TA_CENTER, textColor=white)), pt]
        ], colWidths=[26, 430])
        row.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,0), hc("#5436DA")),
            ('ROUNDEDCORNERS',[5,5,5,5]),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),4),
        ]))
        els.append(row)
        els.append(Spacer(1, 6))
        # Assistant header
        els.append(Paragraph('<font color="#10A37F" size=6><b>ChatGPT</b>  •  deterministic  •  evidence-based</font>', ParagraphStyle("assHead", parent=styles["Caption"], leftIndent=32, textColor=hc("#10A37F"))))
        els.append(HRFlowable(width="100%", thickness=0.3, color=hc("#E5E5E5"), spaceBefore=4, spaceAfter=6, hAlign='LEFT'))
    elif template["header_style"]=="oversize":
        els.append(Paragraph(f'<font color="{colors["muted"]}" size=7>{subtitle.upper()}</font>', styles["Caption"]))
        els.append(Paragraph(f'<font color="{colors["primary"]}" size=18><b>{title}</b></font>', ParagraphStyle("overH1", parent=styles["H1"], fontSize=18, leading=20)))
    else:
        els.append(Paragraph(f'<font color="{colors["primary"]}"><b>{title}</b></font>', styles["H1"]))
        if subtitle:
            els.append(Paragraph(f'<font color="{colors["muted"]}">{subtitle}</font>', styles["Caption"]))
        els.append(HRFlowable(width="100%", thickness=0.5, color=hc(colors["line"]), spaceBefore=2, spaceAfter=6))
    return els

def _card_table(cards, template, styles, col_widths=None):
    colors=template["colors"]
    if not col_widths:
        col_widths=[230,230]
    t=Table(cards, colWidths=col_widths, repeatRows=0)
    style=[
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),8),
        ('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),6),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]
    # card backgrounds per template
    for r in range(len(cards)):
        for c in range(len(cards[0])):
            style.append(('BACKGROUND',(c,r),(c,r), hc(colors["card"])))
            style.append(('BOX',(c,r),(c,r),0.4, hc(colors["line"])))
    # alternating rows subtle
    for r in range(len(cards)):
        if r % 2 == 1:
            for c in range(len(cards[0])):
                # slightly darker for odd rows when many rows
                pass
    # rounded for glass/portfolio
    if template["id"] in ["glass","modern-portfolio","neon","terminal","chatgpt"]:
        style.append(('ROUNDEDCORNERS',[4,4,4,4]))
    t.setStyle(TableStyle(style))
    return t

def _styled_table(data, col_widths, template, styles, header=True, caption=None, zebra=True):
    """ChatGPT-style table: header dark, alternating rows, grid, caption"""
    colors = template["colors"]
    # data: list of list of Paragraph/str
    # Ensure header row styled
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),7),
        ('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('BOX',(0,0),(-1,-1),0.5, hc(colors["line"])),
        ('INNERGRID',(0,0),(-1,-1),0.25, hc(colors["line"])),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [white, hc(colors["card"])] if zebra else [white]),
    ]
    if header:
        style += [
            ('BACKGROUND',(0,0),(-1,0), hc(colors["primary"])),
            ('TEXTCOLOR',(0,0),(-1,0), white),
            ('FONTNAME',(0,0),(-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,0), 7),
            ('BOTTOMPADDING',(0,0),(-1,0),6),
        ]
    # rounded corners for glass-like templates
    if template["id"] in ["glass","modern-portfolio","neon","terminal","chatgpt"]:
        style.append(('ROUNDEDCORNERS',[4,4,4,4]))
    t.setStyle(TableStyle(style))
    # Wrap with caption if provided
    if caption:
        cap = Paragraph(f'<font color="{colors["muted"]}" size=6><i>{esc(caption)}</i></font>', styles["Caption"])
        return [t, Spacer(1,2), cap]
    return [t]

def _code_block(code_text, language="text", title=None, template=None, styles=None):
    """ChatGPT-style code block: dark header with language, mono body, line numbers"""
    colors = template["colors"] if template else {"primary":"#0F172A","line":"#E2E8F0","card":"#F8FAFC","muted":"#64748B","bg":"#FFFFFF"}
    # Escape code
    code_esc = esc(code_text).replace(" ", "&nbsp;").replace(chr(10), "<br/>") if code_text else ""
    # Header bar
    header = []
    if title or language:
        header_text = f'<font color="#94A3B8" size=6><b>{esc(title or language)}</b> &nbsp; <font color="#64748B">— copy</font></font>' if title else f'<font color="#94A3B8" size=6>{esc(language)}</font>'
        header = [Paragraph(header_text, ParagraphStyle("codeHead", parent=styles["Caption"], textColor=hc("#94A3B8"), backColor=hc("#0F172A"), borderPadding=(4,6,4), fontName="Courier", fontSize=6, alignment=0))]
    # Body with dark bg, line numbers simulated via table
    lines = code_text.split(chr(10)) if code_text else []
    # Build mono paragraph with dark bg
    body_style = ParagraphStyle("codeBody", parent=styles["Mono"], fontName="Courier", fontSize=6.5, leading=8, textColor=hc("#E2E8F0"), backColor=hc("#0F172A"), borderPadding=(8,8,8), spaceAfter=0)
    # Use simple approach: single Paragraph with <br/> and dark bg
    body = Paragraph(f'<font face="Courier" color="#E2E8F0" size=6>{esc(code_text).replace(chr(10),"<br/>") if code_text else "<i>empty</i>"}</font>', body_style)
    # Wrap in table with header on top
    if header:
        tbl = Table([[header[0]],[body]], colWidths=[460])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), hc("#0F172A")),
            ('BACKGROUND',(0,1),(-1,1), hc("#0F172A")),
            ('BOX',(0,0),(-1,-1),0.5, hc("#1E293B")),
            ('INNERGRID',(0,0),(-1,-1),0.25, hc("#1E293B")),
            ('LEFTPADDING',(0,0),(-1,-1),0),
            ('RIGHTPADDING',(0,0),(-1,-1),0),
            ('TOPPADDING',(0,0),(-1,-1),0),
            ('BOTTOMPADDING',(0,0),(-1,-1),0),
            ('ROUNDEDCORNERS',[4,4,4,4]),
        ]))
        return tbl
    else:
        # Just body
        tbl = Table([[body]], colWidths=[460])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), hc("#0F172A")),
            ('BOX',(0,0),(-1,-1),0.5, hc("#1E293B")),
            ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
        ]))
        return tbl

def _callout(text, kind="note", template=None, styles=None):
    """ChatGPT-style callout: left border color, icon, subtle bg"""
    colors = template["colors"] if template else {"primary":"#0F172A","line":"#E2E8F0","card":"#F8FAFC","muted":"#64748B"}
    palette = {
        "note": ("#0EA5E9","#F0F9FF"),
        "warning": ("#F59E0B","#FFFBEB"),
        "danger": ("#EF4444","#FEF2F2"),
        "success": ("#10B981","#ECFDF5"),
        "info": ("#6366F1","#F5F3FF"),
    }
    border, bg = palette.get(kind, palette["note"])
    # Use table with left border simulation via first column
    inner = Paragraph(f'<font size=7>{esc(text)}</font>', styles["CardBody"])
    tbl = Table([[Paragraph(f'<font color="{border}"><b>●</b></font>', styles["CardBody"]), inner]], colWidths=[18,442])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), hc(bg)),
        ('BOX',(0,0),(-1,-1),0.5, hc(colors["line"])),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LINEBEFORE',(0,0),(0,-1),3, hc(border)),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))
    return tbl

def _image_placeholder(caption, w=460, h=120, template=None, styles=None):
    """Placeholder for image with caption — ChatGPT-style bordered box"""
    colors = template["colors"] if template else {"line":"#E2E8F0","card":"#F8FAFC","muted":"#64748B"}
    # Draw a simple placeholder using Table with centered text
    inner = Paragraph(f'<font color="{colors["muted"]}" size=7><i>[ Image: {esc(caption)} — 1200×600 @2x ]</i><br/><font size=6>┌─────────────────────────┐<br/>│&nbsp;&nbsp;&nbsp;&nbsp;preview unavailable&nbsp;&nbsp;&nbsp;&nbsp;│<br/>└─────────────────────────┘</font></font>', ParagraphStyle("imgCap", parent=styles["Caption"], alignment=1))
    tbl = Table([[inner]], colWidths=[w], rowHeights=[h])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), hc(colors["card"])),
        ('BOX',(0,0),(-1,-1),0.5, hc(colors["line"])),
        ('INNERGRID',(0,0),(-1,-1),0.25, hc(colors["line"])),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
    ]))
    return tbl


def _pie_languages(languages, template):
    if not languages: return None
    d=Drawing(220, 140)
    pie=Pie()
    pie.x=60; pie.y=10; pie.width=110; pie.height=110
    # sort top 5
    top=languages[:5]
    others=sum(l['percentage'] for l in languages[5:]) if len(languages)>5 else 0
    data=[]
    labels=[]
    for l in top:
        data.append(l['percentage'])
        labels.append(l["language"][:10])
    if others>0:
        data.append(others); labels.append("Other")
    pie.data=data
    pie.labels=labels
    pie.slices.strokeWidth=0.6
    pie.slices.strokeColor=white
    # colors palette based on template primary
    palette=[hc(template["colors"]["primary"]), hc(template["colors"]["secondary"]), hc(template["colors"]["accent"]), hc(template["colors"]["muted"]), hc("#94A3B8")]
    for i in range(len(data)):
        pie.slices[i].fillColor=palette[i % len(palette)]
    # label formatting small
    pie.slices.fontSize=6
    pie.slices.fontName='Helvetica'
    pie.slices.strokeWidth=0.8
    d.add(pie)
    return d

def _bar_frameworks(frameworks, template):
    if not frameworks: return None
    d=Drawing(460, 120)
    bc=VerticalBarChart()
    bc.x=30; bc.y=20; bc.width=400; bc.height=80
    # Count by category
    from collections import Counter
    cats=[f["category"] for f in frameworks]
    c=Counter(cats)
    labels=list(c.keys())[:5]
    vals=[c[k] for k in labels]
    bc.data=[vals]
    bc.categoryAxis.categoryNames=labels
    bc.categoryAxis.labels.fontSize=6
    bc.valueAxis.labels.fontSize=6
    bc.bars[0].fillColor=hc(template["colors"]["primary"])
    bc.barLabelFormat='%d'
    bc.bars[0].strokeColor=white
    d.add(bc)
    return d

def generate_pdf(project: dict, template_id: str, sections_config: list, page_size: str="A4", output_path: str=None):
    """
    project: dict (to_dict())
    sections_config: list of {id, title, enabled, content_override?}
    page_size: "A4" or "Letter"
    """
    from templates.definitions import get_template
    template=get_template(template_id)
    styles=_styles(template)
    colors=template["colors"]

    if output_path is None:
        output_path = f"/tmp/{project.get('project_name','project')}.pdf"

    ps = PAGE_SIZES.get(page_size, A4)
    # margins
    doc=SimpleDocTemplate(
        output_path,
        pagesize=ps,
        leftMargin=36, rightMargin=36, topMargin=48, bottomMargin=36,
        title=f"{project.get('project_name')} — Documentation",
        author="0xPDFForge",
        subject="Project Documentation",
        keywords="documentation, pdf, 0xPDFForge",
    )

    story=[]
    # COVER
    story.extend(_cover_elements(template, project, styles))
    story.append(PageBreak())

    # TOC — simple
    story.extend(_section_title("Contents", "Document map — sections rendered from evidence", template, styles))
    toc_items=[]
    for idx, sec in enumerate(sections_config, start=1):
        if not sec.get("enabled", True):
            continue
        toc_items.append(Paragraph(f'<b>{idx:02d}</b> &nbsp; {esc(sec.get("title",""))} <font color="{colors["muted"]}"> — {esc(sec.get("subtitle",""))}</font>', styles["Body"]))
    # two columns? single column for now
    for it in toc_items:
        story.append(it)
        story.append(Spacer(1,2))
    story.append(Spacer(1, 8))
    story.append(Paragraph('<font color="#64748B" size=7><i>Sections omitted where no evidence was found — marked as “No evidence” or hidden per editor settings.</i></font>', styles["Caption"]))
    # Don't break? include break
    story.append(PageBreak())

    # Helper to get section by id
    # Section builders
    def build_executive():
        els=[]
        els.extend(_section_title("Executive Summary", "High-level, evidence-based overview", template, styles))
        arch=project.get("architecture",{})
        langs=project.get("languages",[])
        fws=project.get("frameworks",[])
        stats=project.get("statistics",{})
        # summary paragraph
        summ = f'This document is a deterministic, static analysis of <b>{esc(project.get("project_name"))}</b>. The codebase contains <b>{stats.get("total_files",0)} files</b> across <b>{len(langs)} languages</b>, with <b>{stats.get("total_loc",0)} lines of code</b> and <b>{len(fws)} detected technologies</b>. Primary language is <b>{langs[0]["language"] if langs else "unknown"}</b> ({langs[0]["percentage"] if langs else 0}%). Architecture inferred as <b>{arch.get("type","generic")}</b>: {esc(arch.get("description","No description")[:220])}'
        els.append(Paragraph(summ, styles["Body"]))
        els.append(Spacer(1,8))
        # KPI row - 4 metrics
        kpi_data = [[
            Paragraph(f'<font color="{colors["primary"]}" size=18><b>{stats.get("total_files",0)}</b></font><br/><font color="{colors["muted"]}" size=7>FILES</font>', styles["KPIValue"]),
            Paragraph(f'<font color="{colors["primary"]}" size=18><b>{len(langs)}</b></font><br/><font color="{colors["muted"]}" size=7>LANGUAGES</font>', styles["KPIValue"]),
            Paragraph(f'<font color="{colors["primary"]}" size=18><b>{len(fws)}</b></font><br/><font color="{colors["muted"]}" size=7>FRAMEWORKS</font>', styles["KPIValue"]),
            Paragraph(f'<font color="{colors["primary"]}" size=18><b>{stats.get("total_loc",0)}</b></font><br/><font color="{colors["muted"]}" size=7>LINES OF CODE</font>', styles["KPIValue"]),
        ]]
        kt = Table(kpi_data, colWidths=[115,115,115,115])
        kt.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), hc(colors["card"])),
            ('BOX',(0,0),(-1,-1),0.5, hc(colors["line"])),
            ('INNERGRID',(0,0),(-1,-1),0.3, hc(colors["line"])),
            ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ]))
        els.append(kt)
        els.append(Spacer(1,6))
        # key facts cards
        cards=[]
        cards.append([
            Paragraph(f'<b><font color="{colors["primary"]}">Stack</font></b><br/>{esc(", ".join([f["name"] for f in fws[:5]]) or "No frameworks confirmed")}', styles["CardBody"]),
            Paragraph(f'<b><font color="{colors["primary"]}">Languages</font></b><br/>{esc(", ".join([f"{l['language']} {l['percentage']}%" for l in langs[:4]]) or "—")}', styles["CardBody"]),
        ])
        cards.append([
            Paragraph(f'<b><font color="{colors["primary"]}">Files</font></b><br/>{stats.get("total_files",0)} total • {stats.get("source_files",0)} source • {stats.get("image_count",0)} images', styles["CardBody"]),
            Paragraph(f'<b><font color="{colors["primary"]}">Health</font></b><br/>{len(project.get("security",[]))} security notes • {len(project.get("apis",[]))} API calls • {len(project.get("databases",[]))} DB signals', styles["CardBody"]),
        ])
        els.append(_card_table(cards, template, styles))
        els.append(Spacer(1,6))
        els.append(Paragraph('<b>Confidence model:</b> <font color="#64748B">Confirmed (manifest) • Detected (import/config) • Inferred (heuristic) • Unknown. No claims are made without evidence.</font>', styles["Caption"]))
        return els

    def build_overview():
        els=[]
        els.extend(_section_title("Project Overview", "Name, purpose, and structure at a glance", template, styles))
        meta=project.get("metadata",{})
        els.append(Paragraph(f'<b>Project:</b> {esc(project.get("project_name"))} &nbsp;|&nbsp; <b>Analyzed:</b> {project.get("analyzed_at","")[:10]} &nbsp;|&nbsp; <b>Duration:</b> {project.get("analysis_duration_ms",0)} ms', styles["Caption"]))
        els.append(Spacer(1,4))
        # readme excerpt
        excerpt=meta.get("readme_excerpt","")
        if excerpt:
            els.append(Paragraph('<b>README excerpt (evidence, truncated):</b>', styles["H3"]))
            els.append(_code_block(excerpt[:700], language="markdown", title="README.md", template=template, styles=styles))
        else:
            els.append(Paragraph('<i>No README found — overview derived from file structure and manifests.</i>', styles["Body"]))
        els.append(Spacer(1,6))
        # vital stats
        stats=project.get("statistics",{})
        els.append(Paragraph('<b>Vital statistics</b>', styles["H3"]))
        rows=[
            [Paragraph('<b>Total files</b>', styles["CardBody"]), Paragraph(str(stats.get("total_files",0)), styles["CardBody"]), Paragraph('<b>Source files</b>', styles["CardBody"]), Paragraph(str(stats.get("source_files",0)), styles["CardBody"])],
            [Paragraph('<b>LOC</b>', styles["CardBody"]), Paragraph(str(stats.get("total_loc",0)), styles["CardBody"]), Paragraph('<b>Ignored</b>', styles["CardBody"]), Paragraph(str(stats.get("ignored_files",0)), styles["CardBody"])],
            [Paragraph('<b>Images</b>', styles["CardBody"]), Paragraph(str(stats.get("image_count",0)), styles["CardBody"]), Paragraph('<b>Docs</b>', styles["CardBody"]), Paragraph(str(stats.get("doc_files",0)), styles["CardBody"])],
        ]
        t=Table(rows, colWidths=[100,60,100,60])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), hc(colors["card"])),
            ('BOX',(0,0),(-1,-1),0.4, hc(colors["line"])),
            ('INNERGRID',(0,0),(-1,-1),0.25, hc(colors["line"])),
            ('LEFTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ]))
        els.append(t)
        return els

    def build_goals():
        els=[]
        els.extend(_section_title("Project Goals", "Inferred purpose from code evidence", template, styles))
        features=project.get("features",[])
        arch=project.get("architecture",{})
        # Heuristic goals based on features
        goals=[]
        if any(f["name"]=="Contact Form" for f in features):
            goals.append("Provide a contact/enquiry interface for user communication")
        if any(f["name"]=="Portfolio / Projects" for f in features):
            goals.append("Showcase projects or portfolio items")
        if any(f["name"]=="Authentication UI" for f in features):
            goals.append("Enable user authentication / account management")
        if len(project.get("apis",[]))>0:
            goals.append("Integrate external services and data via APIs")
        if not goals:
            goals.append("Deliver a codebase as analyzed — goals inferred as general software delivery (no explicit feature signals)")
            goals.append(f"Architecture type: {arch.get('type','generic')} — {arch.get('description','')[:100]}")
        for g in goals:
            els.append(Paragraph(f'• {esc(g)}', styles["Bullet"]))
        els.append(Spacer(1,4))
        els.append(Paragraph('<font color="#94A3B8"><i>Goals are inferred from detected features; not claimed as confirmed requirements.</i></font>', styles["Caption"]))
        return els

    def build_stack():
        els=[]
        els.extend(_section_title("Technology Stack", "Evidence-backed frameworks, libraries, and tools", template, styles))
        fws=project.get("frameworks",[])
        langs=project.get("languages",[])
        if not fws:
            els.append(Paragraph('<i>No frameworks confirmed. The project may use vanilla languages or detection found no manifest evidence.</i>', styles["Body"]))
        else:
            # Group by category
            from collections import defaultdict
            by_cat=defaultdict(list)
            for f in fws:
                by_cat[f["category"]].append(f)
            for cat, items in by_cat.items():
                els.append(Paragraph(f'<b>{cat}</b>', styles["H3"]))
                # cards per cat 2col
                rows=[]
                for i in range(0, len(items), 2):
                    row=[]
                    for j in range(2):
                        if i+j < len(items):
                            it=items[i+j]
                            ev=esc(", ".join(it["evidence"][:2])[:90])
                            conf=f'<font color="{colors["muted"]}" size=6>{it["confidence"]} • {ev}</font>'
                            row.append(Paragraph(f'<b>{esc(it["name"])}</b> <font color="{colors["muted"]}" size=6>{it["version"] or ""}</font><br/>{conf}', styles["CardBody"]))
                        else:
                            row.append(Paragraph("", styles["CardBody"]))
                    rows.append(row)
                if rows:
                    els.append(_card_table(rows, template, styles, col_widths=[230,230]))
                    els.append(Spacer(1,4))
        # Languages pie
        if langs:
            els.append(Paragraph('<b>Language distribution (by bytes)</b>', styles["H3"]))
            # table with pie + list
            pie=_pie_languages(langs, template)
            # lang list
            lang_rows=[]
            for l in langs[:6]:
                lang_rows.append(Paragraph(f'<b>{esc(l["language"])}</b> — {l['percentage']}% • {l["files"]} files • {l["loc"]} LOC', styles["CardBody"]))
            if pie:
                # Put pie and list side by side
                # pie is Drawing, need to embed; use Table with Drawing in cell via workaround: we can render Drawing directly, then list after
                els.append(pie)
                els.append(Spacer(1,4))
            for r in lang_rows:
                els.append(r)
                els.append(Spacer(1,1))
        return els

    def build_stats():
        els=[]
        els.extend(_section_title("Project Statistics", "Measured, not invented", template, styles))
        stats=project.get("statistics",{})
        # Big numbers row
        big=[
            Paragraph(f'<font color="{colors["primary"]}" size=16><b>{stats.get("total_files",0)}</b></font><br/><font color="{colors["muted"]}">total files</font>', ParagraphStyle("bigC", parent=styles["CardBody"], alignment=TA_CENTER)),
            Paragraph(f'<font color="{colors["primary"]}" size=16><b>{stats.get("total_loc",0)}</b></font><br/><font color="{colors["muted"]}">lines of code</font>', ParagraphStyle("bigC2", parent=styles["CardBody"], alignment=TA_CENTER)),
            Paragraph(f'<font color="{colors["primary"]}" size=16><b>{stats.get("dependencies_count",0)}</b></font><br/><font color="{colors["muted"]}">dependencies</font>', ParagraphStyle("bigC3", parent=styles["CardBody"], alignment=TA_CENTER)),
        ]
        t=Table([big], colWidths=[150,150,150])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), hc(colors["card"])),
            ('BOX',(0,0),(-1,-1),0.5, hc(colors["line"])),
            ('INNERGRID',(0,0),(-1,-1),0.25, hc(colors["line"])),
            ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
        ]))
        els.append(t)
        els.append(Spacer(1,8))
        # largest files
        lf=stats.get("largest_files",[])[:6]
        if lf:
            els.append(Paragraph('<b>Largest files</b>', styles["H3"]))
            rows=[[Paragraph('<b>File</b>', styles["Caption"]), Paragraph('<b>Size</b>', styles["Caption"])]]
            for f in lf:
                kb=f["size"]/1024
                rows.append([Paragraph(esc(f["path"][:60]), styles["CardBody"]), Paragraph(f'{kb:.1f} KB', styles["CardBody"])])
            els.extend(_styled_table(rows, [380,70], template, styles, header=True, caption=f"Top {len(rows)-1} largest files by size"))
            els.append(Spacer(1,6))
        # build scripts
        bs=stats.get("build_scripts",{})
        if bs:
            els.append(Paragraph('<b>Available scripts (package.json)</b>', styles["H3"]))
            for k,v in list(bs.items())[:8]:
                els.append(Paragraph(f'<b>{k}</b>: <font face="Courier" size=7>{v[:90]}</font>', styles["Bullet"]))
        else:
            els.append(Paragraph('<i>No build scripts detected in package.json.</i>', styles["Caption"]))
        return els

    def build_architecture():
        els=[]
        els.extend(_section_title("Architecture", "Inferred from frameworks, APIs, and data layer", template, styles))
        arch=project.get("architecture",{})
        els.append(Paragraph(arch.get("description","No architecture inferred."), styles["Body"]))
        els.append(Spacer(1,6))
        # Diagram: simple boxes with arrows using Table
        nodes=arch.get("nodes",[])
        edges=arch.get("edges",[])
        if nodes:
            # Render as vertical stack of boxes with arrows
            for idx, n in enumerate(nodes):
                # box
                box=[[Paragraph(f'<b>{n["label"].replace(chr(10),"<br/>")}</b><br/><font color="{colors["muted"]}" size=6>{n["kind"]}</font>', ParagraphStyle(f"arch{idx}", parent=styles["CardBody"], alignment=TA_CENTER))]]
                bt=Table(box, colWidths=[260], rowHeights=[36])
                bt.setStyle(TableStyle([
                    ('BACKGROUND',(0,0),(-1,-1), hc(colors["card"])),
                    ('BOX',(0,0),(-1,-1),0.8, hc(colors["primary"])),
                    ('LEFTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
                    ('ALIGN',(0,0),(-1,-1),'CENTER'),
                    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ]))
                # center
                outer=Table([[bt]], colWidths=[460])
                outer.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),100)]))
                els.append(outer)
                if idx < len(nodes)-1:
                    # arrow
                    edge_label = next((e["label"] for e in edges if e["from"]==n["id"]), "→")
                    els.append(Paragraph(f'<font color="{colors["primary"]}" size=14>↓</font> <font color="{colors["muted"]}" size=6>{edge_label}</font>', ParagraphStyle(f"arr{idx}", parent=styles["Caption"], alignment=TA_CENTER)))
            els.append(Spacer(1,6))
            els.append(Paragraph('<font color="#64748B" size=6><i>Diagram is schematic, derived from detected layers; not a runtime trace.</i></font>', styles["Caption"]))
        # bar chart for frameworks
        if project.get("frameworks"):
            d=_bar_frameworks(project["frameworks"], template)
            if d:
                els.append(Spacer(1,6))
                els.append(Paragraph('<b>Frameworks by category</b>', styles["H3"]))
                els.append(d)
        return els

    def build_structure():
        els=[]
        els.extend(_section_title("Project Structure", "Visual file tree — summarized for large projects", template, styles))
        tree=project.get("file_tree")
        if not tree:
            els.append(Paragraph('<i>File tree unavailable.</i>', styles["Body"]))
            return els
        # Render tree as mono text
        def render_node(node, prefix="", is_last=True, depth=0, out_lines=None):
            if out_lines is None: out_lines=[]
            if depth==0:
                out_lines.append(node["name"]+"/")
            else:
                connector="└── " if is_last else "├── "
                out_lines.append(prefix + connector + node["name"] + ("/" if node["type"]=="dir" else f'  <font color="{colors["muted"]}">({node.get("size",0)//1024}KB)</font>'))
            if node.get("children"):
                new_prefix = prefix + ("    " if is_last else "│   ")
                children=node["children"]
                # limit children display to first 25 per dir?
                show=children[:25]
                for i, child in enumerate(show):
                    render_node(child, new_prefix, i==len(show)-1, depth+1, out_lines)
                if len(children)>25:
                    out_lines.append(new_prefix + f"└── ... +{len(children)-25} more")
            return out_lines
        lines=render_node(tree)
        # limit total lines to ~50
        if len(lines)>55:
            lines=lines[:55] + [f"... +{len(lines)-55} more entries (large project summarized)"]
        tree_text = "\n".join(lines[:55])
        els.append(_code_block(tree_text, language="text", title=tree["name"]+"/", template=template, styles=styles))
        els.append(Spacer(1,4))
        els.append(Paragraph(f'<font color="{colors["muted"]}" size=6>Showing summarized tree of {project.get("statistics",{}).get("total_files",0)} files. Ignored: {project.get("statistics",{}).get("ignored_files",0)} (node_modules, .git, etc.)</font>', styles["Caption"]))
        return els

    def build_features():
        els=[]
        els.extend(_section_title("Features", "UI & functional signals — evidence required", template, styles))
        feats=project.get("features",[])
        details=project.get("metadata",{}).get("website_details",{})
        if not feats:
            els.append(Paragraph('<i>No distinct UI features confirmed. The project may be non-UI or signals were below threshold.</i>', styles["Body"]))
            return els
        # table of features
        rows=[[Paragraph('<b>Feature</b>', styles["Caption"]), Paragraph('<b>Confidence</b>', styles["Caption"]), Paragraph('<b>Evidence</b>', styles["Caption"])]]
        for f in feats[:18]:
            conf_color = {"detected": colors["primary"], "inferred":"#CA8A04", "confirmed":colors["primary"]}.get(f["confidence"], colors["muted"])
            rows.append([
                Paragraph(f'<b>{esc(f["name"])}</b>', styles["CardBody"]),
                Paragraph(f'<font color="{conf_color}">{f["confidence"]}</font>', styles["CardBody"]),
                Paragraph(f'<font size=6>{esc(", ".join(f["evidence"][:2])[:80])}</font>', styles["CardBody"]),
            ])
        t=Table(rows, colWidths=[130,70,250])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), hc(colors["card"])),
            ('BOX',(0,0),(-1,-1),0.4, hc(colors["line"])),
            ('INNERGRID',(0,0),(-1,-1),0.25, hc(colors["line"])),
            ('LEFTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
        ]))
        els.append(t)
        els.append(Spacer(1,6))
        # website details
        if details:
            els.append(Paragraph(f'<b>UI details:</b> {details.get("media_queries",0)} media queries • {details.get("event_listeners",0)} event listeners • {details.get("forms",0)} forms • Responsive: {"Yes" if details.get("has_responsive") else "No evidence"}', styles["Caption"]))
            if details.get("external_resources"):
                els.append(Paragraph(f'<b>External resources:</b> {", ".join(details["external_resources"][:4])[:120]}', styles["Caption"]))
        els.append(Paragraph('<font color="#94A3B8" size=6><i>contact.js alone does not mean contact form — source was inspected before claims.</i></font>', styles["Caption"]))
        return els

    def build_uipreview():
        els=[]
        els.extend(_section_title("UI / Website Preview", "Live preview when runnable, else static analysis", template, styles))
        ss=project.get("screenshots",{})
        if not ss.get("available"):
            els.append(Paragraph(f'<i>{esc(ss.get("message","Live preview unavailable — static project analysis completed."))}</i>', styles["Body"]))
            els.append(Spacer(1,6))
            els.append(_callout("No live server detected — static analysis only. To enable: ensure package.json has start/dev script and project is HTML/Node-runnable.", kind="info", template=template, styles=styles))
            els.append(Spacer(1,6))
            els.append(_image_placeholder("Desktop Homepage — 1440×900", template=template, styles=styles))
            els.append(Spacer(1,4))
            els.append(_image_placeholder("Mobile Viewport — 375×812", template=template, styles=styles))
        else:
            for img in ss.get("images",[]):
                # would embed RLImage if path exists
                pass
        return els

    def build_deps():
        els=[]
        els.extend(_section_title("Dependencies", "Manifests parsed — no hallucination", template, styles))
        deps=project.get("dependencies",[])
        if not deps:
            els.append(Paragraph('<i>No dependencies detected in manifests (package.json, requirements.txt, etc.)</i>', styles["Body"]))
            return els
        # group by source
        from collections import defaultdict
        by_src=defaultdict(list)
        for d in deps:
            by_src[d["source"]].append(d)
        for src, items in by_src.items():
            els.append(Paragraph(f'<b>{src}</b> — {len(items)} packages', styles["H3"]))
            rows=[[Paragraph('<b>Package</b>', styles["Caption"]), Paragraph('<b>Version</b>', styles["Caption"]), Paragraph('<b>Type</b>', styles["Caption"])]]
            for it in items[:20]:
                rows.append([Paragraph(it["name"], styles["CardBody"]), Paragraph(it["version"] or "—", styles["CardBody"]), Paragraph("dev" if it.get("dev") else "prod", styles["CardBody"])])
            tt=Table(rows, colWidths=[250,120,80])
            tt.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0), hc(colors["card"])),
                ('BOX',(0,0),(-1,-1),0.4, hc(colors["line"])),
                ('INNERGRID',(0,0),(-1,-1),0.25, hc(colors["line"])),
                ('LEFTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
            ]))
            els.append(tt)
            els.append(Spacer(1,4))
            if len(items)>20:
                els.append(Paragraph(f'<font color="{colors["muted"]}" size=6>+{len(items)-20} more in {src}</font>', styles["Caption"]))
        return els

    def build_api():
        els=[]
        els.extend(_section_title("API Integration", "Network calls detected via static scan", template, styles))
        apis=project.get("apis",[])
        if not apis:
            els.append(Paragraph('<i>No API calls detected (fetch, axios, XHR). Project may be static or uses unrecognized client.</i>', styles["Body"]))
            return els
        rows=[[Paragraph('<b>Method</b>', styles["Caption"]), Paragraph('<b>Endpoint</b>', styles["Caption"]), Paragraph('<b>Library</b>', styles["Caption"]), Paragraph('<b>File</b>', styles["Caption"])]]
        for a in apis[:16]:
            rows.append([
                Paragraph(f'<b>{esc(a["method"])}</b>', styles["CardBody"]),
                Paragraph(esc(a["endpoint"][:40]), ParagraphStyle("ep", parent=styles["CardBody"], fontSize=6, leading=7, fontName="Courier")),
                Paragraph(esc(a["library"]), styles["CardBody"]),
                Paragraph(f'{esc(a["source_file"])}:{a["line"]}', ParagraphStyle("src", parent=styles["CardBody"], fontSize=6, leading=7)),
            ])
        els.extend(_styled_table(rows, [50,200,60,150], template, styles, header=True, caption="Secrets redacted — endpoints sanitized"))
        els.append(Spacer(1,4))
        els.append(Paragraph('<font color="#94A3B8" size=6><i>Endpoints redacted where sensitive tokens detected. Secrets never appear verbatim.</i></font>', styles["Caption"]))
        return els

    def build_db():
        els=[]
        els.extend(_section_title("Database", "Only when evidence exists", template, styles))
        dbs=project.get("databases",[])
        if not dbs:
            els.append(Paragraph('<i>No database technology confirmed. No connection code, ORM, or schema files produced strong evidence.</i>', styles["Body"]))
            els.append(Paragraph('<font color="#64748B" size=7>Checked: connection code, models, schemas, SQL files, ORM usage.</font>', styles["Caption"]))
            return els
        for db in dbs:
            conf_color = {"confirmed":colors["primary"], "detected":colors["secondary"], "inferred":"#CA8A04"}.get(db["confidence"], colors["muted"])
            els.append(Paragraph(f'<b>{db["technology"]}</b> <font color="{conf_color}" size=7>{db["confidence"].upper()}</font>', styles["H3"]))
            els.append(Paragraph(f'<font color="{colors["muted"]}" size=7>Evidence: {esc(", ".join(db["evidence"][:3]))}</font>', styles["Caption"]))
            if db.get("files"):
                els.append(Paragraph(f'<font size=7>Files: {esc(", ".join(db["files"][:3]))}</font>', styles["Caption"]))
            els.append(Spacer(1,4))
        return els

    def build_security():
        els=[]
        els.extend(_section_title("Security Findings", "Lightweight static scan — not a full audit", template, styles))
        secs=project.get("security",[])
        if not secs:
            els.append(Paragraph('<b>Static scan detected no obvious high-severity patterns.</b>', styles["Body"]))
            els.append(Paragraph('<font color="#64748B"><i>Do not interpret as “secure”. This is a lightweight heuristic scan.</i></font>', styles["Caption"]))
            return els
        for s in secs[:10]:
            kind = {"high":"danger","medium":"warning","low":"info","info":"note"}.get(s["severity"],"note")
            els.append(Paragraph(f'<b>{esc(s["title"])}</b> <font color="{colors["muted"]}" size=6>— {esc(s["severity"].upper())} • {esc(s.get("file",""))}:{esc(s.get("line",""))}</font>', styles["H3"]))
            els.append(_callout(s["description"], kind=kind, template=template, styles=styles))
            if s.get("evidence_snippet"):
                els.append(_code_block(s.get("evidence_snippet","")[:80], language="evidence", title=esc(s.get("file","")), template=template, styles=styles))
            els.append(Spacer(1,4))
        els.append(Paragraph('<font color="#7C2D12"><b>Important:</b> “Static scan detected...” — do not claim the project is fully secure. Secrets are redacted and never appear verbatim in this PDF.</font>', styles["Caption"]))
        return els

    def build_testing():
        els=[]
        els.extend(_section_title("Testing", "Only if evidence exists", template, styles))
        stats=project.get("statistics",{})
        fws=project.get("frameworks",[])
        test_fws=[f for f in fws if f["category"]=="Testing"]
        if stats.get("test_files",0)==0 and not test_fws:
            els.append(Paragraph('<i>No test files or testing frameworks detected. Coverage information unavailable.</i>', styles["Body"]))
            els.append(Paragraph('<font color="#64748B">Looked for: *.test.js, *.spec.js, __tests__, tests/, jest, vitest, playwright, cypress.</font>', styles["Caption"]))
            return els
        els.append(Paragraph(f'<b>Test files:</b> {stats.get("test_files",0)} &nbsp;|&nbsp; <b>Frameworks:</b> {", ".join([f["name"] for f in test_fws]) or "none confirmed"}', styles["Body"]))
        els.append(Spacer(1,4))
        for f in test_fws:
            els.append(Paragraph(f'• <b>{f["name"]}</b> — {", ".join(f["evidence"][:2])}', styles["Bullet"]))
        return els

    def build_setup():
        els=[]
        els.extend(_section_title("Development Setup", "How to run — from manifests", template, styles))
        stats=project.get("statistics",{})
        bs=stats.get("build_scripts",{})
        # detect startup command
        startup=None
        if "dev" in bs: startup="npm run dev"
        elif "start" in bs: startup="npm start"
        elif "serve" in bs: startup="npm run serve"
        if startup:
            els.append(Paragraph(f'<b>Startup command (detected):</b> <font face="Courier" backColor="{colors["card"]}"> {startup} </font>', styles["Body"]))
        else:
            els.append(Paragraph('<i>No startup script confirmed (checked package.json scripts).</i>', styles["Body"]))
        els.append(Spacer(1,4))
        els.append(Paragraph('<b>Steps (evidence-based):</b>', styles["H3"]))
        steps=[]
        if any(d["source"]=="package.json" for d in project.get("dependencies",[])):
            steps.append("Install dependencies: <b>npm install</b> (package.json present)")
        if any(d["source"] in ["requirements.txt","pyproject.toml"] for d in project.get("dependencies",[])):
            steps.append("Python deps: <b>pip install -r requirements.txt</b> or <b>pip install -e .</b>")
        if os.path.basename(project.get("project_name","")).lower()=="":
            pass
        if project.get("metadata",{}).get("has_readme"):
            steps.append("See README.md for project-specific instructions (excerpt on Overview page)")
        if project.get("metadata",{}).get("has_env_example"):
            steps.append("Copy <b>.env.example → .env</b> and fill required values (never commit .env)")
        if not steps:
            steps.append("No package manager manifest found — check file tree for manual setup")
        for s in steps:
            els.append(Paragraph(f'• {s}', styles["Bullet"]))
        els.append(Spacer(1,4))
        if bs:
            els.append(Paragraph('<b>All scripts:</b>', styles["H3"]))
            for k,v in list(bs.items())[:10]:
                els.append(Paragraph(f'<b>{k}</b>: <font face="Courier" size=7>{v}</font>', styles["Bullet"]))
        return els

    def build_usage():
        els=[]
        els.extend(_section_title("Usage", "How the project is used — from code signals", template, styles))
        # Generic usage based on architecture
        arch=project.get("architecture",{})
        if arch.get("type")=="frontend":
            els.append(Paragraph('This is a frontend project. Usage is via browser: open <b>index.html</b> or run the dev server and visit <b>http://localhost:3000</b> (or configured port). No backend required for static preview.', styles["Body"]))
        elif arch.get("type")=="backend":
            els.append(Paragraph('This is a backend/service project. Use via HTTP API (see API Integration section) or CLI entry points detected in source.', styles["Body"]))
        else:
            els.append(Paragraph('Usage derived from project type and entry files. Refer to README and setup steps for exact commands.', styles["Body"]))
        els.append(Spacer(1,4))
        # entry files
        flats=project.get("flat_files",[])
        entries=[f for f in flats if os.path.basename(f).lower() in ["index.html","app.py","main.py","index.js","server.js","app.js"]][:6]
        if entries:
            els.append(Paragraph('<b>Entry files (detected):</b>', styles["H3"]))
            for e in entries:
                els.append(Paragraph(f'• {e}', styles["Bullet"]))
        return els

    def build_limits():
        els=[]
        els.extend(_section_title("Limitations", "Honest, evidence-aware", template, styles))
        lims=[]
        if len(project.get("apis",[]))==0:
            lims.append("No API integration detected — project appears static or uses server-rendered data")
        if len(project.get("databases",[]))==0:
            lims.append("No database layer confirmed — may be stateless or uses external storage without local evidence")
        if project.get("statistics",{}).get("test_files",0)==0:
            lims.append("No tests detected — coverage and regression safety unknown")
        if project.get("screenshots",{}).get("available")==False:
            lims.append("Live preview unavailable — static analysis only (project not runnable in sandbox)")
        if not lims:
            lims.append("Analysis based on static files; runtime behavior may differ. Manual QA recommended.")
        lims.append("All findings are heuristic; false positives/negatives possible. Review source before production decisions.")
        for l in lims:
            els.append(Paragraph(f'• {l}', styles["Bullet"]))
        return els

    def build_future():
        els=[]
        els.extend(_section_title("Future Improvements", "Suggested, not prescribed", template, styles))
        sugg=[]
        if project.get("statistics",{}).get("test_files",0)==0:
            sugg.append("Add automated tests (Jest/Vitest/Playwright) and CI coverage gate")
        if len(project.get("security",[]))>0:
            sugg.append("Address security findings: rotate hard-coded secrets, avoid eval/innerHTML, tighten CORS")
        if not any(f["name"]=="TypeScript" for f in project.get("frameworks",[])) and any(l["language"]=="JavaScript" for l in project.get("languages",[])):
            sugg.append("Consider TypeScript for type safety in larger codebase")
        if len(project.get("databases",[]))>0 and not any(f["name"]=="Prisma" for f in project.get("frameworks",[])):
            sugg.append("Consider typed ORM (Prisma/TypeORM) if relational DB is core")
        if not project.get("metadata",{}).get("has_readme"):
            sugg.append("Add README.md with setup, usage, architecture, and contribution guide")
        if len(sugg)==0:
            sugg.append("Continue modularizing analyzer/scanner pipeline for additional language support")
            sugg.append("Add CI pipeline and semantic versioning for releases")
        for s in sugg:
            els.append(Paragraph(f'• {s}', styles["Bullet"]))
        return els

    def build_conclusion():
        els=[]
        els.extend(_section_title("Conclusion", "Wrap-up", template, styles))
        els.append(Paragraph(f'<b>{project.get("project_name")}</b> was analyzed deterministically on {project.get("analyzed_at","")[:10]}. The resulting documentation reflects <b>evidence, not assumptions</b>. All sections were generated from file contents, manifests, and static patterns — with confidence levels and omitted sections where evidence was insufficient.', styles["Body"]))
        els.append(Spacer(1,6))
        els.append(Paragraph('<b>Next steps:</b> Use the editor to reorder/hide sections, edit text, switch template or page size, then export PDF. Keep analysis separate from presentation — re-analyze after code changes.', styles["Body"]))
        els.append(Spacer(1,10))
        els.append(Paragraph('<font color="#64748B"><i>Built with 0xPDFForge — Turn any codebase into beautiful documentation.</i></font>', styles["Caption"]))
        return els

    builders={
        "cover": None,  # already done
        "executive": build_executive,
        "overview": build_overview,
        "goals": build_goals,
        "stack": build_stack,
        "statistics": build_stats,
        "architecture": build_architecture,
        "structure": build_structure,
        "features": build_features,
        "uipreview": build_uipreview,
        "dependencies": build_deps,
        "api": build_api,
        "database": build_db,
        "security": build_security,
        "testing": build_testing,
        "setup": build_setup,
        "usage": build_usage,
        "limitations": build_limits,
        "future": build_future,
        "conclusion": build_conclusion,
    }

    # Iterate sections_config order
    for sec in sections_config:
        if not sec.get("enabled", True):
            continue
        sid=sec.get("id")
        if sid=="cover":
            continue
        # check content override
        override=sec.get("content_override")
        if override is not None and sid in builders:
            # Use override as custom paragraph instead of builder
            els=[]
            els.extend(_section_title(sec.get("title"), sec.get("subtitle",""), template, styles))
            # split override by \n\n
            for para in override.split("\n\n"):
                if para.strip():
                    els.append(Paragraph(esc(para.strip()).replace("\n","<br/>").replace(chr(10),"<br/>"), styles["Body"]))
                    els.append(Spacer(1,4))
            story.extend(els)
            story.append(Spacer(1,6))
            continue
        builder=builders.get(sid)
        if builder:
            try:
                story.extend(builder())
                story.append(Spacer(1,8))
            except Exception as e:
                story.extend(_section_title(sec.get("title"), "Error rendering — graceful fallback", template, styles))
                story.append(Paragraph(f'<font color="#DC2626">Section failed: {e}</font>', styles["Body"]))
                story.append(Spacer(1,6))
        else:
            # Unknown section, render title + placeholder
            story.extend(_section_title(sec.get("title"), sec.get("subtitle",""), template, styles))
            story.append(Paragraph('<i>No renderer for this section.</i>', styles["Body"]))
            story.append(Spacer(1,6))

    # Build
    def on_page(canvas, doc):
        _header_footer(canvas, doc, template, project.get("project_name",""))
    def on_first(canvas, doc):
        _cover_background(canvas, doc, template)
        _header_footer(canvas, doc, template, project.get("project_name",""))
    doc.build(story, onFirstPage=on_first, onLaterPages=on_page)
    return output_path
