"""Build the four modular-architecture diagrams as self-contained HTML files.

Usage: python3 docs/diagrams/build.py docs/diagrams
"""
import sys
from pathlib import Path

OUT = Path(sys.argv[1])

PAPER = "#f5f5f5"
INK = "#2d3142"
MUTED = "#4f5d75"
SOFT = "#5a6580"
ACCENT = "#bf4520"
ACCENT_TINT = "rgba(191,69,32,0.08)"
LINK = "#2e5aa8"
SANS = "'Geist', system-ui, sans-serif"
MONO = "'Geist Mono', ui-monospace, monospace"
SERIF = "'Instrument Serif', 'Noto Serif', serif"


def ink(a):
    return f"rgba(45,49,66,{a})"


HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&family=Noto+Serif:ital@0;1&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --color-paper:   #f5f5f5;
      --color-ink:     #2d3142;
      --color-muted:   #4f5d75;
      --color-accent:  #bf4520;
      --font-sans:     'Geist', system-ui, sans-serif;
      --font-serif:    'Instrument Serif', 'Noto Serif', serif;
      --font-mono:     'Geist Mono', ui-monospace, monospace;
    }}
    body {{
      font-family: var(--font-sans);
      background: var(--color-paper);
      color: var(--color-ink);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 3rem 2rem;
    }}
    .frame {{ max-width: 1200px; width: 100%; }}
    .diagram-container {{ width: 100%; overflow-x: auto; }}
    .eyebrow {{
      font-family: var(--font-mono);
      font-size: 0.66rem;
      font-weight: 500;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--color-muted);
      margin-bottom: 0.5rem;
    }}
    h1 {{
      font-family: var(--font-serif);
      font-size: clamp(1.5rem, 2.4vw + 0.75rem, 2rem);
      font-weight: 400;
      letter-spacing: -0.02em;
      line-height: 1.15;
      color: var(--color-ink);
      margin-bottom: 1.5rem;
    }}
    svg {{ width: 100%; min-width: 960px; display: block; }}
    @media print {{
      .diagram-container {{ overflow-x: visible; }}
      svg {{ min-width: 0; }}
    }}
  </style>
</head>
<body>
  <div class="frame">
    <p class="eyebrow">{eyebrow}</p>
    <h1>{title}</h1>
    <div class="diagram-container">
      <svg viewBox="0 0 960 600" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{slug}-title {slug}-desc">
        <title id="{slug}-title">{title}</title>
        <desc id="{slug}-desc">{desc}</desc>
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#4f5d75"/></marker>
          <marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#bf4520"/></marker>
          <marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#2e5aa8"/></marker>
          <marker id="arrow-open" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polyline points="0 0, 8 3, 0 6" fill="none" stroke="#4f5d75" stroke-width="1.2"/></marker>
        </defs>
        <rect width="100%" height="100%" fill="#f5f5f5"/>
{body}
      </svg>
    </div>
  </div>
</body>
</html>
"""


# ---------- primitives ----------

def node(x, y, w, h, name, sub=None, tag=None, kind="backend", tag_w=None):
    fill, stroke, dash = {
        "backend": ("#ffffff", INK, None),
        "focal": (ACCENT_TINT, ACCENT, None),
        "store": (ink(0.05), MUTED, None),
        "input": ("rgba(79,93,117,0.10)", SOFT, None),
    }[kind]
    cx = x + w / 2
    cy = y + h / 2
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PAPER}"/>',
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>']
    if tag:
        tw = tag_w or max(28, round((len(tag) * 5.2 + 8) / 4) * 4)
        tc = ACCENT if kind == "focal" else MUTED
        out.append(f'<rect x="{x+8}" y="{y+6}" width="{tw}" height="12" rx="2" fill="none" stroke="{tc}" stroke-opacity="0.5" stroke-width="0.8"/>')
        out.append(f'<text x="{x+8+tw/2:g}" y="{y+15}" fill="{tc}" font-size="7" font-family="{MONO}" text-anchor="middle" letter-spacing="0.08em">{tag}</text>')
    ny = cy + (6 if sub is None else 0) + (4 if tag else 0)
    out.append(f'<text x="{cx:g}" y="{ny:g}" fill="{INK}" font-size="12" font-weight="600" font-family="{SANS}" text-anchor="middle">{name}</text>')
    if sub:
        out.append(f'<text x="{cx:g}" y="{ny+15:g}" fill="{MUTED}" font-size="9" font-family="{MONO}" text-anchor="middle">{sub}</text>')
    return "\n".join(out)


def label(cx, y_mask, text, w=None, color=SOFT):
    """Arrow label: opaque mask (12px tall, top at y_mask) + centred mono text."""
    w = w or round((len(text) * 5.5 + 8) / 4) * 4
    return (f'<rect x="{cx - w/2:g}" y="{y_mask}" width="{w}" height="12" rx="2" fill="{PAPER}"/>\n'
            f'<text x="{cx:g}" y="{y_mask+9}" fill="{color}" font-size="8" font-family="{MONO}" text-anchor="middle" letter-spacing="0.06em">{text}</text>')


def line(x1, y1, x2, y2, kind="muted", dashed=False, marker=True):
    stroke, mk = {"muted": (MUTED, "arrow"), "accent": (ACCENT, "arrow-accent"), "open": (MUTED, "arrow-open")}[kind]
    d = ' stroke-dasharray="5,4"' if dashed else ""
    m = f' marker-end="url(#{mk})"' if marker else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="1.2"{d}{m}/>'


def path(d, kind="muted", dashed=False, marker=True):
    stroke, mk = {"muted": (MUTED, "arrow"), "accent": (ACCENT, "arrow-accent")}[kind]
    ds = ' stroke-dasharray="5,4"' if dashed else ""
    m = f' marker-end="url(#{mk})"' if marker else ""
    return f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="1.2"{ds}{m}/>'


def callout(tx, ty, text, leader, dot, anchor="end"):
    return (f'<text x="{tx}" y="{ty}" fill="{INK}" font-size="14" font-style="italic" font-family="{SERIF}" text-anchor="{anchor}">{text}</text>\n'
            f'<path d="{leader}" fill="none" stroke="{ink(0.40)}" stroke-width="1" stroke-dasharray="4,3"/>\n'
            f'<circle cx="{dot[0]}" cy="{dot[1]}" r="2" fill="{INK}"/>')


def legend(y, title, items):
    """items: list of (x, swatch_svg, text). Swatch drawn at row y."""
    out = [f'<line x1="40" y1="{y}" x2="920" y2="{y}" stroke="{ink(0.10)}" stroke-width="0.8"/>',
           f'<text x="40" y="{y+20}" fill="{MUTED}" font-size="8" font-family="{MONO}" letter-spacing="0.18em">{title}</text>']
    for x, sw, text in items:
        out.append(sw)
        out.append(f'<text x="{x}" y="{y+44}" fill="{MUTED}" font-size="8.5" font-family="{SANS}">{text}</text>')
    return "\n".join(out)


def sw_box(x, y, fill, stroke, rx=2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x}" y="{y}" width="24" height="12" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1"{d}/>'


def page(slug, eyebrow, title, desc, body):
    (OUT / f"{slug}.html").write_text(HEAD.format(slug=slug, eyebrow=eyebrow, title=title, desc=desc,
                                                  body="\n".join("        " + l for l in body.splitlines())))


# ================= A. Module anatomy =================
def module_anatomy():
    b = []
    # zone: the people module
    b.append(f'<rect x="40" y="136" width="880" height="232" rx="8" fill="{ink(0.02)}" stroke="{ink(0.10)}" stroke-width="0.8"/>')
    b.append(f'<rect x="52" y="140" width="196" height="12" rx="2" fill="{PAPER}"/>')
    b.append(f'<text x="150" y="149" fill="{SOFT}" font-size="7" font-family="{MONO}" text-anchor="middle" letter-spacing="0.14em">PEOPLE/ · IMPORTS POINT DOWN ONLY</text>')
    # arrows
    b.append(line(352, 96, 352, 168, "accent"))
    b.append(label(312, 110, "FACADE CALL", 64, ACCENT))
    b.append(line(352, 224, 352, 280))
    b.append(label(316, 246, "DELEGATES", 56))
    b.append(line(224, 308, 272, 308))
    b.append(line(432, 308, 480, 308))
    b.append(line(640, 308, 688, 308))
    b.append(line(352, 336, 352, 432))
    b.append(label(312, 380, "FACADE CALL", 64))
    b.append(line(560, 336, 560, 432, dashed=True))
    b.append(label(604, 380, "READS MODELS", 72))
    # nodes
    b.append(node(272, 40, 160, 56, "billing", "a higher module", tag="ABOVE"))
    b.append(node(272, 168, 160, 56, "Facade", "people/__init__.py", tag="FACADE", kind="focal"))
    b.append(node(688, 168, 176, 56, "schemas", "DTOs · used by every layer", kind="store"))
    b.append(node(64, 280, 160, 56, "api", "routers · HTTP schemas"))
    b.append(node(272, 280, 160, 56, "services", "use cases"))
    b.append(node(480, 280, 160, 56, "repositories", "queries · no rules"))
    b.append(node(688, 280, 176, 56, "models", "ORM · own tables"))
    b.append(node(296, 432, 320, 56, "identity", "bottom module · provision_login()", tag="BELOW"))
    # callout
    b.append(callout(656, 484, "writes to its tables go through its facade",
                     "M 650,478 Q 630,476 620,468", (616, 466), anchor="start"))
    # legend
    y = 524
    b.append(legend(y, "LEGEND", [
        (72, sw_box(40, y + 34, ACCENT_TINT, ACCENT), "Facade: the only way in"),
        (232, sw_box(200, y + 34, "#ffffff", INK), "Module or layer"),
        (368, sw_box(336, y + 34, ink(0.05), MUTED), "Shared DTOs"),
        (504, line(468, y + 40, 496, y + 40), "Import or call (downward)"),
        (680, line(644, y + 40, 672, y + 40, dashed=True), "Reads another module's models"),
    ]))
    page("module-anatomy", "Architecture · decisions D1, D2, D4, D5",
         "One module, behind its facade",
         "Architecture of one module, people, showing its api, services, repositories and models layers importing downward, "
         "its facade as the only entry for the higher billing module, and its own calls into the lower identity module "
         "through that module's facade while reading identity's models directly.",
         "\n".join(b))


# ================= B. Skill workflow =================
def oval(x, y, w, h, text):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{PAPER}"/>\n'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{ink(0.03)}" stroke="{ink(0.30)}" stroke-width="1"/>\n'
            f'<text x="{x+w/2:g}" y="{y+h/2+4:g}" fill="{INK}" font-size="12" font-weight="600" font-family="{SANS}" text-anchor="middle">{text}</text>')


def diamond(cx, cy, hw, hh, lines):
    out = [f'<polygon points="{cx},{cy-hh} {cx+hw},{cy} {cx},{cy+hh} {cx-hw},{cy}" fill="#ffffff" stroke="{INK}" stroke-width="1"/>']
    y0 = cy + 4 - 7 * (len(lines) - 1)
    for i, t in enumerate(lines):
        out.append(f'<text x="{cx}" y="{y0 + 14*i}" fill="{INK}" font-size="12" font-weight="600" font-family="{SANS}" text-anchor="middle">{t}</text>')
    return "\n".join(out)


def dot(cx, cy):
    return f'<circle cx="{cx}" cy="{cy}" r="4" fill="{INK}"/>'


def skill_workflow():
    b = []
    # arrows
    b.append(line(480, 80, 480, 100))
    b.append(line(576, 140, 640, 140, "accent"))
    b.append(label(608, 120, "NO", 24, ACCENT))
    b.append(line(480, 180, 480, 208, marker=False))
    b.append(label(458, 188, "YES", 28))
    b.append(path("M760,168 V204 Q760,212 752,212 H484", marker=False))
    b.append(line(480, 216, 480, 236))
    b.append(path("M384,276 H248 Q240,276 240,284 V352"))
    b.append(label(312, 256, "NEW MODULE", 60))
    b.append(path("M576,276 H712 Q720,276 720,284 V352"))
    b.append(label(648, 256, "REVIEW A DIFF", 76))
    b.append(line(480, 316, 480, 352))
    b.append(label(520, 328, "LEGACY CODE", 64))
    b.append(path("M240,408 V432 Q240,440 248,440 H476", marker=False))
    b.append(line(480, 408, 480, 436, marker=False))
    b.append(path("M720,408 V432 Q720,440 712,440 H484", marker=False))
    b.append(line(480, 444, 480, 464))
    # nodes
    b.append(oval(380, 40, 200, 40, "Structural task"))
    b.append(diamond(480, 140, 96, 40, ["Skill named in", "agent docs?"]))
    b.append(node(640, 112, 240, 56, "Step 1 · Reconcile", "tier · classify · record ADRs", kind="focal"))
    b.append(dot(480, 212))
    b.append(diamond(480, 276, 96, 40, ["Which task?"]))
    b.append(node(140, 352, 200, 56, "Step 2 · Add a module", "order · layers · enforce"))
    b.append(node(380, 352, 200, 56, "Step 3 · Migrate", "playbook · bottom-up"))
    b.append(node(620, 352, 200, 56, "Step 4 · Review a diff", "a verdict per rule"))
    b.append(dot(480, 440))
    b.append(oval(360, 464, 240, 40, "Done-when criteria met"))
    # callouts
    b.append(callout(904, 64, "light tier: no facades, order or enforcement tests",
                     "M 800,72 Q 792,92 784,112", (784, 112)))
    b.append(callout(632, 508, "bugs met on the way: fixed, or pinned and filed",
                     "M 628,500 Q 610,496 602,486", (600, 484), anchor="start"))
    # legend
    y = 524
    b.append(legend(y, "LEGEND · SHAPE CARRIES TYPE", [
        (72, f'<rect x="40" y="{y+34}" width="24" height="12" rx="6" fill="{ink(0.03)}" stroke="{ink(0.30)}" stroke-width="1"/>', "Start / end"),
        (212, f'<polygon points="180,{y+40} 192,{y+34} 204,{y+40} 192,{y+46}" fill="#ffffff" stroke="{INK}" stroke-width="1"/>', "Decision"),
        (340, sw_box(308, y + 34, "#ffffff", INK), "Step in SKILL.md"),
        (500, sw_box(468, y + 34, ACCENT_TINT, ACCENT), "First run in a project"),
        (676, dot(656, y + 40), "Branches rejoin"),
    ]))
    page("skill-workflow", "Flowchart · SKILL.md", "Which branch the skill takes",
         "Flowchart of the modular-architecture skill: a project whose agent docs do not name the skill is reconciled first, "
         "then the task routes to adding a module, migrating legacy code, or reviewing a structural diff, each ending at its "
         "done-when criteria.",
         "\n".join(b))


# ================= C. Use case sequence =================
def seq():
    b = []
    xs = [120, 300, 480, 660, 840]
    actors = [("HTTP route", "billing/api/", "backend"),
              ("Use case", "billing/services/", "focal"),
              ("Lower facade", "people/__init__.py", "backend"),
              ("Unit of work", "one DB session", "store"),
              ("Notifier port", "adapter, wired at root", "backend")]
    # lifelines
    for cx in xs:
        b.append(f'<line x1="{cx}" y1="96" x2="{cx}" y2="456" stroke="{ink(0.20)}" stroke-width="1" stroke-dasharray="3,3"/>')
    # activation bars
    for cx, y1, y2 in [(120, 128, 432), (300, 164, 432), (480, 200, 288), (840, 380, 404)]:
        b.append(f'<rect x="{cx-4}" y="{y1}" width="8" height="{y2-y1}" fill="{ink(0.06)}" stroke="{MUTED}" stroke-width="0.8"/>')

    def msg(y, x1, x2, text, lx=None, kind="muted", dashed=False):
        lx = lx if lx is not None else (x1 + x2) / 2
        col = ACCENT if kind == "accent" else SOFT
        return line(x1, y, x2, y, kind, dashed) + "\n" + label(lx, y - 20, text, color=col)

    b.append(msg(136, 124, 660, "OPEN UOW", lx=390))
    b.append(msg(172, 124, 296, "RUN(UOW)"))
    b.append(msg(208, 304, 476, "FACADE CALL"))
    b.append(msg(244, 484, 660, "WRITE OWN ROWS"))
    b.append(msg(280, 476, 304, "DTO", dashed=True))
    b.append(msg(316, 304, 660, "WRITE OWN ROWS", lx=570))
    b.append(msg(352, 304, 660, "COMMIT()", lx=570, kind="accent"))
    b.append(msg(388, 304, 836, "NOTIFY", lx=750, kind="open", dashed=True))
    b.append(msg(424, 296, 124, "RESULT DTO", dashed=True))
    # actors
    for cx, (n, s, k) in zip(xs, actors):
        b.append(node(cx - 76, 40, 152, 56, n, s, kind=k))
    # callout
    b.append(callout(904, 500, "any step raises: rollback, nothing saved, nothing sent",
                     "M 672,486 Q 666,470 660,460", (660, 458)))
    y = 524
    b.append(legend(y, "LEGEND", [
        (76, line(40, y + 40, 68, y + 40), "Synchronous call"),
        (220, line(184, y + 40, 212, y + 40, dashed=True), "Return"),
        (336, line(300, y + 40, 328, y + 40, "open", dashed=True), "After-commit notification"),
        (528, line(492, y + 40, 520, y + 40, "accent"), "The one commit, by the outermost use case"),
    ]))
    page("use-case-sequence", "Sequence · decisions D3, D6, D7",
         "A cross-module write in one unit of work",
         "Sequence of a write workflow in the highest module: the HTTP route builds one unit of work per request, the use case "
         "writes through a lower module's facade and its own repositories on that same unit of work, commits once, and only "
         "then calls its notifier port.",
         "\n".join(b))


# ================= D. Migration playbook =================
def playbook():
    b = []
    stages = [
        ("SETUP", "Once per project", "input",
         ["Enforcement tests,", "report-only", "API snapshot test", "Baseline of failures"],
         ["Every module listed,", "enforced set empty", "Baseline taken on a", "fresh database"]),
        ("TICKET 1", "API + facade", "backend",
         ["Characterize endpoints", "Move HTTP into api/", "Build the facade", "Rewire every caller"],
         ["Snapshot unchanged", "Char. tests unchanged", "Route order unchanged", "No old imports left"]),
        ("TICKET 2", "Workflows up", "backend",
         ["Cross-module writes", "move to the highest", "module, one UoW", "Add a notifier port"],
         ["Atomicity test:", "a failed step saves", "nothing", "No upward import left"]),
        ("TICKET 3", "Flatten + enforce", "backend",
         ["Collapse into layers", "Inject the UoW", "Repos become classes", "Delete dead code"],
         ["Zero violations,", "module enforced", "Snapshot unchanged", "Gate = baseline"]),
    ]
    xs = [120, 320, 520, 720]
    W, TOP, BOT = 176, 80, 336
    # row labels
    for y, t in [(108, "STAGE"), (152, "DOES"), (252, "PROVES"), (372, "ALWAYS")]:
        b.append(f'<text x="40" y="{y}" fill="{SOFT}" font-size="8" font-family="{MONO}" letter-spacing="0.14em">{t}</text>')
    # arrows: hand-offs and the per-module loop
    for x in xs[:-1]:
        b.append(line(x + W, 108, x + W + 24, 108))
    b.append(path("M808,80 V56 Q808,48 800,48 H416 Q408,48 408,56 V80", dashed=True))
    b.append(label(608, 56, "NEXT MODULE UP", 80))
    # stage cards
    for x, (tag, name, kind, does, proves) in zip(xs, stages):
        fill, stroke = ("rgba(79,93,117,0.10)", SOFT) if kind == "input" else ("#ffffff", INK)
        b.append(f'<rect x="{x}" y="{TOP}" width="{W}" height="{BOT-TOP}" rx="6" fill="{PAPER}"/>')
        b.append(f'<rect x="{x}" y="{TOP}" width="{W}" height="{BOT-TOP}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
        tw = round((len(tag) * 5.2 + 8) / 4) * 4
        b.append(f'<rect x="{x+12}" y="{TOP+10}" width="{tw}" height="12" rx="2" fill="none" stroke="{MUTED}" stroke-opacity="0.5" stroke-width="0.8"/>')
        b.append(f'<text x="{x+12+tw/2:g}" y="{TOP+19}" fill="{MUTED}" font-size="7" font-family="{MONO}" text-anchor="middle" letter-spacing="0.08em">{tag}</text>')
        b.append(f'<text x="{x+12}" y="{TOP+40}" fill="{INK}" font-size="12" font-weight="600" font-family="{SANS}">{name}</text>')
        for yy in (TOP + 52, TOP + 152):
            b.append(f'<line x1="{x+12}" y1="{yy}" x2="{x+W-12}" y2="{yy}" stroke="{ink(0.12)}" stroke-width="0.8"/>')
        for i, t in enumerate(does):
            b.append(f'<text x="{x+12}" y="{TOP+72+16*i}" fill="{INK}" font-size="11" font-family="{SANS}">{t}</text>')
        for i, t in enumerate(proves):
            b.append(f'<text x="{x+12}" y="{TOP+172+16*i}" fill="{INK}" font-size="11" font-family="{SANS}">{t}</text>')
    # the invariant bar (focal)
    b.append(f'<text x="208" y="376" fill="{SOFT}" font-size="9" font-family="{MONO}" text-anchor="middle">creates the yardstick</text>')
    b.append(f'<rect x="320" y="356" width="576" height="40" rx="6" fill="{ACCENT_TINT}" stroke="{ACCENT}" stroke-width="1"/>')
    b.append(f'<text x="336" y="381" fill="{INK}" font-size="12" font-weight="600" font-family="{SANS}">Behaviour-frozen</text>')
    b.append(f'<text x="472" y="380" fill="{MUTED}" font-size="9" font-family="{MONO}">same API snapshot, same characterization results, bugs included</text>')
    # callout
    b.append(callout(904, 452, "a bug fixed in passing is reverted and filed",
                     "M 848,436 Q 836,416 828,400", (828, 398)))
    y = 524
    b.append(legend(y, "LEGEND", [
        (72, sw_box(40, y + 34, "rgba(79,93,117,0.10)", SOFT), "Runs once"),
        (184, sw_box(152, y + 34, "#ffffff", INK), "One ticket: own branch and review"),
        (408, sw_box(376, y + 34, ACCENT_TINT, ACCENT), "Holds for every ticket"),
        (584, line(548, y + 40, 576, y + 40, dashed=True), "Next module up, until every module is enforced"),
    ]))
    page("migration-playbook", "Process · references/playbook.md",
         "Migrating a module, ticket by ticket",
         "Stage framework of the migration playbook: a one-time setup, then three tickets per module, each listing what it "
         "does and what it must prove, repeated bottom-up through the module order with behaviour frozen throughout.",
         "\n".join(b))


module_anatomy()
skill_workflow()
seq()
playbook()
print("built", sorted(p.name for p in OUT.glob("*.html")))
