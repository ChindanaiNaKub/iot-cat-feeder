"""Build Part V, Conclusion and Future Work, for the report volume."""

from docx_common import h1, h2, para, bullets, numbered, table


def write_body(doc, counter):
    # ---------------------------------------------------------------- chapter 1
    h1(doc, 1, "Conclusion")

    h2(doc, "1.1", "Summary")
    para(doc, "The project delivered a working automatic feeder built from a NodeMCU v3, one servo, and two "
              "ultrasonic sensors, with the whole user interface served from the board itself. The device feeds "
              "the cat at three scheduled times taken from network time, feeds on demand from a phone, closes "
              "the flap on every path without depending on the client, and records the meal count, the last "
              "meal, and its trigger source on a dashboard that needs no internet connection.")
    para(doc, "The scope was cut once, deliberately. Portion control by weight was removed on 2 November when "
              "the amplifier module could not be finished in time, and the report records the decision rather "
              "than hiding it.")
    para(doc, "One sensor did not survive assembly. The level sensor was fixed in place before its aim was "
              "checked, and when the glue set the beam landed on the box floor instead of the hopper, so the "
              "percentage never follows the food. The report records the failure in the limitations rather than "
              "printing a level it could not measure.")

    h2(doc, "1.2", "Against the objectives")
    table(doc, counter, "Objectives and outcome", ["Objective", "Outcome", "Where it is shown"], [
        ["Three meals a day from network time",
         "Delivered. The schedule is gated on a valid clock and suppressed per minute.",
         "Part II, F1; Part III, minute key algorithm; results table"],
        ["A dashboard served in under two seconds",
         "Delivered. One compiled response, no external asset, two second refresh. The response time was "
         "not timed with a stopwatch.",
         "Part II, NFR-PM-01"],
        ["The flap closes on every code path",
         "Delivered. The close runs from the main loop and cannot be stranded by a client.",
         "Part III, manual feeding flow; test TC-03"],
        ["A record of when the cat was fed",
         "Delivered. Five meals in RAM, with time and trigger source, on the dashboard.",
         "Part II, F3; Part III, data design"],
        ["Presence detection inside 60 cm",
         "Integrated. The firmware applies the median filter, the three-reading confirmation, a cooldown, and "
         "a daily cap. No acceptance test with the cat was run, so no accuracy figure is claimed.",
         "Part II, F4; Part III, Section 7.2.2"],
        ["Rebuildable from the repository",
         "Delivered. Wiring page, pin map, bring-up sketches, and this volume.",
         "Repository; Part III, detailed design"],
    ], widths=[5.0, 7.0, 4.5])

    h2(doc, "1.3", "Lessons")
    bullets(doc, [
        "**A requirement that depends on a part is a schedule risk until the part is on the bench.** The load "
        "cell was planned as a target feature for weeks. The blocker was found two days before the deadline, "
        "and by then there was no time left to solder, calibrate, and test it.",
        "**A fixed size buffer is a correctness bug.** The status response was malformed for a reason no test "
        "covered, because the test checked the fields that were present and not the ones that were cut off.",
    ])

    h2(doc, "1.4", "Limitations accepted in this version")
    bullets(doc, [
        "The meal history is lost on reboot.",
        "Meal size is open loop and follows the flap dwell, not the mass dispensed.",
        "The meal count increments before the servo moves, so a failed servo still counts a meal.",
        "The hopper level is not delivered. The level sensor was glued down before its aim was checked, so the "
        "beam reads the box floor and the dashboard reports a fixed percentage that does not follow the food. "
        "The mount has to be moved and the depth captured again before the reading means anything.",
        "There is no authentication, so the device is safe only on a trusted network.",
        "The enclosure is cardboard, the servo linkage is taped, and one hopper serves one cat.",
    ])

    # ---------------------------------------------------------------- chapter 2
    h1(doc, 2, "Future Work")

    h2(doc, "2.1", "Portion control by weight")
    para(doc, "The parts are already in the repository as a design: the HX711 amplifier, a 1 kg load cell, the "
              "wiring page, and a calibration sketch. The remaining work is to solder the module header, "
              "calibrate the cell against a known mass, and close the loop. The controller would open the flap, "
              "sample the mass, and close when the target is reached, with the existing timeout as the guard "
              "against a stalled or disconnected cell. The seam is already there, because every feeding path "
              "passes through `feed(source)`. The spread of 18 to 30 pieces per cycle measured in Section 11.5 "
              "is the case for it.")

    h2(doc, "2.2", "Persistence and notification")
    para(doc, "The daily history currently lives in RAM. A small append-only record in flash, capped at the "
              "last 32 meals, would survive a power cut and would let the owner see a week rather than a day. "
              "Once the history is durable, a notification path becomes useful, either as a message on the "
              "local network or as a publish to a broker when the deployment network allows it.")

    h2(doc, "2.3", "Cat identity and imaging")
    para(doc, "The device cannot tell one cat from another, and it cannot show that the cat ate rather than "
              "the bowl. An RFID collar tag would separate the portions between two cats. A camera module "
              "would attach evidence to a meal. Both are additions to a design that already has a single "
              "feeding path to hang them on.")

    h2(doc, "2.4", "Reliability and enclosure")
    para(doc, "A hardware watchdog would recover the device from a firmware hang without the owner power "
              "cycling it. A laser-cut or printed body would fix the servo geometry, which is currently held "
              "by tape and cardboard, and would make the flap repeat the same travel on every cycle.")
