"""Build the Software Requirements Specification as a .docx."""

import pathlib

import meta
from docx_common import (
    HEADINGS, sec, Numbering, cover, h1, h2, h3, para, bullets, new_document, save,
    table, table_of_contents, figure,
)

FIG = pathlib.Path(__file__).parent / "figures"


def use_case(doc, counter, code, title, fields):
    rows = [[k, v] for k, v in fields]
    table(doc, counter, f"{code}: {title}", ["Item", "Description"], rows, widths=[3.6, 12.9], size=9.5)


def build(out_dir, toc_entries=None):
    HEADINGS.clear()
    doc = new_document(meta.TITLE_SRS, meta.PROJECT)
    _cover(doc)
    table_of_contents(doc, entries=toc_entries)
    write_body(doc, Numbering())
    return save(doc, pathlib.Path(out_dir) / "IoT_Cat_Feeder_SRS_V1.0.0.docx")


def _cover(doc):
    cover(doc, meta.TITLE_SRS, meta.PROJECT, meta.TAGLINE, meta.MEMBER, meta.STUDENT_ID,
          meta.PROGRAMME, meta.COLLEGE, meta.MONTH, meta.ADVISOR)


def write_body(doc, counter):
    # ---------------------------------------------------------------- chapter 1
    h1(doc, 1, "Introduction")

    h2(doc, "1.1", "Purpose")
    para(doc, "This document specifies the requirements for the IoT Cat Feeder, version 1.0.0. It is written "
              "for the project advisor as the acceptance basis, for the developer as the input to the design, "
              "and for the examiner as the evidence that each requirement has a stated, checkable condition.")
    para(doc, "The document follows the structure of ISO/IEC/IEEE 29148 for software requirements. The section "
              "order is adapted to the size of the project: the standard separates product functions from "
              "detailed requirements, which this document keeps, and it separates verification from the "
              f"requirement text, which this document keeps as a matrix in Section {sec('2.10')}.")

    h2(doc, "1.2", "Scope")
    para(doc, "The product is a single-board appliance that dispenses dry cat food on a schedule and on demand, "
              "and reports its state through a web page served by the same board.")
    table(doc, counter, "System identification", ["Item", "Value"], [
        ["Product name", "IoT Cat Feeder"],
        ["Version specified", "1.0.0"],
        ["Platform", "NodeMCU v3, ESP8266EX, 80 MHz, 4 MB flash"],
        ["Runtime", "Arduino core for ESP8266, single-threaded main loop"],
        ["Network role", "Wi-Fi station client with an embedded HTTP server on port 80"],
        ["Users", "One owner, one cat"],
        ["Operating environment", "Indoor, 2.4 GHz Wi-Fi, 5 V 2 A supply"],
    ], widths=[4.6, 11.9])
    para(doc, "The product does not store data outside the device, does not authenticate users, and does not "
              "depend on any external service other than a network time server.")

    h2(doc, "1.3", "Product Perspective")
    para(doc, "The device is a standalone system. It replaces the manual act of pouring food, not a software "
              "component inside another product. The owner is the only human actor. The clock is an external "
              "service that provides the time reference. The cat is an environmental actor whose position "
              "becomes an input through the presence requirement.")

    h2(doc, "1.4", "Product Functions")
    table(doc, counter, "Product functions", ["ID", "Function", "Summary", "Status"], [
        ["F1", "Scheduled feeding", "Dispenses one meal at each configured time, using network time.", "Delivered"],
        ["F2", "On-demand feeding", "Dispenses one meal when the owner presses the dashboard button.", "Delivered"],
        ["F3", "Status and history", "Reports flap state, daily count, last meal, and link quality.", "Delivered"],
        ["F4", "Presence-triggered feeding", "Dispenses a meal when a cat is detected near the bowl.", "Integrated"],
        ["F5", "Hopper level monitoring", "Reports the remaining food as a percentage of hopper depth.", "Not delivered"],
    ], widths=[1.2, 4.2, 8.1, 3.0])

    h2(doc, "1.5", "User Characteristics")
    table(doc, counter, "User classes", ["User class", "Technical level", "Characteristics and needs"], [
        ["Owner", "Non-technical", "Uses a phone browser. Expects a single page with a single action. Cannot "
                                   "be asked to install software, create an account, or read a manual."],
        ["Maintainer", "Technical", "Rebuilds and reflashes the device. Needs the wiring, the pin map, the "
                                    "library list, and the credentials file documented."],
        ["Cat", "None", "Interacts physically. Must not be able to open the flap or be caught by it."],
    ], widths=[3.2, 3.2, 10.1])

    h2(doc, "1.6", "Limitations")
    bullets(doc, [
        "History is held in RAM. A reboot clears the daily count.",
        "Any device on the same Wi-Fi network can issue a feeding command, because there is no authentication.",
        "Only dry food with a free-flowing particle size can be dispensed.",
        "The device cannot detect that the bowl is already full before dispensing.",
        "Only one feeder and one hopper are supported.",
        "The system does not operate without a 5 V supply.",
    ])

    h2(doc, "1.7", "Assumptions and Dependencies")
    table(doc, counter, "Assumptions and dependencies", ["ID", "Statement", "Effect if false"], [
        ["A-01", "The Wi-Fi network is 2.4 GHz and reachable from the device position.",
         "The device cannot join. The dashboard is unreachable."],
        ["A-02", "A network time server is reachable at least once after each boot.",
         "Scheduled feeding is disabled. Manual feeding still works."],
        ["A-03", "The hopper holds at least 300 g of dry food.",
         "Meals become short. The level requirement reports the shortage."],
        ["A-04", "The servo can lift the flap without stalling.",
         "Brownout or a failed meal. R-01 in the proposal covers the mitigation."],
        ["A-05", "The owner's phone and the device are on the same subnet.",
         "The dashboard cannot be reached by name or address."],
    ], widths=[1.4, 9.0, 6.1])

    h2(doc, "1.8", "Definitions")
    table(doc, counter, "Definitions", ["Term", "Definition"], [
        ["Meal", "One dispense cycle, defined as one flap open event followed by an automatic close."],
        ["Flap", "The servo-driven cover that gates the hopper outlet."],
        ["Hopper", "The container that holds dry food above the flap."],
        ["Schedule minute", "A minute of local time that appears in the configured meal table."],
        ["Source", "The trigger of a meal: the web button, the schedule, or the presence sensor."],
        ["Minute key", "An integer that identifies one calendar minute, used to prevent duplicate meals."],
        ["Integrated", "Wired and driven by the firmware as a target feature. No acceptance test has been "
                       "run, so the requirement is not claimed as delivered."],
        ["Not delivered", "The function exists in the firmware but the hardware does not produce a usable "
                          "signal. The reason is stated where the requirement is described."],
    ], widths=[3.6, 12.9])

    h2(doc, "1.9", "References")
    table(doc, counter, "References", ["Reference", "Use in this document"], [
        ["ISO/IEC/IEEE 29148:2018, Requirements engineering", "Structure of the requirement sections."],
        ["IEEE Std 1016-2009, Software design descriptions", "Structure of the companion SDD."],
        ["Arduino core for ESP8266, reference documentation",
         "Behaviour of `ESP8266WebServer`, `configTime`, and `WiFi`."],
        ["HC-SR04 ultrasonic sensor datasheet", "Range, beam angle, and supply voltage limits."],
        ["HX711 datasheet", "Clock timing and gain selection."],
        ["SG90 servo datasheet", "Stall current and torque limits."],
    ], widths=[8.0, 8.5])

    # ---------------------------------------------------------------- chapter 2
    h1(doc, 2, "Specification Requirements")

    h2(doc, "2.1", "Feature Description")

    h3(doc, "2.1.1", "F1: Scheduled Feeding")
    para(doc, "At each configured meal time the device dispenses one meal without any user action. The time "
              "reference comes from a network time server, so the schedule stays correct after a power cut "
              "without a battery-backed clock.")
    table(doc, counter, "F1 parameters", ["Parameter", "Value"], [
        ["Meal times", "08:00, 13:00, 18:00"],
        ["Time zone", "UTC+7, no daylight saving"],
        ["Time sources", "`pool.ntp.org`, `time.nist.gov`"],
        ["Duplicate suppression", "One meal per calendar minute"],
        ["Editing", "Dashboard form, stored in EEPROM"],
        ["Behaviour before time is valid", "Scheduler disabled, dashboard shows `--:--:--`"],
    ], widths=[5.2, 11.3])

    h3(doc, "2.1.2", "F2: On-Demand Feeding")
    para(doc, "The owner presses a button on the dashboard and receives a meal within 1.5 seconds. The request "
              "is a `POST` to `/feed`. The button disables itself for 1.3 seconds after the press so that a "
              "double tap does not produce two overlapping cycles.")
    table(doc, counter, "F2 parameters", ["Parameter", "Value"], [
        ["Endpoint", "`POST /feed`"],
        ["Response", "`200` with `{\"ok\":true}`"],
        ["Flap open duration", "900 ms"],
        ["Client lockout", "1300 ms"],
        ["Accepted methods", "`POST` only. Others return 404."],
    ], widths=[5.2, 11.3])

    h3(doc, "2.1.3", "F3: Status and History")
    para(doc, "The dashboard shows five values and refreshes without user action. The values answer one "
              "question: was the cat fed today, and by what.")
    table(doc, counter, "F3 parameters", ["Displayed value", "Source field", "Format"], [
        ["Flap state", "`open`", "Open, or Closed"],
        ["Meals today", "`count`", "Integer with unit"],
        ["Last meal", "`last`, `source`", "HH:MM with trigger in brackets"],
        ["Device time", "`time`", "HH:MM:SS"],
        ["Configured schedule", "`schedule`", "Three times separated by a middle dot"],
        ["Link quality", "`rssi`, `ip`", "dBm and dotted quad"],
    ], widths=[5.2, 4.6, 6.7])

    h3(doc, "2.1.4", "F4: Presence-Triggered Feeding (target)")
    para(doc, "An ultrasonic sensor aimed at the approach path detects a cat within 60 cm. A confirmed "
              "detection dispenses one meal, subject to a cooldown and a daily cap. Confirmation requires "
              "three consecutive readings inside range, which prevents a single stray echo from feeding the cat.")

    h3(doc, "2.1.5", "F5: Hopper Level Monitoring")
    para(doc, "A second ultrasonic sensor aimed down into the hopper estimates the remaining food as a "
              "percentage of the usable depth. Portion control by weight moved to Future Work on 2 November, "
              "when the amplifier header pins were found to be unsoldered.")

    h2(doc, "2.2", "Use Case Diagram")
    figure(doc, counter, str(FIG / "usecase.png"),
           "Use cases. Dashed use cases are planned extensions and are not part of version 1.0.0.",
           width_cm=16.5)

    h2(doc, "2.3", "Use Case Description")

    h3(doc, "2.3.1", "UC-01: Feed the Cat on Demand")
    use_case(doc, counter, "UC-01", "Feed the cat on demand", [
        ("Actor", "Owner"),
        ("Goal", "Dispense one meal immediately."),
        ("Precondition", "The device is powered and reachable on the network. A browser has loaded the dashboard."),
        ("Trigger", "The owner presses the feeding button."),
        ("Main flow", "1. The browser sends `POST /feed`.\n2. The device validates the method.\n3. The device records the "
                      "meal with source `manual`.\n4. The device drives the servo to the open angle.\n5. The device "
                      "returns `{\"ok\":true}`.\n6. After 900 ms the main loop closes the flap."),
        ("Alternate flow", "A1. The request times out: the browser shows a connection failure, and the flap "
                           "still closes because the close is driven locally."),
        ("Postcondition", "One meal is counted. The flap is closed."),
        ("Frequency", "Up to several times per day."),
    ])

    h3(doc, "2.3.2", "UC-02: Receive a Scheduled Feeding")
    use_case(doc, counter, "UC-02", "Receive a scheduled feeding", [
        ("Actor", "System clock, provided by NTP"),
        ("Goal", "Dispense one meal at a configured time without user action."),
        ("Precondition", "The device has a valid time, meaning the epoch is later than 9 September 2020."),
        ("Trigger", "Local time reaches a minute in the meal table."),
        ("Main flow", "1. The main loop reads the local time.\n2. The minute key is computed.\n3. If the key equals the "
                      "previous key, the loop exits.\n4. If the minute matches a meal time, one meal is dispensed "
                      "with source `schedule`.\n5. The flap closes after 900 ms."),
        ("Alternate flow", "A1. Time is not yet valid: the loop exits without dispensing. A2. The clock jumps "
                           "backward after a resync: a repeated minute key still produces at most one meal."),
        ("Postcondition", "One meal is counted with source `schedule`."),
        ("Frequency", "Three times per day."),
    ])

    h3(doc, "2.3.3", "UC-03: View Status and History")
    use_case(doc, counter, "UC-03", "View status and history", [
        ("Actor", "Owner"),
        ("Goal", "Confirm that the cat has been fed and inspect the device clock."),
        ("Precondition", "The device is reachable."),
        ("Trigger", "The owner opens the dashboard, or the two-second refresh fires."),
        ("Main flow", "1. The browser sends `GET /status`.\n2. The device serialises the status object.\n3. The page updates "
                      "five display rows and the link footer."),
        ("Alternate flow", "A1. The request fails: the footer reports a lost connection and the previous "
                           "values stay on screen."),
        ("Postcondition", "No state changes on the device."),
        ("Frequency", "Continuous while the page is open."),
    ])

    h3(doc, "2.3.4", "UC-04: Feed When the Cat Approaches (target)")
    use_case(doc, counter, "UC-04", "Feed when the cat approaches", [
        ("Actor", "Cat"),
        ("Goal", "Dispense a meal when the cat is at the bowl and the cooldown has expired."),
        ("Precondition", "The presence sensor is connected and calibrated. The daily cap is not reached."),
        ("Trigger", "Three consecutive distance readings below 60 cm."),
        ("Main flow", "1. The loop polls the sensor.\n2. The median distance is computed.\n3. The confirmation counter "
                      "increments.\n4. A meal is dispensed with source `presence`.\n5. The cooldown starts."),
        ("Alternate flow", "A1. The cat leaves before confirmation: the counter resets. A2. Cooldown is active: "
                           "the request is ignored and no meal is counted."),
        ("Postcondition", "One meal is counted. The presence cooldown is running."),
        ("Frequency", "At most once per 30 minutes."),
    ])

    h3(doc, "2.3.5", "UC-05: Recover From a Network Loss")
    use_case(doc, counter, "UC-05", "Recover from a network loss", [
        ("Actor", "System"),
        ("Goal", "Return to the network without a reboot."),
        ("Precondition", "The device was connected and lost the link."),
        ("Trigger", "The connection state changes to disconnected."),
        ("Main flow", "1. The loop checks the connection state.\n2. A retry is issued no more than once every 5 seconds.\n"
                      "3. On success the local address is printed once to the serial console."),
        ("Alternate flow", "A1. The network is absent: retries continue indefinitely at the same rate."),
        ("Postcondition", "The dashboard is reachable again. No meal state is lost."),
        ("Frequency", "On every disconnection."),
    ])

    h2(doc, "2.4", "Activity Diagram")
    para(doc, "The activity diagram below shows one iteration of the main loop. The close of the flap is evaluated on every "
              "iteration and does not depend on an HTTP request completing.")
    figure(doc, counter, str(FIG / "activity.png"), "Main loop activity.", width_cm=16.5)

    h2(doc, "2.5", "Functional Requirements")
    para(doc, "Priority uses MoSCoW. Verification uses one of T for test, D for demonstration, A for analysis, "
              "or I for inspection.")
    table(doc, counter, "Functional requirements", ["ID", "Requirement", "Priority", "Verification", "Status"], [
        ["FR-01", "The device shall dispense one meal at 08:00, 13:00, and 18:00 local time.",
         "Must", "T", "Delivered"],
        ["FR-02", "The device shall obtain local time from a network time server and shall not evaluate the "
                  "schedule until the time is valid.", "Must", "T", "Delivered"],
        ["FR-03", "The device shall dispense at most one scheduled meal per calendar minute.",
         "Must", "T", "Delivered"],
        ["FR-04", "The device shall dispense one meal when it receives `POST /feed`.", "Must", "T", "Delivered"],
        ["FR-05", "The device shall close the flap within 1000 ms of opening it, on every code path.",
         "Must", "T", "Delivered"],
        ["FR-06", "The device shall reject any method other than `POST` on `/feed`.", "Must", "T", "Delivered"],
        ["FR-07", f"The device shall return the status fields defined in Section {sec('2.6.2')} on "
                  "`GET /status`.",
         "Must", "T", "Delivered"],
        ["FR-08", "The dashboard shall refresh its values every 2 seconds without user action.",
         "Must", "D", "Delivered"],
        ["FR-09", "The device shall reset the daily meal count when the local date changes.", "Must", "T",
         "Delivered"],
        ["FR-10", "The device shall record the trigger source of every meal.", "Must", "T",
         "Delivered"],
        ["FR-11", "The device shall serve the dashboard page on `GET /` with no external asset.",
         "Must", "T", "Delivered"],
        ["FR-12", "The device shall return 404 for every undefined path.", "Must", "T", "Delivered"],
        ["FR-13", "The device shall detect a cat within 60 cm of the bowl after three consecutive readings.",
         "Should", "T", "Integrated"],
        ["FR-14", "The device shall not dispense more than one presence-triggered meal in 30 minutes.",
         "Should", "T", "Integrated"],
        ["FR-15", "The device shall dispense a mass within 15 percent of the configured target.",
         "Could", "T", "Future work"],
        ["FR-16", "The device shall report hopper level as a percentage of usable depth.", "Could", "D",
         "Not delivered"],
        ["FR-17", "The device shall persist the daily history across a reboot.", "Could", "T", "Future work"],
        ["FR-18", "The device shall refuse a meal when the configured daily cap is reached.", "Should", "T",
         "Integrated"],
        ["FR-19", "The device shall accept three meal times on `POST /schedule`, reject a malformed value, "
                  "and retain the accepted table across a reboot.", "Must", "T", "Delivered"],
    ], widths=[1.4, 7.9, 2.1, 2.5, 2.7], size=8.8)

    h2(doc, "2.6", "External Interface Requirements")

    h3(doc, "2.6.1", "User Interface")
    para(doc, "One page, one column, maximum width 420 px, in Thai. The page uses a light background and a "
              "single accent colour. It has no navigation, no form, and no settings panel.")
    table(doc, counter, "Dashboard elements", ["Element", "Type", "Behaviour"], [
        ["Title block", "Static text", "Names the device and states the primary action."],
        ["Status card", "Five text rows", "Rebuilt from `/status` on every refresh."],
        ["Feed button", "Button", "Sends `POST /feed`, disables itself for 1300 ms."],
        ["Link footer", "Text", "Shows RSSI and IP, or a lost-connection message."],
    ], widths=[3.8, 3.0, 9.7])

    h3(doc, "2.6.2", "Software Interface")
    table(doc, counter, "HTTP interface", ["Method", "Path", "Request body", "Response"], [
        ["GET", "/", "None", "HTML, 200"],
        ["GET", "/status", "None", "JSON, 200, `application/json; charset=utf-8`"],
        ["POST", "/feed", "None", "Status JSON, 200"],
        ["POST", "/schedule", "`t=HH:MM,HH:MM,HH:MM`", "Status JSON, 200; `{\"ok\":false}`, 400 if malformed"],
        ["Any", "Other", "None", "Text, 404"],
    ], widths=[2.4, 3.2, 3.4, 7.5])

    table(doc, counter, "Status response fields", ["Field", "Type", "Range", "Meaning"], [
        ["open", "Boolean", "true, false", "Flap is open."],
        ["count", "Integer", "0 to 255", "Meals counted since local midnight."],
        ["last", "String", "HH:MM or -", "Local time of the last meal."],
        ["source", "String", "label or empty", "Trigger of the last meal."],
        ["time", "String", "HH:MM:SS or --:--:--", "Device local time."],
        ["schedule", "String", "Three times", "Configured meal times."],
        ["ip", "String", "Dotted quad", "Device address."],
        ["rssi", "Integer", "-90 to -30", "Signal strength in dBm."],
        ["level", "Integer", "-1 to 100", "Hopper fill percentage. -1 before the first sample."],
        ["near", "Number", "cm, -1 unknown", "Last presence distance."],
        ["cat", "Boolean", "true, false", "A cat is inside the presence range now."],
        ["cap", "Integer", "0 to 6", "Presence-triggered meals used today."],
        ["hist", "Array", "Up to 5 entries", "Recent meals, each with time and source."],
    ], widths=[2.6, 2.4, 5.4, 6.1])

    h3(doc, "2.6.3", "Hardware Interface")
    table(doc, counter, "Hardware interface", ["Device", "Signal", "Pin", "Electrical notes", "Status"], [
        ["Servo SG90", "PWM", "D5, GPIO14", "50 Hz, 1 to 2 ms pulse. Powered from VIN, not 3V3.", "Connected"],
        ["Servo SG90", "Supply", "VIN, GND", "5 V from powerbank. 470 uF across the rail.", "Connected"],
        ["HC-SR04 presence", "Trig", "D6, GPIO12", "3.3 V drive is accepted.", "Wired"],
        ["HC-SR04 presence", "Echo", "D7, GPIO13", "5 V output. Divided to 3.00 V with 2.2k and 3.3k.", "Wired"],
        ["HC-SR04 level", "Trig", "D1, GPIO5", "Aimed down into the hopper.", "Wired"],
        ["HC-SR04 level", "Echo", "D2, GPIO4", "Divided with a second 2.2k and 3.3k pair.", "Wired"],
    ], widths=[2.6, 2.0, 2.9, 6.4, 2.6], size=9)

    h2(doc, "2.7", "Data Requirements")
    para(doc, "The device keeps one state record in RAM and one schedule table in EEPROM. There is no "
              "database, no file system, and no remote store in the delivered baseline.")
    table(doc, counter, "Persistent and in-memory data", ["Name", "Type", "Lifetime", "Purpose"], [
        ["Feeder state", "Struct of six fields", "Until reboot", "Flap state, count, last meal, source, day."],
        ["Meal table", "Three hour and minute pairs", "EEPROM, survives reboot", "Schedule definition."],
        ["Meal history", "Ring buffer of five entries", "Until reboot", "Recent meals for the dashboard."],
        ["Minute key", "Integer", "Until reboot", "Duplicate suppression for the scheduler."],
        ["Last connection attempt", "Unsigned long", "Until reboot", "Rate limit for Wi-Fi retries."],
    ], widths=[4.2, 4.0, 3.6, 4.7])
    para(doc, "Requirement FR-17 would add a flash record with one line per meal, written append-only, capped at "
              "the last 32 meals. That record is not part of version 1.0.0.")

    h2(doc, "2.8", "Quality Requirements")
    table(doc, counter, "Non-functional requirements", ["ID", "Category", "Requirement", "Verification"], [
        ["NFR-PM-01", "Performance", "A dashboard request completes within 2 s on the same network.", "T"],
        ["NFR-PM-02", "Performance", "A manual meal starts within 1.5 s of the button press.", "T"],
        ["NFR-PM-03", "Performance", "Presence detection dispenses within 2 s of entering range.", "T"],
        ["NFR-RL-01", "Reliability", "The flap is never open longer than 3 s.", "T"],
        ["NFR-RL-02", "Reliability", "The device rejoins the network within 30 s of it returning, with no reboot.", "T"],
        ["NFR-RL-03", "Reliability", "Schedule timing drifts by no more than 1 minute over 24 hours.", "T"],
        ["NFR-RL-04", "Reliability", "A failed HTTP response does not leave the flap open.", "A"],
        ["NFR-UH-01", "Usability", "The dashboard is readable at 375 px width without zoom.", "D"],
        ["NFR-UH-02", "Usability", "A first-time user feeds the cat without instruction.", "D"],
        ["NFR-UH-03", "Usability", "The dashboard states the connection state when the link fails.", "D"],
        ["NFR-SEC-01", "Security", "Wi-Fi credentials are excluded from version control.", "I"],
        ["NFR-SEC-02", "Security", "Only documented methods and paths are served.", "T"],
        ["NFR-SEC-03", "Security", "The device exposes no administrative endpoint.", "I"],
        ["NFR-OP-01", "Maintainability", "The firmware builds from a documented library set.", "I"],
        ["NFR-OP-02", "Maintainability", "The pin map and wiring are documented in one page.", "I"],
        ["NFR-CP-01", "Constraint", "The device runs from a 5 V 2 A powerbank with no host computer.", "T"],
        ["NFR-CP-02", "Constraint", "The device operates on 2.4 GHz Wi-Fi only.", "I"],
        ["NFR-CP-03", "Constraint", "The firmware fits in the 4 MB flash of the NodeMCU v3.", "I"],
    ], widths=[2.6, 2.8, 8.7, 2.4], size=9)

    h2(doc, "2.9", "Design Constraints")
    bullets(doc, [
        "The servo signal uses GPIO14 because the board exposes it as D5 with no boot-time conflict.",
        "The echo line of a 5 V ultrasonic sensor must be divided before it reaches a 3.3 V input.",
        "No blocking delay is permitted in the main loop, because the HTTP server is polled from the same loop.",
        "The dashboard must be complete in one response under 4 KB, because it is compiled into the binary.",
    ])

    h2(doc, "2.10", "Verification")
    para(doc, "Each requirement maps to one test case in the SDD. The matrix below states the method and the "
              "pass condition at requirement level.")
    table(doc, counter, "Verification matrix", ["Requirement group", "Method", "Pass condition"], [
        ["FR-01 to FR-03", "Timed observation", "Exactly three scheduled meals in 24 hours, each within 1 minute."],
        ["FR-04, FR-05", "Manual test, 50 repetitions", "Every repetition dispenses and closes. No flap stays open."],
        ["FR-06, FR-12", "Request inspection", "Non-POST and unknown paths return 404 with no side effect."],
        ["FR-07, FR-10, FR-11", "Response inspection", "All fields present, values match the device state."],
        ["FR-08", "Observation", "The page changes without user action within 2 s."],
        ["FR-09", "Clock rollover", "The count returns to zero after local midnight."],
        ["FR-13, FR-14", "Field test with the cat", "16 of 20 detections correct. No second meal inside 30 minutes."],
        ["FR-16", "Level comparison", "Reported percentage within 10 points of the measured fill at three known levels."],
        ["FR-17", "Power cycle", "History survives a reboot. Currently fails by design."],
        ["FR-19", "Schedule edit", "Valid table is served back and survives a reboot. A malformed table returns 400."],
        ["NFR-PM-01", "Stopwatch", "Median response under 2 s across 20 requests."],
        ["NFR-RL-02", "Router power cycle", "The device rejoins with no manual action."],
        ["NFR-SEC-01", "Repository inspection", "`secrets.h` is absent from the tree and from history."],
    ], widths=[3.6, 4.2, 8.7])

