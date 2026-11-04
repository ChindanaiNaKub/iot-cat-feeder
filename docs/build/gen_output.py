"""Build Part IV, Output and Discussion, for the report volume.

The chapter reports the device as built and the measurements taken from it. The
measured column is left blank until the test record exists: no value is written
here that was not observed on the hardware.
"""

import pathlib

from docx_common import figure, h1, h2, para, bullets, numbered, table

EVIDENCE = pathlib.Path(__file__).parent.parent / "evidence"


def write_body(doc, counter):
    # ---------------------------------------------------------------- chapter 1
    h1(doc, 1, "The Delivered System")

    para(doc, "This part reports the device as it exists on the bench and the measurements taken from it. The "
              "earlier parts describe what the device shall do. This part records what was observed.")

    h2(doc, "1.1", "Hardware on the bench")
    table(doc, counter, "Assembled hardware", ["Part", "Role", "Connection"], [
        ["NodeMCU v3 (ESP8266)", "Controller and web server",
         "micro USB for flashing, VIN from the powerbank in use"],
        ["Servo SG90", "Drives the flap", "Signal D5, GPIO14. Supply from VIN, not 3V3."],
        ["Capacitor 470 uF", "Absorbs servo inrush", "Across 5 V and ground at the servo connector"],
        ["HC-SR04P, presence", "Detects the cat near the bowl", "Trig D6, echo D7 through the divider"],
        ["HC-SR04P, level", "Measures hopper depth", "Trig D1, echo D2 through a second divider"],
        ["Resistors 2.2k and 3.3k", "Brings the 5 V echo to 3.00 V", "2.2k in series, 3.3k to ground"],
        ["Powerbank 5 V 2 A", "Runs the device with no host computer", "VIN and the servo supply"],
        ["Cardboard hopper and bowl", "Holds and catches the food", "Cut and taped to the servo bracket"],
        ["Phone browser", "Dashboard", "Same Wi-Fi network as the device"],
    ], widths=[4.4, 5.4, 6.7])

    h2(doc, "1.2", "Firmware behaviour as delivered")
    bullets(doc, [
        "Every feeding path calls `feed(source)`. The button, the scheduler, and the presence detector all "
        "enter through the same function, so the daily count and the safety rules cannot diverge.",
        "The flap closes from `millis()` in the main loop after `OPEN_MS`. It does not close from the network "
        "callback, so a client that disconnects mid-request cannot leave the flap open.",
        "The schedule is read from network time and is ignored until the clock is valid. A minute key "
        "suppresses a second meal inside the same calendar minute.",
        "The three meal times are editable from the dashboard and stored in EEPROM, so a new schedule "
        "survives a power cut without a reflash.",
        "Presence needs three consecutive readings inside the range before a meal is dispensed. A cooldown and "
        "a daily cap bound how often the cat can trigger a meal.",
        "Hopper level is the median of the last five samples, mapped between an empty and a full "
        "depth captured on the dashboard. The sensor mount defeats it, as Section 11.4 explains.",
        "The dashboard is one response compiled into the binary. It refreshes every two seconds and has no "
        "external asset, so it works with no internet connection.",
    ])

    h2(doc, "1.3", "Configuration in the delivered firmware")
    table(doc, counter, "Firmware constants", ["Parameter", "Value", "Name in the source"], [
        ["Flap closed angle", "0 degrees", "`CLOSED_DEG`"],
        ["Flap open angle", "135 degrees", "`OPEN_DEG`"],
        ["Flap dwell before the close", "900 ms", "`OPEN_MS`"],
        ["Scheduled meals", "08:00, 13:00, 18:00, editable", "`DEFAULT_SCHEDULE`"],
        ["Presence range", "60 cm", "`NEAR_CM`"],
        ["Presence cooldown", "30 minutes", "`COOLDOWN_MS`"],
        ["Presence daily cap", "6 meals", "`PRESENCE_CAP`"],
        ["History depth", "5 meals", "`HISTORY_N`"],
        ["Hopper span", "4 cm full, 18 cm empty", "`LEVEL_FULL_CM`, `LEVEL_EMPTY_CM`"],
        ["Dashboard refresh", "2 s", "Dashboard script"],
        ["Echo divider ratio", "5 x 3.3 / (2.2 + 3.3) = 3.00 V", "Wiring page"],
    ], widths=[4.8, 5.4, 6.3])

    # ---------------------------------------------------------------- chapter 2
    h1(doc, 2, "Test Results")

    h2(doc, "2.1", "Procedure")
    para(doc, "Every test ran on the assembled device with the powerbank as the only supply. The feeding button "
              "was pressed ten times with five seconds between presses, and every open and every close was "
              "watched at the flap rather than inferred from the log. The schedule was tested by setting the "
              "next meal one minute ahead, leaving the device undisturbed, and watching the flap at the "
              "appointed minute. The portion trial dispensed three meals at the configured dwell, thirty "
              "seconds apart, and counted the pieces that fell into the bowl. The presence and level tests "
              "were not run. Section 10.3 states the reason for each.")
    para(doc, "The design document defines the test cases and the pass condition for each. This chapter "
              "records the measured value for those cases.")

    h2(doc, "2.2", "Measured results")
    para(doc, "The pass condition for each row is stated in the test plan of Part III.")
    table(doc, counter, "Measured results", ["Criterion", "Test", "Measured", "Unit"], [
        ["Manual presses completed", "TC-03", "10", "presses"],
        ["Automatic closes", "TC-03", "10", "of 10"],
        ["Closes that exceeded 3 s", "TC-03", "0", "count"],
        ["Scheduled meals fired", "TC-04", "3", "of 3"],
        ["Schedule drift", "TC-04", "0", "minutes"],
        ["Open angle commanded", "Servo test", "135", "degrees"],
        ["Pieces per meal, mean", "Portion trial", "22.0", "pieces"],
        ["Pieces per meal, range", "Portion trial", "18 to 25", "pieces"],
        ["Reboots during the tests", "All", "0", "count"],
    ], widths=[5.6, 2.6, 4.2, 4.1])

    h2(doc, "2.3", "Tests not run")
    table(doc, counter, "Tests not run and the reason", ["Criterion", "Reason"], [
        ["Flap open latency, mean (TC-02)",
         "The open was observed on every press but not timed with a stopwatch, so no figure is claimed."],
        ["Presence decisions correct (TC-09)",
         "No acceptance walk was run. The dashboard received a 9 cm reading during setup, which shows the "
         "sensor path is live but does not measure detection accuracy."],
        ["Level with a full hopper (TC-10)",
         "The beam lands on the box floor instead of the grain, so the reading does not follow the fill. "
         "Section 11.4 describes the fault."],
        ["Level with an empty hopper (TC-10)", "Same fault as the row above."],
    ], widths=[6.0, 11.5])

    h2(doc, "2.4", "Photos and Evidence")
    para(doc, "The photographs below record the device as built and running on the powerbank, with no host "
              "computer attached.")
    figure(doc, counter, str(EVIDENCE / "04.jpg"),
           "The assembled feeder: cardboard hopper, flap at the outlet, and dry food in the bowl.",
           width_cm=8.5)
    figure(doc, counter, str(EVIDENCE / "01.jpg"),
           "Inside the enclosure, from above: controller, wiring, servo linkage, and bowl.", width_cm=14.0)
    figure(doc, counter, str(EVIDENCE / "05.jpg"),
           "The flap pivot where it passes through the hopper wall, seen from above the open hopper.",
           width_cm=14.0)
    figure(doc, counter, str(EVIDENCE / "06.jpg"),
           "The hopper chute with dry food resting in it, looking down past the cardboard baffles.",
           width_cm=9.0)
    figure(doc, counter, str(EVIDENCE / "02.jpg"),
           "The open enclosure with the power cable leaving the box for the powerbank.", width_cm=8.5)
    figure(doc, counter, str(EVIDENCE / "03.jpg"),
           "An ultrasonic sensor on its cardboard bracket above the hopper opening.", width_cm=8.5)
    figure(doc, counter, str(EVIDENCE / "website-desktop.png"),
           "The dashboard served by the device: flap state, daily count, hopper level, cat range, "
           "schedule, and meal log.", width_cm=8.0)

    # ---------------------------------------------------------------- chapter 3
    h1(doc, 3, "Discussion")

    h2(doc, "3.1", "Clock and schedule")
    para(doc, "The schedule is only evaluated after the clock is valid, which removes the class of fault where "
              "the device boots at an arbitrary time and immediately believes a meal is due. The minute key "
              "makes the scheduler idempotent inside one minute, so a slow pass through the loop, a clock "
              "resync, or a second evaluation cannot double feed. The residual error is bounded by the network "
              "time query and by the one minute resolution of the schedule. In the test the three configured "
              "times each produced one meal, with no second meal inside the same minute and no measurable "
              "drift against the minute that was set.")

    h2(doc, "3.2", "Flap safety")
    para(doc, "The close condition lives in the main loop and depends only on `millis()`, so it survives a "
              "dropped client, a blocked socket, and a browser that closes the page mid-request. This was a "
              "deliberate inversion of the obvious design, where the request handler opens the flap and then "
              "closes it after a delay. The loop version also keeps the HTTP server responsive during the "
              "open interval, because nothing blocks. Ten consecutive presses five seconds apart produced ten "
              "closes and no stranded flap, which is the failure this design exists to prevent.")

    h2(doc, "3.3", "Presence detection")
    para(doc, "Two filters stand between the sensor and a meal. The median of five samples rejects a single "
              "bad echo, which is common when the beam grazes a moving cat. Three consecutive readings inside "
              "the range reject a transient, such as a hand crossing the beam during setup. The cooldown and "
              "the daily cap bound the cost of a false positive to one meal, which is the failure the owner "
              "would notice least.")

    h2(doc, "3.4", "Hopper level")
    para(doc, "The level reading is a distance, not a mass, and the surface of dry food is not flat. The "
              "median filter removes the worst of the scatter, and the percentage is mapped between an empty "
              "and a full depth captured from the dashboard rather than assumed. A percentage would therefore "
              "be a coarse signal. It answers whether the owner needs to refill, not how many meals remain.")
    para(doc, "On the assembled unit the sensor does not deliver that signal. It was fixed in place before its "
              "aim was checked, and when the glue set the beam landed on the floor of the box instead of the "
              "hopper. The reading stays at the depth of that floor whatever is poured in, and no pair of "
              "captured depths turns it into a level. The paragraph above describes the design, not a measured "
              "result. Moving the mount is the whole of the remaining work, because the firmware path exists "
              "and takes its two end points from the dashboard.")

    h2(doc, "3.5", "The portion control decision")
    para(doc, "Portion control by weight was in the original scope and left it on 2 November. The header pins "
              "of the amplifier module were never soldered, and soldering, calibrating, and testing the load "
              "cell did not fit in the two days that remained after the sensors were integrated. The feature "
              "was removed from the version rather than carried half-connected, and the work that depended on "
              "it moved to Future Work. The schedule test took the freed day.")
    para(doc, "The cost of the decision is stated plainly. Portion size is still set by the flap dwell, so a "
              "change in food size or flow rate changes the meal size. The design keeps the seam for the "
              "closed loop, because every feeding path already passes through `feed(source)` and the timeout "
              "that would guard a mass-controlled close is the timer that is already running.")
    para(doc, "Three consecutive cycles at the same dwell produced 18, 25, and 23 pieces, a mean of 22. Against "
              "the 15 percent window the requirement sets, the upper two cycles sit inside it and the lowest "
              "sits outside, 18 percent below the mean. A spread that size is not a margin an owner can rely "
              "on, and it cannot be tuned away. The two candidates are bridging in the hopper and the head of "
              "food pressing on the flap, and the firmware measures neither, so the report does not attribute "
              "the spread to one of them. The result is the argument for closing the loop rather than tuning the "
              "dwell, because no single dwell compensates for a variable the controller cannot see.")

    h2(doc, "3.6", "Defects found and fixed")
    bullets(doc, [
        "**Brownout during the flap cycle.** With the servo supplied from the notebook port, the board reset "
        "whenever the servo started. The stall current pulled the rail below the regulator dropout. A "
        "powerbank with a higher current limit and a 470 uF capacitor at the servo connector fixed it. The "
        "bring-up sketch reproduces the fault without the rest of the firmware.",
        "**Five volt echo into a 3.3 V input.** The first divider used 1k and 2k, which gives 3.33 V, inside "
        "the pin limit but without margin. It was replaced with 2.2k and 3.3k, which gives 3.00 V and is clear "
        "of the input threshold with resistors that were on hand.",
        "**Truncated status JSON.** The status response formatted its header into a 64 byte buffer before "
        "appending the history array. The formatted fragment was longer than the buffer, so the tail was cut "
        "and the response was malformed. The buffer was raised to 96 bytes and the write now checks the return "
        "value of the formatter and reports an overflow instead of truncating silently.",
        "**Servo travel.** A sweep of the horn showed the flap reaches full open before the nominal end of "
        "travel. The open angle was set just below the measured stop, which keeps the servo from stalling "
        "against the hopper wall for the whole open interval.",
    ])

    h2(doc, "3.7", "Limitations and threats to validity")
    bullets(doc, [
        "The history lives in RAM. A reboot clears the daily count, so a test that spans a reboot undercounts.",
        "The portion is reported as a count of pieces, not a mass, because no scale was available. The count "
        "measures consistency but cannot be converted to grams without knowing the mean piece weight.",
        "The portion trial is three cycles from one hopper fill, so the spread is indicative rather than a "
        "distribution.",
        "The schedule test measures one device in one room. A different access point changes the time source "
        "and therefore the drift.",
        "Presence accuracy is not measured. The only reading taken was 9 cm during setup, which is short of "
        "the 60 cm the requirement names and is not a detection trial.",
        "The level sensor is mounted where its beam misses the hopper, so the level test was not run and no "
        "percentage is reported. The mount is the only thing between the design and a working gauge.",
        "There is no authentication. Any client on the same network can dispense a meal.",
    ])
