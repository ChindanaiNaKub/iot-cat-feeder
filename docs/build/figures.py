"""Generate the diagrams the reports embed. Rerun to regenerate every PNG."""

import pathlib

from graphviz import Digraph

HERE = pathlib.Path(__file__).parent
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)

FONT = "Carlito"
BOX = dict(shape="box", style="rounded,filled", fillcolor="#FFFFFF", color="#4F81BD", fontname=FONT,
           fontsize="10", penwidth="1.2", margin="0.18,0.10")
ACCENT = dict(shape="box", style="rounded,filled", fillcolor="#DCE6F2", color="#2F5597", fontname=FONT,
              fontsize="10", penwidth="1.4")
ACTOR = dict(shape="box", style="filled", fillcolor="#F2F2F2", color="#808080", fontname=FONT,
             fontsize="10", margin="0.16,0.08")
PLANNED = dict(shape="box", style="rounded,dashed,filled", fillcolor="#FFFFFF", color="#A6A6A6",
               fontname=FONT, fontsize="10", margin="0.18,0.10", fontcolor="#595959")
EDGE = dict(fontname=FONT, fontsize="8.5", color="#404040")


def render(graph, name):
    path = OUT / name
    graph.attr(dpi="190", bgcolor="white", pad="0.15")
    graph.render(filename=str(path), format="png", cleanup=True)
    return str(path) + ".png"


def context():
    g = Digraph("context")
    g.attr(rankdir="LR", nodesep="0.45", ranksep="0.9")
    g.node("owner", "Cat owner\nmobile browser", **ACTOR)
    g.node("cat", "Cat", **ACTOR)
    g.node("power", "Powerbank\n5 V, 2 A", **ACTOR)
    g.node("ntp", "NTP server\npool.ntp.org", **ACTOR)
    g.node("feeder", "IoT Cat Feeder\nNodeMCU v3 (ESP8266)\nWi-Fi access point client", **ACCENT)
    g.node("servo", "Servo SG90\nflap actuator", **BOX)
    g.node("hopper", "Hopper and bowl\ncardboard, gravity fed", **BOX)

    g.edge("owner", "feeder", label="HTTP over Wi-Fi", **EDGE)
    g.edge("feeder", "servo", label="PWM  50 Hz", **EDGE)
    g.edge("servo", "hopper", label="opens flap", **EDGE)
    g.edge("cat", "feeder", label="ultrasonic\nrange (planned)", style="dashed", **EDGE)
    g.edge("feeder", "ntp", label="SNTP query", style="dashed", **EDGE)
    g.edge("power", "feeder", label="5 V supply", **EDGE)
    g.edge("power", "servo", label="5 V, 470 uF bulk", **EDGE)
    return render(g, "context")


def components():
    g = Digraph("components")
    g.attr(rankdir="TB", nodesep="0.35", ranksep="0.55", compound="true")

    with g.subgraph(name="cluster_esp") as esp:
        esp.attr(label="NodeMCU v3 firmware  (feeder.ino)", fontname=FONT, fontsize="10",
                 color="#2F5597", style="rounded", penwidth="1.2")
        esp.node("ui", "Web UI\nPAGE in PROGMEM", **BOX)
        esp.node("http", "HTTP server\n/, /status, /feed", **BOX)
        esp.node("sched", "Scheduler\ncheckSchedule()", **BOX)
        esp.node("feed", "feed(source)\nsingle actuation gate", **ACCENT)
        esp.node("state", "Feeder state\nstruct Feeder", **BOX)
        esp.node("wifi", "Wi-Fi manager\nkeepWifi()", **BOX)
        esp.node("ntp", "Time client\nconfigTime()", **BOX)
        esp.node("sensor", "Sensor driver\nmedian filter (planned)", **PLANNED)

    g.node("browser", "Mobile browser", **ACTOR)
    g.node("servo", "Servo SG90", **BOX)
    g.node("ultra", "HC-SR04 x2\n(planned)", **PLANNED)
    g.node("ntpsrv", "NTP server", **ACTOR)

    g.edge("browser", "ui", label="GET /", **EDGE)
    g.edge("browser", "http", label="/status, /feed", **EDGE)
    g.edge("ui", "http", style="invis")
    g.edge("http", "feed", label="POST /feed", **EDGE)
    g.edge("http", "state", label="read", style="dashed", **EDGE)
    g.edge("sched", "feed", label="hour match", **EDGE)
    g.edge("sensor", "feed", label="cat near", **EDGE)
    g.edge("feed", "servo", label="write(135)", **EDGE)
    g.edge("feed", "state", label="markFeed", **EDGE)
    g.edge("state", "http", label="statusJson", style="dashed", **EDGE)
    g.edge("ntp", "sched", label="time_t", style="dashed", **EDGE)
    g.edge("ntpsrv", "ntp", **EDGE)
    g.edge("wifi", "http", style="invis")
    g.edge("ultra", "sensor", **EDGE)
    return render(g, "components")


def state():
    g = Digraph("state")
    g.attr(rankdir="LR", nodesep="0.5", ranksep="1.0")
    g.node("start", "", shape="circle", width="0.18", style="filled", fillcolor="#404040")
    g.node("idle", "IDLE\nflap shut, servo at 0 deg", **ACCENT)
    g.node("open", "FEEDING\nflap open, servo at 135 deg", **ACCENT)
    g.node("cooldown", "COOLDOWN\nno feed for 30 min (planned)", **PLANNED)

    g.edge("start", "idle", **EDGE)
    g.edge("idle", "open", label="feed(source)\nmanual or scheduled", **EDGE)
    g.edge("open", "idle", label="900 ms elapsed\nauto close", **EDGE)
    g.edge("open", "cooldown", label="cat-mode feed done\n(planned)", style="dashed", **EDGE)
    g.edge("cooldown", "idle", label="timer expired\n(planned)", style="dashed", **EDGE)
    g.edge("idle", "open", label="cat within 60 cm\n(planned)", style="dashed",
           constraint="false", **EDGE)
    return render(g, "state")


def activity():
    g = Digraph("activity")
    g.attr(rankdir="LR", nodesep="0.35", ranksep="0.45")
    g.node("loop", "loop()", shape="oval", style="filled", fillcolor="#F2F2F2", fontname=FONT,
           fontsize="10", color="#808080")
    g.node("client", "server.handleClient()\nserve pending HTTP request", **BOX)
    g.node("decide", "route", shape="diamond", style="filled", fillcolor="#FFF2CC", color="#BF9000",
           fontname=FONT, fontsize="9.5")
    g.node("mark", "markFeed(source)\ncount, time, source", **BOX)
    g.node("servo", "servo.write(135)", **BOX)
    g.node("guard", "open for 900 ms?", shape="diamond", style="filled", fillcolor="#FFF2CC",
           color="#BF9000", fontname=FONT, fontsize="9.5")
    g.node("close", "closeFlap()\nservo.write(0)", **BOX)
    g.node("sched", "checkSchedule()\nminute key changed?", **BOX)
    g.node("wifi", "keepWifi()\nreconnect every 5 s", **BOX)
    g.node("web", "POST /feed", shape="oval", style="filled", fillcolor="#DCE6F2", fontname=FONT,
           fontsize="9.5", color="#2F5597")
    g.node("timer", "scheduled minute", shape="oval", style="filled", fillcolor="#DCE6F2",
           fontname=FONT, fontsize="9.5", color="#2F5597")

    g.edge("loop", "client", **EDGE)
    g.edge("client", "decide", **EDGE)
    g.edge("web", "decide", **EDGE)
    g.edge("timer", "decide", **EDGE)
    g.edge("decide", "mark", label="feed requested", **EDGE)
    g.edge("mark", "servo", **EDGE)
    g.edge("servo", "guard", **EDGE)
    g.edge("guard", "close", label="yes", **EDGE)
    g.edge("guard", "sched", label="no", **EDGE)
    g.edge("close", "sched", **EDGE)
    g.edge("sched", "wifi", **EDGE)
    g.edge("wifi", "loop", label="next iteration", style="dashed", **EDGE)
    return render(g, "activity")


def usecase():
    g = Digraph("usecase")
    g.attr(rankdir="LR", nodesep="0.12", ranksep="0.6")
    uc = dict(shape="ellipse", style="filled", fillcolor="#FFFFFF", color="#4F81BD", fontname=FONT,
              fontsize="9.5", penwidth="1.2", margin="0.10,0.05")
    ucp = dict(shape="ellipse", style="dashed,filled", fillcolor="#FFFFFF", color="#A6A6A6",
               fontname=FONT, fontsize="9.5", fontcolor="#595959", margin="0.10,0.05")

    g.node("owner", "Cat owner", shape="box", style="filled", fillcolor="#F2F2F2", color="#808080",
           fontname=FONT, fontsize="10")
    g.node("cat", "Cat", shape="box", style="filled", fillcolor="#F2F2F2", color="#808080",
           fontname=FONT, fontsize="10")
    g.node("clock", "System clock\n(NTP)", shape="box", style="filled", fillcolor="#F2F2F2",
           color="#808080", fontname=FONT, fontsize="10")
    g.node("sys", "System", shape="box", style="filled", fillcolor="#F2F2F2", color="#808080",
           fontname=FONT, fontsize="10")

    g.node("uc1", "UC-01\nFeed on demand", **uc)
    g.node("uc2", "UC-02\nReceive scheduled feeding", **uc)
    g.node("uc3", "UC-03\nView status and history", **uc)
    g.node("uc4", "UC-04\nFeed when cat approaches", **ucp)
    g.node("uc5", "UC-05\nRecover from network loss", **uc)

    g.edge("owner", "uc1", **EDGE)
    g.edge("owner", "uc3", **EDGE)
    g.edge("clock", "uc2", **EDGE)
    g.edge("cat", "uc4", style="dashed", **EDGE)
    g.edge("sys", "uc5", **EDGE)
    return render(g, "usecase")


if __name__ == "__main__":
    for builder in (context, components, state, activity, usecase):
        print(builder())
