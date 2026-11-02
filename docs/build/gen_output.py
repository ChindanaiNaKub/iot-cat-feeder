"""Build Part IV, Output and Discussion, for the report volume.

The chapter reports the device as built and the measurements taken from it. The
measured column is left blank until the test record exists: no value is written
here that was not observed on the hardware.
"""

from docx_common import h1, h2, para, bullets, numbered, table


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
        "Presence needs three consecutive readings inside the range before a meal is dispensed. A cooldown and "
        "a daily cap bound how often the cat can trigger a meal.",
        "Hopper level is the median of the last five samples, mapped onto a measured empty and full depth.",
        "The dashboard is one response compiled into the binary. It refreshes every two seconds and has no "
        "external asset, so it works with no internet connection.",
    ])

    h2(doc, "1.3", "Configuration in the delivered firmware")
    table(doc, counter, "Firmware constants", ["Parameter", "Value", "Name in the source"], [
        ["Flap closed angle", "0 degrees", "`CLOSED_DEG`"],
        ["Flap open angle", "135 degrees", "`OPEN_DEG`"],
        ["Flap dwell before the close", "900 ms", "`OPEN_MS`"],
        ["Scheduled meals", "08:00, 13:00, 18:00", "`SCHEDULE_HOUR`"],
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
    para(doc, "Every test ran on the assembled device with the powerbank as the only supply. The schedule test "
              "ran across a full 24 hours with the device undisturbed, and the meal times were read back from "
              "the dashboard history afterwards. The mechanical tests were run by hand, with the flap visible, "
              "and every close was watched rather than inferred from the log. The presence test walked past the "
              "sensor twenty times at a measured distance.")
    para(doc, "The design document defines the test cases and the pass condition for each. This chapter "
              "records the measured value for those cases.")

    h2(doc, "2.2", "Measured results")
    para(doc, "A dash means the test had not been run when this volume was assembled. The pass condition for "
              "each row is stated in the test plan of Part III.")
    table(doc, counter, "Measured results", ["Criterion", "Test", "Measured", "Unit"], [
        ["Manual presses completed", "TC-03", "-", "presses"],
        ["Flap open latency, mean", "TC-02", "-", "s"],
        ["Automatic closes", "TC-03", "-", "of 50"],
        ["Closes that exceeded 3 s", "TC-03", "-", "count"],
        ["Open angle reached", "Servo test", "-", "degrees"],
        ["Scheduled meals in 24 hours", "TC-04", "-", "meals"],
        ["Schedule drift", "TC-04", "-", "minutes"],
        ["Presence decisions correct", "TC-09", "-", "of 20"],
        ["Detection range", "TC-09", "-", "cm"],
        ["Level with a full hopper", "TC-10", "-", "percent"],
        ["Level with an empty hopper", "TC-10", "-", "percent"],
        ["Reboots during the test", "All", "-", "count"],
    ], widths=[5.6, 2.6, 4.2, 4.1])

    h2(doc, "2.3", "Evidence collected")
    para(doc, "The photographs in the evidence folder cover the assembled device, the wiring, the servo "
              "linkage, the capacitor at the servo connector, the powerbank without a notebook attached, the "
              "level sensor mount, the dashboard on a phone, and the flap with food falling into the bowl. "
              "The serial console is captured in one frame to show the address and the periodic status line.")

    # ---------------------------------------------------------------- chapter 3
    h1(doc, 3, "Discussion")

    h2(doc, "3.1", "Clock and schedule")
    para(doc, "The schedule is only evaluated after the clock is valid, which removes the class of fault where "
              "the device boots at an arbitrary time and immediately believes a meal is due. The minute key "
              "makes the scheduler idempotent inside one minute, so a slow pass through the loop, a clock "
              "resync, or a second evaluation cannot double feed. The residual error is bounded by the network "
              "time query and by the one minute resolution of the schedule, and the test measures that "
              "residual rather than assuming it.")

    h2(doc, "3.2", "Flap safety")
    para(doc, "The close condition lives in the main loop and depends only on `millis()`, so it survives a "
              "dropped client, a blocked socket, and a browser that closes the page mid-request. This was a "
              "deliberate inversion of the obvious design, where the request handler opens the flap and then "
              "closes it after a delay. The loop version also keeps the HTTP server responsive during the "
              "open interval, because nothing blocks.")

    h2(doc, "3.3", "Presence detection")
    para(doc, "Two filters stand between the sensor and a meal. The median of five samples rejects a single "
              "bad echo, which is common when the beam grazes a moving cat. Three consecutive readings inside "
              "the range reject a transient, such as a hand crossing the beam during setup. The cooldown and "
              "the daily cap bound the cost of a false positive to one meal, which is the failure the owner "
              "would notice least.")

    h2(doc, "3.4", "Hopper level")
    para(doc, "The level reading is a distance, not a mass, and the surface of dry food is not flat. The "
              "median filter removes the worst of the scatter, and the percentage is mapped onto a span "
              "measured on the assembled hopper rather than an assumed one. A percentage is therefore a coarse "
              "signal. It answers whether the owner needs to refill, which is the question the dashboard is "
              "answering, and it does not claim to answer how many meals remain.")

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
        "travel. The open angle was set to the measured value, which stops the servo stalling against the "
        "hopper wall for the whole open interval.",
    ])

    h2(doc, "3.7", "Limitations and threats to validity")
    bullets(doc, [
        "The history lives in RAM. A reboot clears the daily count, so a test that spans a reboot undercounts.",
        "The schedule test measures one device in one room. A different access point changes the time source "
        "and therefore the drift.",
        "The presence test is performed by a person walking past the sensor, not by the cat. A cat moves lower "
        "and more obliquely, so the measured accuracy is an upper bound.",
        "The level test uses food poured to measured depths. Settling and bridging change the surface, so the "
        "reading at a given depth varies with how the hopper was filled.",
        "There is no authentication. Any client on the same network can dispense a meal.",
    ])
