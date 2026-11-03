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
from docx_common import HEADINGS, Numbering, cover, new_document, para, part, save, table_of_contents

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


ABSTRACT = (
    "This report documents an automatic dry-food feeder for one cat, built on a NodeMCU v3 with one servo "
    "and two ultrasonic sensors, and serving its own dashboard over the local Wi-Fi network. The problem is "
    "that an owner who is out of the house cannot deliver the midday meal, and a bowl left full all day "
    "removes portion control. The delivered device dispenses at 08:00, 13:00, and 18:00 from network time, "
    "feeds on demand from a phone, closes the flap from the main loop so a dropped client cannot strand it, "
    "and reports the flap state, the daily count, and the last meal with its trigger source. Portion control "
    "by weight and durable history were removed from version 1.0.0 and recorded as future work. The report "
    "states the measured results and states plainly which tests were not run and why.")


def build(out_dir, toc_entries=None):
    HEADINGS.clear()
    doc = new_document("Project Report", meta.PROJECT)
    cover(doc, "Project Report", meta.PROJECT, meta.TAGLINE, meta.MEMBER, meta.STUDENT_ID,
          meta.PROGRAMME, meta.COLLEGE, meta.MONTH, meta.ADVISOR)
    table_of_contents(doc, entries=toc_entries)

    doc.add_heading("Abstract", level=1)
    HEADINGS.append((1, "Abstract"))
    para(doc, ABSTRACT)

    counter = Numbering()
    for module, label, title, blurb, shift, letter in PARTS:
        docx_common.CHAPTER_SHIFT = shift
        docx_common.APPENDIX_LETTER = letter
        part(doc, label, title, blurb)
        module.write_body(doc, counter)

    docx_common.CHAPTER_SHIFT = 0
    docx_common.APPENDIX_LETTER = "A"
    return save(doc, pathlib.Path(out_dir) / "IoT_Cat_Feeder_Report_V1.0.0.docx")
