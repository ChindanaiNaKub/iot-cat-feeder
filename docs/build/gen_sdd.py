"""Build the Software Design Description as a .docx."""

import pathlib

import meta
from docx_common import (
    HEADINGS, sec, Numbering, cover, h1, h2, h3, para, bullets, numbered, new_document, save,
    table, table_of_contents, figure,
)

FIG = pathlib.Path(__file__).parent / "figures"


def build(out_dir, toc_entries=None):
    HEADINGS.clear()
    doc = new_document(meta.TITLE_SDD, meta.PROJECT)
    _cover(doc)
    table_of_contents(doc, entries=toc_entries)
    write_body(doc, Numbering())
    return save(doc, pathlib.Path(out_dir) / "IoT_Cat_Feeder_SDD_V1.0.0.docx")


def _cover(doc):
    cover(doc, meta.TITLE_SDD, meta.PROJECT, meta.TAGLINE, meta.MEMBER, meta.STUDENT_ID,
          meta.PROGRAMME, meta.COLLEGE, meta.MONTH, meta.ADVISOR)


def write_body(doc, counter):
    # ---------------------------------------------------------------- chapter 1
    h1(doc, 1, "Introduction")

    h2(doc, "1.1", "Purpose")
    para(doc, "This document describes how the IoT Cat Feeder is built. It is the design counterpart to the "
              "Software Requirements Specification, and it is organised around the design views named in "
              "IEEE Std 1016: decomposition, dependency, interface, and detail. Every design entity below "
              "traces back to a requirement, and every requirement traces forward to a test.")
    para(doc, "The reader this document serves is the next student who has to rebuild the device, or the "
              "examiner who has to decide whether the code and the circuit are one system or two unrelated "
              "artefacts.")

    h2(doc, "1.2", "Scope")
    para(doc, "The design covers the firmware in `firmware/feeder/feeder.ino`, the wiring in "
              "`docs/wiring_nodemcu_servo.html`, and the power arrangement. It excludes the mechanical "
              "construction of the cardboard hopper beyond the flap geometry, which is described only where "
              "it constrains the servo.")

    h2(doc, "1.3", "Design Overview")
    para(doc, "The firmware is one translation unit with no classes, no threads, and no dynamic allocation "
              "after start-up. It runs a single cooperative loop that serves HTTP, watches the clock, and "
              "closes the flap. Each of those three duties is a function call, and none of them blocks.")
    para(doc, "The single organising rule is that all feeding passes through `feed(source)`. Three triggers "
              "converge on it: the HTTP handler, the scheduler, and the presence detector. Counting, safety, "
              "and the daily cap therefore live in one place instead of three.")

    h2(doc, "1.4", "Definitions")
    table(doc, counter, "Design terms", ["Term", "Meaning in this document"], [
        ["Component", "A named function or small group of functions with one responsibility."],
        ["State layer", "The `struct Feeder` instance and the functions that read or write it."],
        ["Minute key", "Integer `(day * 100 + hour) * 100 + minute`, used to detect a new minute."],
        ["Flap cycle", "One open command followed by the automatic close."],
        ["Parts received", "Hardware on the bench and wired. Firmware integration and acceptance test outstanding."],
    ], widths=[3.4, 13.1])

    # ---------------------------------------------------------------- chapter 2
    h1(doc, 2, "System Architecture")

    h2(doc, "2.1", "Architectural Overview")
    para(doc, "The system has three layers. The network layer terminates HTTP and converts requests into "
              "commands. The control layer decides whether a meal should happen. The device layer drives the "
              "servo and reports electrical state. The layers are functions in one file rather than modules in "
              "separate files, because the whole program is under 900 lines and a file split would add build "
              "complexity without adding clarity.")
    table(doc, counter, "Layer responsibilities", ["Layer", "Components", "Responsibility"], [
        ["Network", "`keepWifi`, `server`, request handlers",
         "Maintain the link, parse requests, serialise responses."],
        ["Control", "`feed`, `checkSchedule`, `markFeed`, presence detector (target)",
         "Decide when a meal occurs and record it exactly once."],
        ["Device", "`Servo`, `closeFlap`, sensor driver (target)",
         "Drive the actuator and sample the sensors."],
        ["Presentation", "`PAGE`, dashboard script",
         "Render state and send one command."],
    ], widths=[2.8, 6.6, 7.1])

    h2(doc, "2.2", "Context View")
    figure(doc, counter, str(FIG / "context.png"), "Context view: external entities and energy flow.",
           width_cm=16.5)

    h2(doc, "2.3", "Component View")
    figure(doc, counter, str(FIG / "components.png"),
           "Component view. Dashed components are target features.", width_cm=16.5)
    table(doc, counter, "Component catalogue", ["Component", "Kind", "Depends on", "Status"], [
        ["`PAGE`", "Constant string in PROGMEM", "Nothing", "Delivered"],
        ["`server`", "`ESP8266WebServer` instance", "`PAGE`, `statusJson`, `feed`", "Delivered"],
        ["`statusJson`", "Function", "`Feeder`, `clockText`, `scheduleText`, `WiFi`", "Delivered"],
        ["`feed`", "Function", "`markFeed`, `Servo`, `millis`", "Delivered"],
        ["`closeFlap`", "Function", "`Servo`, `Feeder`", "Delivered"],
        ["`markFeed`", "Function", "`time`, `Feeder`", "Delivered"],
        ["`checkSchedule`", "Function", "`time`, `Feeder`, `feed`", "Delivered"],
        ["`clockText`, `scheduleText`", "Functions", "`time`, constant table", "Delivered"],
        ["`keepWifi`", "Function", "`WiFi`, `millis`", "Delivered"],
        ["Presence detector", "Function", "Ultrasonic driver, `feed`", "Parts received"],
    ], widths=[4.0, 4.6, 5.0, 2.9], size=9)

    h2(doc, "2.4", "Deployment and Power Design")
    para(doc, "The device has one power input and one ground reference. The servo is the only load that draws "
              "significant current, and it is the reason the power design differs from the obvious one.")
    table(doc, counter, "Power distribution", ["Rail", "Source", "Loads", "Notes"], [
        ["5 V", "Powerbank, 2 A", "VIN of the board, servo V+", "Servo must not be fed from 3V3."],
        ["3.3 V", "On-board regulator", "ESP8266 core, logic", "Limited to a few hundred milliamps."],
        ["Ground", "Common", "Board, servo, sensors", "A single ground reference for PWM to be valid."],
        ["Bulk capacitance", "470 uF, 16 V", "Across 5 V and ground", "Absorbs the servo inrush."],
    ], widths=[3.2, 3.4, 4.6, 5.3])
    para(doc, "The failure that forced this design was observed during bring-up. With the servo powered from "
              "the notebook USB port, the board reset whenever the servo started. The stall current of the "
              "servo pulls the rail below the regulator dropout. Two changes fixed it: a powerbank with a "
              "higher current limit, and a 470 uF capacitor next to the servo connector. The bring-up sketch "
              "`firmware/servo_test/servo_test.ino` exists so that this behaviour can be reproduced without the "
              "rest of the firmware.")

    h2(doc, "2.5", "Design Rationale")
    table(doc, counter, "Design decisions and alternatives", ["Decision", "Alternative", "Why the alternative lost"], [
        ["Single file, functions only", "Split modules with headers",
         "Under 900 lines. A split adds include order problems for no gain."],
        ["Cooperative loop, no delay", "`delay(900)` after opening the flap",
         "`delay` blocks the HTTP server. The page would freeze on every meal."],
        ["Close driven by `millis()` in the loop", "Close driven by the HTTP handler",
         "The handler runs only if the client stays connected. The loop always runs."],
        ["One `feed(source)` gate", "Separate functions per trigger",
         "Three triggers would need three copies of the counting and cap logic."],
        ["Embedded HTML in PROGMEM", "SPIFFS file, CDN assets",
         "No file system to corrupt, no network fetch, one flash image."],
    ], widths=[4.2, 4.6, 7.7], size=9)

    # ---------------------------------------------------------------- chapter 3
    h1(doc, 3, "Detailed Design")

    h2(doc, "3.1", "Data Design")
    para(doc, "The program holds one state record and three constants. There is no heap use after start-up, "
              "apart from the `String` growth inside the JSON builder, which is bounded by the buffer size.")
    table(doc, counter, "State record", ["Field", "Type", "Initial", "Meaning"], [
        ["`open`", "`bool`", "`false`", "Flap is currently open."],
        ["`openedAt`", "`unsigned long`", "0", "`millis()` at the last open command."],
        ["`countToday`", "`int`", "0", "Meals since the last local date change."],
        ["`lastDay`", "`int`", "-1", "Day of month that `countToday` belongs to."],
        ["`lastTime`", "`String`", "`-`", "HH:MM of the last meal."],
        ["`lastSource`", "`String`", "empty", "Trigger of the last meal."],
    ], widths=[3.2, 3.4, 2.4, 7.5])
    table(doc, counter, "Constants", ["Name", "Value", "Used by"], [
        ["`SERVO_PIN`", "D5, GPIO14", "`setup`"],
        ["`CLOSED_DEG`", "0", "`closeFlap`, `setup`"],
        ["`OPEN_DEG`", "135", "`feed`"],
        ["`OPEN_MS`", "900", "`loop`"],
        ["`SCHEDULE_COUNT`", "3", "`loadSchedule`, `checkSchedule`, `scheduleText`"],
        ["`TZ_OFFSET`", "25200 s", "`setup`"],
    ], widths=[4.2, 4.6, 7.7])
    para(doc, "`OPEN_DEG` is the commanded angle, set a few degrees below the angle where the flap linkage "
              "meets its mechanical stop. Commanding the stop itself would stall the servo for the whole open "
              "interval. A different servo or linkage requires this value to be re-measured.")

    h2(doc, "3.2", "Component Description")
    table(doc, counter, "Function catalogue", ["Function", "Signature", "Purpose"], [
        ["`setup`", "`void setup()`", "Attach the servo, close the flap, start Wi-Fi, start the time client, "
                                     "register routes, start the server."],
        ["`loop`", "`void loop()`", "Poll HTTP, enforce the close deadline, check the schedule, keep the link."],
        ["`feed`", "`void feed(const String &source)`", "Record the meal, open the flap, stamp the open time."],
        ["`closeFlap`", "`void closeFlap()`", "Command the closed angle and clear the open flag."],
        ["`markFeed`", "`void markFeed(const String &source)`", "Update count, time, source, and handle the "
                                                               "date change."],
        ["`checkSchedule`", "`void checkSchedule()`", "Compare local time with the meal table, at most once "
                                                      "per minute."],
        ["`clockText`", "`String clockText()`", "Format the local time, or a placeholder before NTP."],
        ["`scheduleText`", "`String scheduleText()`", "Format the meal table for the dashboard."],
        ["`statusJson`", "`String statusJson()`", "Build the status object."],
        ["`keepWifi`", "`void keepWifi()`", "Reconnect at most once every 5 s, with one console line."],
        ["`loadSchedule`, `saveSchedule`, `applySchedule`", "`void` / `bool`",
         "Read the meal table from EEPROM, write it back, and validate a new one."],
    ], widths=[3.0, 5.4, 8.1], size=9)

    h3(doc, "3.2.1", "Algorithm: the minute key")
    para(doc, "The scheduler must fire once per scheduled minute, but `loop` runs thousands of times per "
              "second. The design collapses the date and time into one integer and compares it with the value "
              "from the previous iteration.")
    para(doc, "`key = (tm_mday * 100 + tm_hour) * 100 + tm_min`", align="left")
    bullets(doc, [
        "A repeated call inside the same minute produces the same key, so the function exits before the meal "
        "table is examined.",
        "The key changes at a minute boundary, at an hour boundary, and at a month boundary, because the day "
        "field is included. Two identical keys therefore indicate the same minute, not merely the same clock "
        "face.",
        "The design trades a rare false negative for a common false positive. A clock that jumps backward one "
        "minute re-enters a previous key and is suppressed. A clock that jumps backward by hours may re-enter "
        f"a key that matches a meal time, which is the residual risk recorded in Section {sec('3.6')}.",
    ])

    h3(doc, "3.2.2", "Algorithm: median filtering for ranging (target)")
    para(doc, "A single ultrasonic reading on a kibble surface is unreliable because the beam scatters. The "
              "target design takes ten samples, sorts them, and uses the median. A detection is confirmed only "
              "after three consecutive medians fall inside the range window, which removes one-off echoes "
              "from the hopper wall or the cat's own movement.")

    h2(doc, "3.3", "State Design")
    figure(doc, counter, str(FIG / "state.png"),
           "State design. Solid transitions are delivered, dashed are targets.", width_cm=16.5)
    table(doc, counter, "State transitions", ["From", "Event", "Guard", "To", "Action"], [
        ["IDLE", "Boot", "None", "IDLE", "Servo to closed angle."],
        ["IDLE", "`feed(source)`", "None", "FEEDING", "Record meal, servo to open angle, stamp time."],
        ["FEEDING", "Loop iteration", "`millis() - openedAt >= 900`", "IDLE", "Servo to closed angle."],
        ["FEEDING", "Loop iteration", "Close deadline not reached", "FEEDING", "None."],
        ["IDLE", "Cat within 60 cm, three times", "Cooldown expired, cap not reached", "FEEDING",
         "Record meal with source presence.", ],
        ["FEEDING", "Presence meal completed", "None", "COOLDOWN", "Start 30 minute timer."],
        ["COOLDOWN", "Loop iteration", "30 minutes elapsed", "IDLE", "None."],
    ], widths=[2.2, 4.4, 4.2, 2.2, 3.5], size=9)

    h2(doc, "3.4", "Interaction Flows")

    h3(doc, "3.4.1", "Flow: manual feeding")
    numbered(doc, [
        "The dashboard sends `POST /feed` with an empty body.",
        "`server.handleClient()` in the main loop dispatches the request to the registered handler.",
        "The handler calls `feed(\"manual\")` and sends `{\"ok\":true}`.",
        "`feed` calls `markFeed`, which reads `time()`, formats HH:MM, resets the count if the day changed, "
        "increments the count, and stores the source.",
        "`feed` writes the open angle and records `millis()`.",
        "On a later loop iteration, the close condition becomes true and `closeFlap` writes the closed angle.",
        "The dashboard, polling every 2 seconds, reads `open: false` and the updated count.",
    ])

    h3(doc, "3.4.2", "Flow: scheduled feeding")
    numbered(doc, [
        "A loop iteration calls `checkSchedule`.",
        "The function reads `time()`. If the value is below the validity epoch, it returns.",
        "It computes the minute key and compares it with the stored key. If equal, it returns.",
        "It stores the new key and compares the hour and minute with each row of the meal table.",
        "On a match it calls `feed(\"schedule\")` and returns, so a second match in the same iteration cannot "
        "occur.",
    ])

    h3(doc, "3.4.3", "Flow: network recovery")
    numbered(doc, [
        "Each loop iteration calls `keepWifi`.",
        "If the link is up and the address has not been printed since the last recovery, the address is "
        "printed once.",
        "If the link is down, the function returns unless 5 seconds have passed since the last attempt.",
        "It starts a connection attempt and stamps the time. The attempt does not block.",
    ])

    h2(doc, "3.5", "Interface Design")

    h3(doc, "3.5.1", "HTTP contract")
    para(doc, "The endpoint contract and the status fields are specified in the interface section of the "
              "Software Requirements Specification. The handler for each path is a lambda registered in "
              "`setup`, and every handler returns the same status object so the dashboard can render one shape.")

    h3(doc, "3.5.2", "Response format")
    para(doc, "The status object is assembled into a reserved `String` and each numeric fragment is formatted "
              "with `snprintf` into a 96 byte stack buffer. The return value of `snprintf` is compared with the "
              "buffer size, and an overflow is reported on the serial console instead of truncating silently. "
              "The 96 byte size was chosen after the first 64 byte buffer cut the history array and produced "
              "malformed JSON.")

    h3(doc, "3.5.3", "User interface")
    table(doc, counter, "Dashboard layout", ["Region", "Content", "Interaction"], [
        ["Header", "Device name and one-line purpose", "None"],
        ["Status card", "Five rows: flap, meals today, last meal, device time, schedule", "Read only"],
        ["Action", "Full-width feeding button", "`POST /feed`, then a 1300 ms lockout"],
        ["Footer", "RSSI and IP, or a lost-connection message", "None"],
    ], widths=[3.4, 8.1, 5.0])

    h2(doc, "3.6", "Error Handling and Recovery")
    table(doc, counter, "Failure modes", ["Failure", "Detection", "Response", "Residual risk"], [
        ["Wi-Fi lost", "`WiFi.status()`", "Retry every 5 s without rebooting", "Dashboard unavailable until "
                                                                            "the link returns"],
        ["Time not yet valid", "Epoch below 1600000000", "Scheduler disabled, placeholder clock shown",
         "A meal during the first seconds after boot is skipped"],
        ["Clock jumps backward", "Repeated minute key", "The meal in that minute is suppressed",
         "A jump of hours can re-enter a meal minute"],
        ["Client disconnects mid-request", "Handler never returns", "The loop closes the flap on schedule",
         "The count is already incremented"],
        ["Servo stalls", "Not detected", "None in firmware", "Brownout, reboot, lost meal"],
        ["Unknown path", "`onNotFound`", "404 with no state change", "None"],
        ["Buffer truncation", "Not detected", "None", "Malformed JSON if a field grows"],
    ], widths=[3.4, 3.4, 4.8, 4.9], size=9)

    h2(doc, "3.7", "Security Considerations")
    bullets(doc, [
        "The trust boundary is the Wi-Fi network. Any client on it can dispense food. This is accepted for a "
        "single household and is documented in the SRS limitations.",
        "No administrative endpoint exists, so there is no credential to steal from the device.",
        "The Wi-Fi credentials live in `secrets.h`, which is excluded by `.gitignore`. The repository ships "
        "`secrets.example.h` only.",
        "The device sends no telemetry outbound except the NTP query, which carries no user data.",
    ])

    # ---------------------------------------------------------------- chapter 4
    h1(doc, 4, "Traceability and Verification")

    h2(doc, "4.1", "Requirements Traceability Matrix")
    table(doc, counter, "Traceability", ["Requirement", "Component", "Test"], [
        ["FR-01, FR-02, FR-03", "`checkSchedule`, `configTime`", "TC-04, TC-05"],
        ["FR-04, FR-05", "`feed`, `closeFlap`, `loop`", "TC-02, TC-03"],
        ["FR-06, FR-12", "Route registration, `onNotFound`", "TC-08"],
        ["FR-07, FR-10, FR-11", "`statusJson`, `PAGE`", "TC-01, TC-06"],
        ["FR-08", "Dashboard script", "TC-01"],
        ["FR-09", "`markFeed`", "TC-07"],
        ["FR-13, FR-14", "Presence detector, target", "TC-09"],
        ["FR-15", "Not implemented, deferred", "Future work"],
        ["FR-16", "Level sensor", "TC-10"],
        ["FR-17, FR-18", "Not implemented", "Future work"],
        ["NFR-RL-01", "`loop` close condition", "TC-03"],
        ["NFR-RL-02", "`keepWifi`", "TC-11"],
        ["NFR-SEC-01", "`.gitignore`", "Inspection"],
    ], widths=[4.0, 6.4, 6.1])

    h2(doc, "4.2", "Test Plan")
    table(doc, counter, "Test cases", ["ID", "Case", "Procedure", "Pass condition"], [
        ["TC-01", "Dashboard loads", "Open the device address on a phone.", "Five rows populated within 2 s."],
        ["TC-02", "Manual feeding", "Press the button, observe the flap.", "Flap opens within 1.5 s."],
        ["TC-03", "Automatic close", "Press 50 times with 5 s between presses.",
         "All 50 close without intervention. No flap stays open."],
        ["TC-04", "Schedule fires", "Set the next meal one minute ahead and wait.",
         "One meal at the minute, recorded with source schedule."],
        ["TC-05", "Duplicate suppression", "Observe the same minute for 60 s.", "Exactly one meal."],
        ["TC-06", "Status accuracy", "Compare every field with the device state.",
         "All fields match."],
        ["TC-07", "Date rollover", "Let the device run past local midnight.", "Count returns to zero."],
        ["TC-08", "Method rejection", "`GET /feed`, `POST /status`, and an unknown path.",
         "404 for each, with no meal dispensed."],
        ["TC-09", "Presence detection", "Walk past the sensor 20 times at 50 to 70 cm.",
         "At least 16 detections, no meal inside the cooldown."],
        ["TC-10", "Hopper level", "Fill the hopper to three measured levels.",
         "The reported percentage is within 10 points of each fill."],
        ["TC-11", "Network recovery", "Power cycle the router.", "The device rejoins within 30 s, no reboot."],
    ], widths=[1.3, 3.2, 6.2, 5.8], size=9)

