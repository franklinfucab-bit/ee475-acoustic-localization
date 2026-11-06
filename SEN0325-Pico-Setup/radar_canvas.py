"""Bearing-only radar display: 0 degrees forward, clockwise positive."""
import math
import tkinter as tk

BG = "#071722"
GRID = "#19434b"
ACCENT = "#42e3b3"
TEXT = "#b7d2da"


def polar_point(cx, cy, radius, angle_deg):
    angle = math.radians(angle_deg)
    return cx + radius * math.sin(angle), cy - radius * math.cos(angle)


class RadarCanvas(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, background=BG, highlightthickness=0, **kwargs)
        self.cx = self.cy = self.radius = 0
        self.front_calibrated=False
        self.state = (None, None, False, "Waiting for bearing")
        self.bind("<Configure>", self.resize)

    def resize(self, event):
        self.cx, self.cy = event.width / 2, event.height / 2 - 4
        self.radius = max(20, min(event.width, event.height) / 2 - 56)
        self.delete("all")
        cx, cy, radius = self.cx, self.cy, self.radius
        for fraction in (0.25, 0.5, 0.75, 1):
            r = radius * fraction
            self.create_oval(cx-r, cy-r, cx+r, cy+r, outline=GRID, width=1)
        for angle in range(0, 360, 30):
            x, y = polar_point(cx, cy, radius, angle)
            self.create_line(cx, cy, x, y, fill=GRID, dash=(3, 5))
            x, y = polar_point(cx, cy, radius + 22, angle)
            cardinal={0:'0° Front',90:'90° Right',180:'180° Rear',270:'270° Left'} if self.front_calibrated else {0:'0° Array ref.',90:'90°',180:'180°',270:'270°'}
            label=cardinal.get(angle,f'{angle}°')
            self.create_text(x, y, text=label, fill=ACCENT if angle % 90 == 0 else TEXT,
                             font=("Segoe UI", 11 if angle % 90 == 0 else 9))
        for angle in range(0, 360, 5):
            outer = polar_point(cx, cy, radius, angle)
            inner = polar_point(cx, cy, radius - (8 if angle % 30 == 0 else 4), angle)
            self.create_line(*inner, *outer, fill="#3a7275")
        # Robot/array at the origin. This is the UI coordinate reference.
        self.create_polygon(cx, cy-18, cx-12, cy+12, cx+12, cy+12,
                            fill="#173e49", outline=ACCENT, width=2)
        self.create_oval(cx-3, cy-3, cx+3, cy+3, fill=ACCENT, outline="")
        self.create_text(16, 16, text="PLANAR BEARING / 360°", anchor="nw", fill=TEXT,
                         font=("Segoe UI", 11))
        self.create_text(event.width / 2, event.height-13,
                         text="Bearing only | Use Set Front to define zero", fill="#789aa5",
                         font=("Segoe UI", 9))
        self.render(*self.state, force=True)

    def render(self, angle=None, confidence=None, demo=False, message="Waiting for bearing", force=False):
        state = (angle, confidence, demo, message)
        if not force and state == self.state:
            return
        self.state = state
        self.delete("target")
        cx, cy, radius = self.cx, self.cy, self.radius
        if angle is None:
            self.create_text(cx, cy+53, text=message, fill="#85aab6", tags="target",
                             font=("Segoe UI", 13))
            self.create_text(cx, cy+77, text="Play the selected beacon and start radar", fill="#587e8b", tags="target",
                             font=("Segoe UI", 10))
            return
        color = "#ffbb61" if demo else ACCENT
        start = polar_point(cx, cy, 24, angle)
        endpoint = polar_point(cx, cy, radius * 0.76, angle)
        self.create_line(*start, *endpoint, arrow=tk.LAST, arrowshape=(14, 18, 7),
                         fill=color, width=3, tags="target")
        x, y = endpoint
        self.create_oval(x-14, y-14, x+14, y+14, outline=color, width=2, tags="target")
        self.create_oval(x-4, y-4, x+4, y+4, fill=color, outline="", tags="target")
        text = f"{'Simulated bearing' if demo else 'Estimated bearing' if self.front_calibrated else 'Array reference bearing'} {angle:.1f}°"
        self.create_text(cx, 49, text=text, fill=color, tags="target",
                         font=("Segoe UI", 14, "bold"))
        if demo:
            self.create_text(cx, cy+59, text="SIMULATED DATA", fill=color, tags="target",
                             font=("Segoe UI", 13, "bold"))


class DirectionState:
    """A valid DOA estimate is fresh for 1.5 seconds; levels never set a bearing."""
    def __init__(self,transition_seconds=0):
        self.angle = None
        self.confidence = None
        self.updated = 0
        self.transition_seconds=transition_seconds
        self.visual_from=None

    def update(self, packet, now):
        previous,_=self.current(now)
        if not packet["valid"]:
            if packet.get("drop"):
                self.angle = None
                self.confidence = None
                self.visual_from=None
            return
        self.angle = packet["angle_deg"] % 360
        self.visual_from=previous if previous is not None else self.angle
        self.confidence = packet["confidence"]
        self.updated = now

    def current(self, now):
        if self.angle is not None and now - self.updated <= 1.5:
            if self.transition_seconds>0 and self.visual_from is not None:
                progress=max(0,min(1,(now-self.updated)/self.transition_seconds))
                progress=progress*progress*(3-2*progress)
                delta=(self.angle-self.visual_from+180)%360-180
                return (self.visual_from+delta*progress)%360,self.confidence
            return self.angle, self.confidence
        return None, None
