"""
Entourage International — PDF Generator
Converts all 4 markdown files to professional branded PDFs
Brand: Dark (#0A0A0A), White (#FFFFFF), Green (#00C853), Gold (#B8920A)
"""

import re
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# ─── Brand Colors ────────────────────────────────────────────────────────────
BRAND_BLACK   = colors.HexColor('#0A0A0A')
BRAND_DARK    = colors.HexColor('#141414')
BRAND_SURFACE = colors.HexColor('#1C1C1C')
BRAND_GREEN   = colors.HexColor('#00C853')
BRAND_GREEN_D = colors.HexColor('#009624')
BRAND_GOLD    = colors.HexColor('#C9A227')
BRAND_WHITE   = colors.HexColor('#FFFFFF')
BRAND_GRAY1   = colors.HexColor('#E8E8E8')
BRAND_GRAY2   = colors.HexColor('#9E9E9E')
BRAND_GRAY3   = colors.HexColor('#616161')
BRAND_RED     = colors.HexColor('#E53935')
BRAND_ORANGE  = colors.HexColor('#F57C00')
BRAND_YELLOW  = colors.HexColor('#F9A825')
BRAND_BLUE    = colors.HexColor('#1565C0')

PAGE_W, PAGE_H = A4
MARGIN = 22 * mm

# ─── Custom Flowables ────────────────────────────────────────────────────────

class DarkCover(Flowable):
    """Full-bleed dark cover block."""
    def __init__(self, title, subtitle, tag, meta_pairs, width, height):
        super().__init__()
        self.title      = title
        self.subtitle   = subtitle
        self.tag        = tag
        self.meta_pairs = meta_pairs
        self.width      = width
        self.height     = height

    def wrap(self, *args):
        return self.width, self.height

    def draw(self):
        c = self.canv
        w, h = self.width, self.height

        # Background
        c.setFillColor(BRAND_BLACK)
        c.rect(0, 0, w, h, fill=1, stroke=0)

        # Accent corner gradient (simulated with multiple transparent rects)
        for i in range(12):
            alpha = 0.06 - i * 0.005
            radius = 80 + i * 18
            c.setFillColorRGB(0, 0.78, 0.32, alpha)
            c.circle(w - 10*mm, h - 10*mm, radius, fill=1, stroke=0)

        # Bottom line accent
        c.setStrokeColor(BRAND_GREEN)
        c.setLineWidth(2)
        c.line(MARGIN, 28*mm, MARGIN + 40*mm, 28*mm)

        # Tag
        c.setFillColor(BRAND_GREEN)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(MARGIN, h - 28*mm, self.tag.upper())

        # Title
        c.setFillColor(BRAND_WHITE)
        lines = self.title.split('\n')
        y = h - 50*mm
        for line in lines:
            c.setFont('Helvetica-Bold', 34 if len(self.title) < 40 else 28)
            c.drawString(MARGIN, y, line)
            y -= 38

        # Subtitle
        c.setFillColor(BRAND_GRAY2)
        c.setFont('Helvetica', 13)
        c.drawString(MARGIN, y - 10, self.subtitle)

        # Meta row
        x = MARGIN
        y_meta = 40*mm
        c.setFillColor(BRAND_GRAY3)
        c.setFont('Helvetica', 8)
        for label, value in self.meta_pairs:
            c.drawString(x, y_meta + 10, label)
            c.setFillColor(BRAND_GRAY1)
            c.setFont('Helvetica-Bold', 8)
            c.drawString(x, y_meta, value)
            c.setFillColor(BRAND_GRAY3)
            c.setFont('Helvetica', 8)
            x += 52*mm


class SectionDivider(Flowable):
    """Minimal section header with green dot accent."""
    def __init__(self, text, width, color=None):
        super().__init__()
        self.text  = text
        self.width = width
        self.color = color or BRAND_GREEN

    def wrap(self, *args):
        return self.width, 24

    def draw(self):
        c = self.canv
        # Dot
        c.setFillColor(self.color)
        c.circle(5, 10, 4, fill=1, stroke=0)
        # Text
        c.setFillColor(BRAND_BLACK)
        c.setFont('Helvetica-Bold', 14)
        c.drawString(16, 5, self.text)
        # Thin rule
        c.setStrokeColor(colors.HexColor('#E0E0E0'))
        c.setLineWidth(0.5)
        c.line(0, 0, self.width, 0)


class Callout(Flowable):
    """Branded callout / alert box."""
    STYLES = {
        'important': (BRAND_RED,    '#FFF5F5', '⚠'),
        'note':      (BRAND_BLUE,   '#F0F4FF', 'ℹ'),
        'tip':       (BRAND_GREEN,  '#F0FFF4', '→'),
        'warning':   (BRAND_ORANGE, '#FFF8F0', '!'),
    }

    def __init__(self, text, style, width):
        super().__init__()
        self.text   = text
        self.style  = style.lower()
        self.width  = width

    def wrap(self, *args):
        # Estimate height
        words = len(self.text.split())
        lines = max(2, words // 10)
        return self.width, lines * 14 + 24

    def draw(self):
        c = self.canv
        border_col, bg_hex, icon = self.STYLES.get(self.style, self.STYLES['note'])
        bg_col = colors.HexColor(bg_hex)
        _, h = self.wrap()

        c.setFillColor(bg_col)
        c.roundRect(0, 0, self.width, h, 6, fill=1, stroke=0)
        c.setFillColor(border_col)
        c.rect(0, 0, 3, h, fill=1, stroke=0)

        # Icon
        c.setFont('Helvetica-Bold', 12)
        c.drawString(10, h - 18, icon)

        # Text (simple wrapping)
        c.setFont('Helvetica', 9)
        c.setFillColor(BRAND_BLACK)
        max_chars = int(self.width / 5.2)
        words = self.text.split()
        lines = []
        current = ''
        for w in words:
            if len(current) + len(w) + 1 <= max_chars:
                current = (current + ' ' + w).strip()
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)

        y = h - 20
        for line in lines:
            c.drawString(26, y, line)
            y -= 13


class StatBar(Flowable):
    """Horizontal stat pills row."""
    def __init__(self, stats, width):
        super().__init__()
        self.stats = stats   # list of (label, value) tuples
        self.width = width

    def wrap(self, *args):
        return self.width, 36

    def draw(self):
        c = self.canv
        n = len(self.stats)
        pill_w = (self.width - (n - 1) * 8) / n
        x = 0
        for label, value in self.stats:
            c.setFillColor(colors.HexColor('#F5F5F5'))
            c.roundRect(x, 2, pill_w, 30, 6, fill=1, stroke=0)
            c.setStrokeColor(colors.HexColor('#E0E0E0'))
            c.setLineWidth(0.5)
            c.roundRect(x, 2, pill_w, 30, 6, fill=0, stroke=1)
            c.setFillColor(BRAND_BLACK)
            c.setFont('Helvetica-Bold', 11)
            c.drawCentredString(x + pill_w / 2, 20, str(value))
            c.setFillColor(BRAND_GRAY2)
            c.setFont('Helvetica', 7.5)
            c.drawCentredString(x + pill_w / 2, 8, label)
            x += pill_w + 8


# ─── Style Definitions ───────────────────────────────────────────────────────

def get_styles(content_width):
    base = dict(fontName='Helvetica', fontSize=9.5, leading=15,
                textColor=BRAND_BLACK, spaceAfter=6)

    return {
        'body':    ParagraphStyle('body',    **base),
        'body_j':  ParagraphStyle('body_j',  alignment=TA_JUSTIFY, **base),
        'h1':      ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=20,
                                  leading=24, textColor=BRAND_BLACK,
                                  spaceBefore=18, spaceAfter=6),
        'h2':      ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=15,
                                  leading=19, textColor=BRAND_BLACK,
                                  spaceBefore=14, spaceAfter=4),
        'h3':      ParagraphStyle('h3', fontName='Helvetica-Bold', fontSize=12,
                                  leading=16, textColor=BRAND_DARK,
                                  spaceBefore=10, spaceAfter=3),
        'h4':      ParagraphStyle('h4', fontName='Helvetica-Bold', fontSize=9.5,
                                  leading=13, textColor=BRAND_GRAY2,
                                  spaceBefore=8, spaceAfter=2),
        'caption': ParagraphStyle('caption', fontName='Helvetica', fontSize=8,
                                  leading=11, textColor=BRAND_GRAY2),
        'code':    ParagraphStyle('code', fontName='Courier', fontSize=8,
                                  leading=12, textColor=BRAND_DARK,
                                  backColor=colors.HexColor('#F7F7F7'),
                                  leftIndent=10, rightIndent=10,
                                  spaceBefore=4, spaceAfter=4),
        'bullet':  ParagraphStyle('bullet', fontName='Helvetica', fontSize=9.5,
                                  leading=14, textColor=BRAND_BLACK,
                                  leftIndent=14, firstLineIndent=-10,
                                  spaceAfter=3),
        'strong':  ParagraphStyle('strong', fontName='Helvetica-Bold', fontSize=9.5,
                                  leading=14, textColor=BRAND_BLACK),
        'tag':     ParagraphStyle('tag', fontName='Helvetica-Bold', fontSize=7,
                                  textColor=BRAND_GREEN, spaceAfter=2),
        'foot':    ParagraphStyle('foot', fontName='Helvetica', fontSize=7.5,
                                  textColor=BRAND_GRAY2, alignment=TA_CENTER),
    }


# ─── Table Builder ───────────────────────────────────────────────────────────

def build_table(rows, content_width):
    """Build a styled table from 2D list of strings."""
    if not rows:
        return None

    col_count = max(len(r) for r in rows)
    col_width = content_width / col_count

    data = []
    for row in rows:
        data.append([Paragraph(str(c).strip('* '), ParagraphStyle(
            'tc', fontName='Helvetica', fontSize=8.5, leading=12,
            textColor=BRAND_BLACK)) for c in row])

    t = Table(data, colWidths=[col_width] * col_count, repeatRows=1)
    t.setStyle(TableStyle([
        # Header
        ('BACKGROUND',   (0,0), (-1,0), BRAND_BLACK),
        ('TEXTCOLOR',    (0,0), (-1,0), BRAND_WHITE),
        ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,0), 8),
        ('TOPPADDING',   (0,0), (-1,0), 7),
        ('BOTTOMPADDING',(0,0), (-1,0), 7),
        ('LEFTPADDING',  (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        # Body rows
        ('BACKGROUND',   (0,1), (-1,-1), BRAND_WHITE),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [BRAND_WHITE, colors.HexColor('#FAFAFA')]),
        ('FONTNAME',     (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',     (0,1), (-1,-1), 8.5),
        ('TOPPADDING',   (0,1), (-1,-1), 6),
        ('BOTTOMPADDING',(0,1), (-1,-1), 6),
        ('VALIGN',       (0,0), (-1,-1), 'TOP'),
        # Borders
        ('BOX',          (0,0), (-1,-1), 0.5, colors.HexColor('#E0E0E0')),
        ('LINEBELOW',    (0,0), (-1,-1), 0.5, colors.HexColor('#EEEEEE')),
        ('LINEBELOW',    (0,0), (-1,0),  1.0, BRAND_GREEN),
        ('ROUNDEDCORNERS', [4]),
    ]))
    return t


# ─── Markdown → Story Parser ─────────────────────────────────────────────────

def md_inline(text):
    """Convert inline markdown (bold, code, links) to ReportLab markup."""
    # Remove image refs
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Bold+italic
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', text)
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Italic
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<font face="Courier" size="8">\1</font>', text)
    # Escape XML chars (except our tags)
    # We need to be careful - replace & that aren't already entities
    text = re.sub(r'&(?!amp;|lt;|gt;|nbsp;)', '&amp;', text)
    return text.strip()


def parse_md_to_story(md_text, styles, content_width):
    story = []
    lines = md_text.splitlines()
    i = 0
    in_code = False
    code_buf = []
    table_rows = []
    in_table = False

    def flush_table():
        nonlocal in_table, table_rows
        if table_rows:
            # Remove separator row
            clean = [r for r in table_rows if not all(
                re.match(r'^[-:]+$', c.strip()) for c in r)]
            if len(clean) > 1:
                t = build_table(clean, content_width)
                if t:
                    story.append(Spacer(1, 6))
                    story.append(t)
                    story.append(Spacer(1, 8))
        table_rows = []
        in_table = False

    while i < len(lines):
        line = lines[i]

        # Code block
        if line.strip().startswith('```'):
            if in_code:
                in_code = False
                code_text = '\n'.join(code_buf)
                if code_text.strip():
                    story.append(Spacer(1, 4))
                    data = [[Paragraph(
                        '<font face="Courier" size="7.5" color="#333333">' +
                        code_text.replace('&', '&amp;').replace('<', '&lt;')
                              .replace('>', '&gt;').replace('\n', '<br/>') +
                        '</font>',
                        ParagraphStyle('c', leftIndent=8, rightIndent=8,
                                       spaceBefore=4, spaceAfter=4)
                    )]]
                    ct = Table(data, colWidths=[content_width])
                    ct.setStyle(TableStyle([
                        ('BACKGROUND',    (0,0),(0,0), colors.HexColor('#F5F5F5')),
                        ('BOX',           (0,0),(0,0), 0.5, colors.HexColor('#E0E0E0')),
                        ('LEFTPADDING',   (0,0),(0,0), 10),
                        ('RIGHTPADDING',  (0,0),(0,0), 10),
                        ('TOPPADDING',    (0,0),(0,0), 8),
                        ('BOTTOMPADDING', (0,0),(0,0), 8),
                    ]))
                    story.append(ct)
                    story.append(Spacer(1, 6))
                code_buf = []
            else:
                in_code = True
                if in_table:
                    flush_table()
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # Table row
        if line.strip().startswith('|'):
            if not in_table:
                in_table = True
            cols = [c.strip() for c in line.strip().strip('|').split('|')]
            table_rows.append(cols)
            i += 1
            continue
        elif in_table:
            flush_table()

        # Skip HTML image tags
        if line.strip().startswith('![') or line.strip().startswith('<img'):
            i += 1
            continue

        # Headings
        m = re.match(r'^(#{1,4})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            text = md_inline(m.group(2))
            if level == 1:
                story.append(Spacer(1, 8))
                story.append(Paragraph(text, styles['h1']))
            elif level == 2:
                story.append(Spacer(1, 12))
                story.append(SectionDivider(re.sub('<.*?>', '', text), content_width))
                story.append(Spacer(1, 6))
            elif level == 3:
                story.append(Spacer(1, 6))
                story.append(Paragraph(text, styles['h3']))
            else:
                story.append(Paragraph(text.upper(), styles['h4']))
            i += 1
            continue

        # Callout / alert blocks [!TYPE]
        m = re.match(r'^>\s*\[!(IMPORTANT|NOTE|TIP|WARNING)\]', line, re.IGNORECASE)
        if m:
            ctype = m.group(1).lower()
            texts = []
            i += 1
            while i < len(lines) and lines[i].startswith('>'):
                texts.append(lines[i].lstrip('> ').strip())
                i += 1
            callout_text = ' '.join(texts)
            callout_text = re.sub(r'\*\*(.*?)\*\*', r'\1', callout_text)
            callout_text = re.sub(r'`(.*?)`', r'\1', callout_text)
            story.append(Spacer(1, 6))
            story.append(Callout(callout_text, ctype, content_width))
            story.append(Spacer(1, 8))
            continue

        # Blockquote (non-alert)
        if line.startswith('>'):
            text = md_inline(line.lstrip('> ').strip())
            if text:
                data = [[Paragraph(f'<i>{text}</i>',
                    ParagraphStyle('bq', fontName='Helvetica', fontSize=9,
                                   textColor=BRAND_GRAY3, leftIndent=4))]]
                qt = Table(data, colWidths=[content_width])
                qt.setStyle(TableStyle([
                    ('LEFTPADDING',  (0,0),(0,0), 12),
                    ('TOPPADDING',   (0,0),(0,0), 6),
                    ('BOTTOMPADDING',(0,0),(0,0), 6),
                    ('LINEAFTER',    (0,0),(0,0), 0, BRAND_WHITE),
                    ('LINEBEFORE',   (0,0),(0,0), 2.5, BRAND_GREEN),
                    ('BACKGROUND',   (0,0),(0,0), colors.HexColor('#F9F9F9')),
                ]))
                story.append(qt)
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^---+$', line.strip()):
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width=content_width, thickness=0.5,
                                    color=colors.HexColor('#E0E0E0')))
            story.append(Spacer(1, 8))
            i += 1
            continue

        # Bullet/checkbox
        m = re.match(r'^(\s*)([-*+]|\d+\.|\[ \]|\[x\])\s+(.*)', line)
        if m:
            prefix = m.group(2)
            text   = md_inline(m.group(3))
            if prefix in ('[ ]', '[x]'):
                bullet_char = '☐ ' if prefix == '[ ]' else '☑ '
            elif re.match(r'\d+\.', prefix):
                bullet_char = prefix + ' '
            else:
                bullet_char = '• '
            story.append(Paragraph(f'{bullet_char}{text}', styles['bullet']))
            i += 1
            continue

        # Arrow lines (→)
        if line.strip().startswith('→'):
            text = md_inline(line.strip())
            story.append(Paragraph(
                f'<font color="#00C853">→</font> {text[1:].strip()}',
                ParagraphStyle('arr', fontName='Helvetica', fontSize=9,
                               leading=13, textColor=BRAND_BLACK,
                               leftIndent=14, spaceAfter=2)))
            i += 1
            continue

        # Paragraph
        if line.strip():
            text = md_inline(line.strip())
            story.append(Paragraph(text, styles['body']))
        else:
            story.append(Spacer(1, 5))

        i += 1

    if in_table:
        flush_table()

    return story


# ─── Page Template ───────────────────────────────────────────────────────────

def make_header_footer(doc_title, doc_subtitle=''):
    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BRAND_BLACK)
        canvas.rect(0, PAGE_H - 12*mm, PAGE_W, 12*mm, fill=1, stroke=0)

        canvas.setFillColor(BRAND_GREEN)
        canvas.setFont('Helvetica-Bold', 7)
        canvas.drawString(MARGIN, PAGE_H - 7.5*mm, 'ENTOURAGE INTERNATIONAL')

        canvas.setFillColor(BRAND_GRAY2)
        canvas.setFont('Helvetica', 7)
        canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 7.5*mm, doc_title.upper())

        # Footer
        canvas.setFillColor(colors.HexColor('#F5F5F5'))
        canvas.rect(0, 0, PAGE_W, 9*mm, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor('#E0E0E0'))
        canvas.setLineWidth(0.5)
        canvas.line(0, 9*mm, PAGE_W, 9*mm)

        canvas.setFillColor(BRAND_GRAY3)
        canvas.setFont('Helvetica', 7)
        canvas.drawString(MARGIN, 3.5*mm, 'Confidential · Prepared by Antigravity · April 2026')
        canvas.drawRightString(PAGE_W - MARGIN, 3.5*mm, f'Page {doc.page}')

        canvas.restoreState()
    return on_page


# ─── Document Builder ────────────────────────────────────────────────────────

def build_pdf(md_file, pdf_file, cover_data):
    print(f'  Building: {pdf_file}')
    with open(md_file, encoding='utf-8') as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=18*mm, bottomMargin=14*mm,
        title=cover_data['title'],
        author='Antigravity',
        subject='Entourage International',
        creator='Antigravity PDF Engine',
    )

    content_width = PAGE_W - 2 * MARGIN
    styles = get_styles(content_width)

    # Page callback
    on_page = make_header_footer(cover_data['title'], cover_data.get('subtitle', ''))

    story = []

    # Cover
    story.append(DarkCover(
        title=cover_data['title'],
        subtitle=cover_data.get('subtitle', ''),
        tag=cover_data.get('tag', 'Entourage International'),
        meta_pairs=cover_data.get('meta', []),
        width=content_width,
        height=180*mm,
    ))
    story.append(Spacer(1, 20))

    # Stats row if provided
    if cover_data.get('stats'):
        story.append(StatBar(cover_data['stats'], content_width))
        story.append(Spacer(1, 16))

    story.append(HRFlowable(width=content_width, thickness=1, color=BRAND_GREEN))
    story.append(Spacer(1, 16))

    # Parse markdown body
    body = parse_md_to_story(md_text, styles, content_width)
    story.extend(body)

    # Build
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'  ✓ Done: {pdf_file}')


# ─── Main ─────────────────────────────────────────────────────────────────────

BASE = r'c:\Users\unrea\Desktop\malak 2'
OUT  = os.path.join(BASE, 'output')
os.makedirs(OUT, exist_ok=True)

docs = [
    {
        'md':  os.path.join(BASE, 'entourage_3month_strategy.md'),
        'pdf': os.path.join(OUT, '01_3month_strategy.pdf'),
        'cover': {
            'title':    '3-Month Social\nMedia Strategy',
            'subtitle': 'May – July 2026 | Paid Ads · Production · Agentic Workflows',
            'tag':      'Confidential Strategy Document',
            'meta': [
                ('Prepared by', 'Antigravity'),
                ('Period',      'May – July 2026'),
                ('Version',     '1.0'),
                ('Client',      'Entourage International'),
            ],
            'stats': [
                ('Total Ad Budget', '$5,000'),
                ('Platforms', '6 Channels'),
                ('Monthly Posts', '15+'),
                ('Agentic Workflows', '6 Systems'),
            ],
        },
    },
    {
        'md':  os.path.join(BASE, 'entourage_competitive_audit.md'),
        'pdf': os.path.join(OUT, '02_competitive_audit.pdf'),
        'cover': {
            'title':    'Competitive Social\nMedia Audit',
            'subtitle': 'Entourage International vs. Top GCC Marketing Agencies',
            'tag':      'Market Intelligence Report',
            'meta': [
                ('Prepared by', 'Antigravity'),
                ('Date',        'April 2026'),
                ('Scope',       'GCC Agencies'),
                ('Version',     '1.0'),
            ],
            'stats': [
                ('Current LI Followers', '27,958'),
                ('Current IG Followers', '5,399'),
                ('Missing Platforms', '2 Critical'),
                ('Competitors Analysed', '5 Agencies'),
            ],
        },
    },
    {
        'md':  os.path.join(BASE, 'entourage_sample_posts.md'),
        'pdf': os.path.join(OUT, '03_sample_posts.pdf'),
        'cover': {
            'title':    'Sample Post Pack',
            'subtitle': 'Production-Ready Content | 6 Posts Across All Platforms',
            'tag':      'Content Production Pack',
            'meta': [
                ('Prepared by', 'Antigravity'),
                ('Launch Week', 'May 2026'),
                ('Posts Ready', '6 Posts'),
                ('Platforms',   'LI · IG · TK · SC'),
            ],
            'stats': [
                ('Total Posts', '6 Ready'),
                ('Est. Reach', '87K–224K'),
                ('Boost Budget', '$700'),
                ('Platforms', '4 Active'),
            ],
        },
    },
    {
        'md':  os.path.join(BASE, 'gcc_agency_social_media_analysis.md'),
        'pdf': os.path.join(OUT, '04_gcc_agency_analysis.pdf'),
        'cover': {
            'title':    'GCC Agency Social\nMedia Analysis',
            'subtitle': 'Top 5 Agencies · Tactics · Reach Formula · Platform Intelligence',
            'tag':      'Competitive Intelligence',
            'meta': [
                ('Prepared by', 'Antigravity'),
                ('Date',        'April 2026'),
                ('Data source', 'Campaign ME · Qoruz · P&S Intelligence'),
                ('Market Size', '$315.5M (2025)'),
            ],
            'stats': [
                ('GCC Market Size', '$315.5M'),
                ('CAGR', '13.9%'),
                ('UAE Penetration', '115%'),
                ('KSA Market Share', '40%'),
            ],
        },
    },
]

print('\n🖨️  Entourage PDF Generator — Starting...\n')
for d in docs:
    build_pdf(d['md'], d['pdf'], d['cover'])

print(f'\n✅  All 4 PDFs saved to: {OUT}\n')
