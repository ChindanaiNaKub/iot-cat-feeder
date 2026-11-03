"""Build the single bound volume that carries the three reports as parts.

Chapter numbers run continuously across the volume, table and figure numbers share one
sequence, and appendices are lettered once each, so a printed copy reads as one report.
"""

import pathlib

import docx_common
import gen_conclusion
import gen_output
import gen_proposal
import gen_sdd
import gen_srs
import meta
from docx_common import HEADINGS, Numbering, cover, new_document, part, save, table_of_contents

PARTS = [
    (gen_proposal, "Part I", "Project Proposal",
     "Problem, objectives, scope, and the review that supports them.", 0, "A"),
    (gen_srs, "Part II", "Software Requirements Specification",
     "Functions, use cases, interfaces, and verifiable requirements.", 2, "A"),
    (gen_sdd, "Part III", "Software Design Description",
     "Architecture, detailed design, traceability, and the test plan.", 4, "B"),
    (gen_output, "Part IV", "Output and Discussion",
     "The delivered system, the measured results, and what they mean.", 8, "C"),
    (gen_conclusion, "Part V", "Conclusion and Future Work",
     "What was achieved, what was learned, and what comes next.", 11, "D"),
]


def build(out_dir, toc_entries=None):
    HEADINGS.clear()
    doc = new_document("Project Report", meta.PROJECT)
    cover(doc, "Project Report", meta.PROJECT, meta.TAGLINE, meta.MEMBER, meta.STUDENT_ID,
          meta.PROGRAMME, meta.COLLEGE, meta.MONTH, meta.ADVISOR)
    table_of_contents(doc, entries=toc_entries)

    counter = Numbering()
    for module, label, title, blurb, shift, letter in PARTS:
        docx_common.CHAPTER_SHIFT = shift
        docx_common.APPENDIX_LETTER = letter
        part(doc, label, title, blurb)
        module.write_body(doc, counter)

    docx_common.CHAPTER_SHIFT = 0
    docx_common.APPENDIX_LETTER = "A"
    return save(doc, pathlib.Path(out_dir) / "IoT_Cat_Feeder_Report_V1.0.0.docx")
