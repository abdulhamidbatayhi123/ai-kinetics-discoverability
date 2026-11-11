"""Paper 2's one figure style, built to Nature Portfolio's artwork rules (read live 2026-11-05,
research-figure-guide.nature.com and the natcomputsci / natchemeng AIP pages):

- widths 89 mm (single column) or 183 mm (double), height at most 170 mm, drawn at 100 %, so
  every font size below is the printed size;
- Arial, 5-7 pt (body 7, ticks and legends 6), panel letters 8 pt bold lowercase; the 5 pt floor
  and the size limits are ASSERTED when a figure is saved;
- no gridlines, shadows or coloured text; Okabe-Ito colours; every series also differs by line
  style or marker, so the figures survive greyscale;
- vector PDF with embedded TrueType fonts (fonttype 42), plus a 600 dpi PNG for review;
- a provenance file per figure: SHA-256 of the drawing script, this module and every input.

Fixed colour meanings (identical in every figure of the paper):
  discovery, best method    blue        identifiability of k     vermilion
  methods: M2 STLSQ sky, M3 ensemble green, M4 best subset blue, M5 EIV (oracle) black,
           M7 PySR reddish purple, M9 slow manifold grey; strong form dashed, weak form solid
  H2b words: fails before orange, fails with sky, outlives green; no verdict light grey
Paper 1's figstyle.py (imported with its solver) is left untouched; Paper 2 figures use this one.
"""
import hashlib
import json
import os
import sys
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

MM = 1 / 25.4
W1, W2 = 89 * MM, 183 * MM            # Nature single and double column (inches)
H_MAX = 170 * MM
BODY_PT, SMALL_PT, LETTER_PT, MIN_PT, MAX_PT = 7.0, 6.0, 8.0, 5.0, 8.0
PNG_DPI = 600

OI = {"black": "#000000", "orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73",
      "yellow": "#F0E442", "blue": "#0072B2", "vermilion": "#D55E00", "purple": "#CC79A7",
      "grey": "#8C8C8C", "light": "#DDDDDD", "dark": "#333333"}

ROLE = {"disc": OI["blue"], "ident": OI["vermilion"], "neutral": OI["dark"], "muted": "#6B6B6B"}
C = {"dark": OI["dark"], "grey": ROLE["muted"]}   # names the figure scripts use for neutral ink
SOLVER = {"stlsq": OI["sky"], "ensemble": OI["green"], "best_subset": OI["blue"],
          "eiv_best_subset": OI["black"], "m7": OI["purple"], "slow_manifold": OI["grey"]}
WORD = {"discovery fails before identifiability": "#4D4D4D",   # verdict: a neutral hue used for nothing else

        "discovery fails with identifiability": OI["sky"],
        "discovery outlives identifiability": OI["green"]}
NO_VERDICT = OI["light"]
# three noise levels in one panel: one hue, three lightnesses (sequential, ordered)
DISC_SHADES = ("#9ecae1", "#3d85c6", "#08306b")
IDENT_SHADES = ("#fdbb84", "#e6550d", "#7f2704")


def apply():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic",
        "mathtext.bf": "Arial:bold", "mathtext.default": "regular",
        "font.size": BODY_PT, "axes.labelsize": BODY_PT, "axes.titlesize": BODY_PT,
        "xtick.labelsize": SMALL_PT, "ytick.labelsize": SMALL_PT, "legend.fontsize": SMALL_PT,
        "legend.title_fontsize": SMALL_PT, "legend.frameon": False, "legend.handlelength": 1.6,
        "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5, "lines.linewidth": 1.0,
        "lines.markersize": 3.5, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "axes.edgecolor": OI["dark"], "axes.labelcolor": "#000000",
        "xtick.color": OI["dark"], "ytick.color": OI["dark"], "text.color": "#000000",
        "axes.titlelocation": "left", "axes.titleweight": "normal",
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "savefig.dpi": PNG_DPI, "figure.dpi": 150})
    os.environ.setdefault("SOURCE_DATE_EPOCH", "0")


def letter(ax, s, x=-0.16, y=1.02):
    """Panel letter, Nature style: lowercase, bold, 8 pt, top left outside the axes."""
    ax.text(x, y, s, transform=ax.transAxes, fontsize=LETTER_PT, fontweight="bold",
            ha="left", va="bottom", color="#000000")


def font_range(fig):
    from matplotlib.text import Text
    sizes = [t.get_fontsize() for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()]
    return (min(sizes), max(sizes)) if sizes else (None, None)


def coloured_text(fig):
    """Visible texts whose colour is not black or the dark grey of axes (Nature: no coloured text)."""
    from matplotlib.colors import to_hex
    from matplotlib.text import Text
    ok = {"#000000", OI["dark"].lower(), ROLE["muted"].lower(), "#ffffff"}
    return [t.get_text()[:30] for t in fig.findobj(Text)
            if t.get_visible() and t.get_text().strip() and to_hex(t.get_color()).lower() not in ok]


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def save(fig, stem, inputs=(), allow_coloured_text=()):
    """Check the figure against the rules, then write stem.pdf, stem.png and stem.prov.json.
    Raises AssertionError instead of writing a figure that breaks a rule."""
    w, h = fig.get_size_inches()
    assert w <= W2 + 1e-6, f"{stem}: width {w / MM:.1f} mm > 183 mm"
    assert h <= H_MAX + 1e-6, f"{stem}: height {h / MM:.1f} mm > 170 mm"
    lo, hi = font_range(fig)
    assert lo is None or lo >= MIN_PT - 1e-9, f"{stem}: text at {lo} pt < {MIN_PT} pt"
    assert hi is None or hi <= MAX_PT + 1e-9, f"{stem}: text at {hi} pt > {MAX_PT} pt"
    bad = [t for t in coloured_text(fig) if t not in allow_coloured_text]
    assert not bad, f"{stem}: coloured text {bad}"
    os.makedirs(os.path.dirname(stem) or ".", exist_ok=True)
    meta = {"CreationDate": None, "ModDate": None}
    fig.savefig(stem + ".pdf", metadata=meta)
    fig.savefig(stem + ".png", dpi=PNG_DPI)
    script = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else None
    prov = {"figure": os.path.basename(stem), "size_mm": [round(w / MM, 1), round(h / MM, 1)],
            "font_pt": [lo, hi], "made": time.strftime("%Y-%m-%d %H:%M:%S"),
            "style_sha256": _sha(__file__),
            "script": os.path.basename(script) if script and os.path.exists(script) else None,
            "script_sha256": _sha(script) if script and os.path.exists(script) else None,
            "inputs": {p: _sha(p) for p in inputs if os.path.exists(p)}}
    with open(stem + ".prov.json", "w", encoding="utf-8") as f:
        json.dump(prov, f, indent=1)
    plt.close(fig)
    return [stem + ".pdf", stem + ".png"]
