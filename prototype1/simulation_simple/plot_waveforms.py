#!/usr/bin/env python3
"""Plot the last two switching periods written by flyback_simple.cir.

Usage: python3 plot_waveforms.py [waveforms.txt] [waveforms.svg]
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

src = sys.argv[1] if len(sys.argv) > 1 else "waveforms.txt"
dst = sys.argv[2] if len(sys.argv) > 2 else "waveforms.svg"

d = np.loadtxt(src)
t = (d[:, 0] - d[0, 0]) * 1e6  # microseconds
# wrdata writes a (time, value) pair per vector
panels = [
    ("Gate voltage, V", d[:, 1]),
    ("Drain voltage, V", d[:, 3]),
    ("Supply (primary) current, A", d[:, 9]),
    ("Secondary current, A", d[:, 11]),
    ("Output voltage, V", d[:, 7]),
]

INK, MUTED, GRID, LINE = "#1f2328", "#59636e", "#e6e8eb", "#2a6fbb"
fig, axes = plt.subplots(len(panels), 1, sharex=True, figsize=(8, 9))
fig.patch.set_facecolor("white")
for ax, (label, y) in zip(axes, panels):
    ax.plot(t, y, color=LINE, linewidth=1.2)
    ax.set_title(label, loc="left", fontsize=10, color=INK, pad=4)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.margins(x=0)
axes[-1].ticklabel_format(axis="y", useOffset=False)
axes[-1].set_xlabel("Time, µs", color=MUTED, fontsize=10)
fig.suptitle("Simple model: two switching periods in steady state",
             x=0.01, ha="left", fontsize=12, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig(dst)
