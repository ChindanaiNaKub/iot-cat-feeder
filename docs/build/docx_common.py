"""Shared docx helpers so the three reports share one visual style.

Style is copied from the ParkPilot reports in Documents/Final_Progress/build:
A4, 2.2 cm side margins, Times New Roman 11 pt, 1.15 line spacing, blue headings.
"""

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

BODY_FONT = "Times New Roman"
ACCENT = RGBColor(0x4F, 0x81, 0xBD)
INK = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x5A, 0x5A, 0x5A)
HEADER_FILL = "DCE6F2"

HEADINGS = []

# Set by the caller. A consolidated volume shifts chapter numbers up and renames
# appendices so three reports can share one numbering sequence.
CHAPTER_SHIFT = 0
APPENDIX_LETTER = "A"

# A part opener already forced a page break, so the chapter that follows it must not.
_NO_BREAK_NEXT = False


def sec(number):
    """Shift a section number like "2.10" by the current chapter shift."""
    if CHAPTER_SHIFT == 0:
        return number
    head, _, tail = number.partition(".")
    return str(int(head) + CHAPTER_SHIFT) + (("." + tail) if tail else "")


def _fonts(style, name=BODY_FONT):
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), name)


def new_document(title, subtitle):
    doc = Document()

    normal = doc.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(11)
    normal.font.color.rgb = INK
    _fonts(normal)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(6)

    specs = {
        "Heading 1": (16, True, Pt(0), Pt(14)),
        "Heading 2": (13, True, Pt(14), Pt(6)),
        "Heading 3": (11.5, True, Pt(10), Pt(4)),
    }
    for name, (size, bold, before, after) in specs.items():
        style = doc.styles[name]
        style.font.name = BODY_FONT
        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.color.rgb = ACCENT
        style.font.italic = False
        _fonts(style)
        style.paragraph_format.space_before = before
        style.paragraph_format.space_after = after
        style.paragraph_format.keep_with_next = True
    doc.styles["Heading 1"].paragraph_format.page_break_before = True

    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.different_first_page_header_footer = True

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run(title + "  |  ")
    run.font.size = Pt(8.5)
    run.font.color.rgb = MUTED
    _page_field(footer)

    doc.core_properties.title = title
    doc.core_properties.subject = subtitle
    doc.core_properties.author = "Chindanai Jaiman"
    return doc


def _page_field(paragraph):
    run = paragraph.add_run()
    run.font.size = Pt(8.5)
    run.font.color.rgb = MUTED
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)


def cover(doc, report_type, project, tagline, member, student_id, programme, college, month, advisor):
    for _ in range(3):
        doc.add_paragraph()
    _centered(doc, project, size=26, bold=True, space_after=6)
    _centered(doc, tagline, size=12.5, color=MUTED, space_after=48)
    _centered(doc, report_type, size=17, bold=True, color=ACCENT, space_after=60)

    _centered(doc, member + "  " + student_id, size=12, space_after=2)
    _centered(doc, programme, size=12, color=MUTED, space_after=2)
    _centered(doc, college, size=12, color=MUTED, space_after=36)
    _centered(doc, month, size=12, space_after=72)
    _centered(doc, "Project Advisor", size=11, color=MUTED, space_after=2)
    _centered(doc, advisor, size=12, bold=True)

    doc.add_page_break()


def _centered(doc, text, size=11, bold=False, color=INK, space_after=0):
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_after = Pt(space_after)
    run = par.add_run(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return par


def table_of_contents(doc, heading="Table of Contents", entries=None):
    par = doc.add_paragraph()
    par.paragraph_format.space_after = Pt(12)
    run = par.add_run(heading)
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = ACCENT

    if entries:
        for level, text, page in entries:
            line = doc.add_paragraph()
            line.paragraph_format.space_after = Pt(2)
            line.paragraph_format.left_indent = Cm(0.6 * (level - 1))
            line.paragraph_format.tab_stops.add_tab_stop(
                Cm(16.6), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            run = line.add_run(text)
            run.font.size = Pt(10.5 if level > 1 else 11)
            run.font.bold = level == 1
            run = line.add_run("\t" + str(page))
            run.font.size = Pt(10.5 if level > 1 else 11)
            run.font.bold = level == 1
        doc.add_page_break()
        return

    par = doc.add_paragraph()
    run = par.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Select the table, then update the field to build the contents."
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, separate, placeholder, end):
        run._r.append(el)
    doc.add_page_break()


def h1(doc, number, title):
    global _NO_BREAK_NEXT
    if isinstance(number, str) and number.isalpha():
        text = f"Appendix {APPENDIX_LETTER}  {title}"
    else:
        text = f"Chapter {int(number) + CHAPTER_SHIFT}  {title}"
    HEADINGS.append((1, text))
    heading = doc.add_heading(text, level=1)
    if _NO_BREAK_NEXT:
        heading.paragraph_format.page_break_before = False
        _NO_BREAK_NEXT = False
    return heading


def h2(doc, number, title):
    text = f"{sec(number)}  {title}"
    HEADINGS.append((2, text))
    return doc.add_heading(text, level=2)


def h3(doc, number, title):
    text = f"{sec(number)}  {title}"
    return doc.add_heading(text, level=3)


def part(doc, label, title, blurb=""):
    global _NO_BREAK_NEXT
    text = f"{label}  {title}"
    HEADINGS.append((1, text))
    par = doc.add_heading(text, level=1)
    _NO_BREAK_NEXT = True
    if blurb:
        note = doc.add_paragraph()
        note.paragraph_format.space_before = Pt(10)
        run = note.add_run(blurb)
        run.font.size = Pt(11)
        run.font.italic = True
        run.font.color.rgb = MUTED
    return par


def para(doc, text, size=11, italic=False, align="justify", space_after=6):
    par = doc.add_paragraph()
    if align == "justify":
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align == "center":
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_after = Pt(space_after)
    _rich(par, text, size=size, italic=italic)
    return par


def _rich(par, text, size=11, italic=False):
    """Render `monospace` and **bold** spans without a run per word."""
    for index, chunk in enumerate(text.split("`")):
        if not chunk:
            continue
        if index % 2:
            run = par.add_run(chunk)
            run.font.name = "Consolas"
            run.font.size = Pt(size - 1)
            run.font.italic = italic
            continue
        for bold_index, piece in enumerate(chunk.split("**")):
            if not piece:
                continue
            run = par.add_run(piece)
            run.font.size = Pt(size)
            run.font.italic = italic
            run.font.bold = bold_index % 2 == 1


def bullets(doc, items, size=11):
    for item in items:
        par = doc.add_paragraph(style="List Bullet")
        par.paragraph_format.space_after = Pt(2)
        par.paragraph_format.line_spacing = 1.15
        _rich(par, item, size=size)


def numbered(doc, items, size=11):
    for index, item in enumerate(items, 1):
        par = doc.add_paragraph()
        par.paragraph_format.left_indent = Cm(0.8)
        par.paragraph_format.first_line_indent = Cm(-0.8)
        par.paragraph_format.space_after = Pt(3)
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = par.add_run(f"{index}.  ")
        run.font.size = Pt(size)
        _rich(par, item, size=size)


class Numbering:
    def __init__(self):
        self.table = 0
        self.figure = 0

    def next_table(self):
        self.table += 1
        return self.table

    def next_figure(self):
        self.figure += 1
        return self.figure


def table(doc, counter, caption, headers, rows, widths=None, size=9.5, caption_above=True):
    number = counter.next_table()
    if caption_above:
        _caption(doc, f"Table {number}.  {caption}", bold_prefix=f"Table {number}.", space_before=8)

    tbl = doc.add_table(rows=1, cols=len(headers))
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = widths is None
    if widths:
        _fixed_layout(tbl)

    header = tbl.rows[0]
    _repeat_header(header)
    for cell, text in zip(header.cells, headers):
        cell.text = ""
        par = cell.paragraphs[0]
        par.paragraph_format.space_after = Pt(2)
        par.paragraph_format.space_before = Pt(2)
        run = par.add_run(text)
        run.font.bold = True
        run.font.size = Pt(size)
        run.font.name = BODY_FONT
        _shade(cell, HEADER_FILL)

    for row in rows:
        cells = tbl.add_row().cells
        for cell, text in zip(cells, row):
            cell.text = ""
            for index, line in enumerate(str(text).split("\n")):
                par = cell.paragraphs[0] if index == 0 else cell.add_paragraph()
                par.paragraph_format.space_after = Pt(2)
                par.paragraph_format.space_before = Pt(2)
                _rich(par, line, size=size)

    if widths:
        for row in tbl.rows:
            for cell, width in zip(row.cells, widths):
                cell.width = Cm(width)
        for column, width in zip(tbl.columns, widths):
            column.width = Cm(width)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return tbl


def _caption(doc, text, bold_prefix=None, size=9.5, space_before=4):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(space_before)
    par.paragraph_format.space_after = Pt(2)
    par.paragraph_format.keep_with_next = True
    if bold_prefix:
        run = par.add_run(bold_prefix + "  ")
        run.font.bold = True
        run.font.size = Pt(size)
        rest = text[len(bold_prefix):].strip()
        run = par.add_run(rest)
        run.font.size = Pt(size)
    else:
        run = par.add_run(text)
        run.font.size = Pt(size)
    return par


def figure(doc, counter, path, caption, width_cm=15.5):
    number = counter.next_figure()
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_before = Pt(6)
    par.paragraph_format.space_after = Pt(2)
    par.paragraph_format.keep_with_next = True
    par.add_run().add_picture(path, width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(10)
    run = cap.add_run(f"Figure {number}.  ")
    run.font.bold = True
    run.font.size = Pt(9.5)
    run = cap.add_run(caption)
    run.font.size = Pt(9.5)
    return cap


def _fixed_layout(tbl):
    tblpr = tbl._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblpr.append(layout)


def _repeat_header(row):
    trpr = row._tr.get_or_add_trPr()
    flag = OxmlElement("w:tblHeader")
    flag.set(qn("w:val"), "true")
    trpr.append(flag)


def _shade(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcpr.append(shd)


def save(doc, path):
    doc.save(path)
    return path
