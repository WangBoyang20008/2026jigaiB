"""Empirical complexity benchmark for the five sorting algorithms.

Measures comparisons, swaps and wall-clock time across input sizes and
input distributions (random / sorted / reversed / nearly-sorted), then
writes results.csv and a self-contained HTML report with SVG charts.
Pure stdlib so it runs anywhere.
"""

import csv
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from algorithms import ALGORITHMS

SIZES = [50, 100, 200, 400, 800, 1600]
REPEATS = 5
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")


def make_input(kind, n, rng):
    if kind == "random":
        return [rng.randint(0, 10_000) for _ in range(n)]
    if kind == "sorted":
        return list(range(n))
    if kind == "reversed":
        return list(range(n, 0, -1))
    if kind == "nearly_sorted":
        arr = list(range(n))
        for _ in range(max(1, n // 20)):
            i, j = rng.randrange(n), rng.randrange(n)
            arr[i], arr[j] = arr[j], arr[i]
        return arr
    raise ValueError(kind)


def measure(name, data):
    gen = ALGORITHMS[name][1](data)
    last = None
    t0 = time.perf_counter()
    for last in gen:
        pass
    elapsed = time.perf_counter() - t0
    assert last.array == sorted(data), f"{name} produced wrong result"
    return last.comparisons, last.swaps, elapsed


def benchmark(kind):
    rng = random.Random(42)
    rows = []
    for n in SIZES:
        for name in ALGORITHMS:
            comp = swaps = 0
            elapsed = 0.0
            for _ in range(REPEATS):
                data = make_input(kind, n, rng)
                c, s, t = measure(name, data)
                comp += c
                swaps += s
                elapsed += t
            rows.append({
                "distribution": kind,
                "algorithm": name,
                "n": n,
                "comparisons": comp // REPEATS,
                "swaps": swaps // REPEATS,
                "time_ms": round(elapsed / REPEATS * 1000, 3),
            })
            print(f"{kind:14s} {name:10s} n={n:5d} "
                  f"comp={comp // REPEATS:9d} swaps={swaps // REPEATS:9d}")
    return rows


PALETTE = ["#6e8cc8", "#f0c850", "#eb5a5a", "#5ac882", "#b07cd8"]
SHORT_NAMES = {"bubble": "Bubble", "insertion": "Insertion",
               "quick": "Quick", "merge": "Merge", "heap": "Heap"}


def svg_chart(series, title, x_label, y_label, width=720, height=380):
    """Render a simple log-y line chart as inline SVG."""
    pad_l, pad_r, pad_t, pad_b = 70, 20, 40, 50
    xs = sorted({x for points, _, _ in series for x, _ in points})
    ys = [y for points, _, _ in series for _, y in points if y > 0]
    x_min, x_max = min(xs), max(xs)
    import math
    y_min, y_max = min(ys), max(ys)
    log_lo, log_hi = math.log10(y_min), math.log10(y_max)

    def px(x):
        return pad_l + (x - x_min) / (x_max - x_min) * (width - pad_l - pad_r)

    def py(y):
        v = (math.log10(max(y, 1)) - log_lo) / (log_hi - log_lo)
        return height - pad_b - v * (height - pad_t - pad_b)

    parts = [f'<svg width="{width}" height="{height}" '
             f'xmlns="http://www.w3.org/2000/svg" font-family="sans-serif">',
             f'<text x="{width/2}" y="22" text-anchor="middle" '
             f'font-size="16" fill="#dde">{title}</text>']
    # grid + y ticks
    import math as m
    for e in range(int(log_lo), int(log_hi) + 1):
        y = 10 ** e
        yy = py(y)
        parts.append(f'<line x1="{pad_l}" y1="{yy:.1f}" x2="{width-pad_r}" '
                     f'y2="{yy:.1f}" stroke="#333" />')
        parts.append(f'<text x="{pad_l-8}" y="{yy+4:.1f}" text-anchor="end" '
                     f'font-size="11" fill="#99a">10^{e}</text>')
    for x in xs:
        parts.append(f'<text x="{px(x):.1f}" y="{height-pad_b+18}" '
                     f'text-anchor="middle" font-size="11" fill="#99a">{x}</text>')
    parts.append(f'<text x="{width/2}" y="{height-8}" text-anchor="middle" '
                 f'font-size="12" fill="#99a">{x_label}</text>')
    parts.append(f'<text x="14" y="{height/2}" text-anchor="middle" '
                 f'font-size="12" fill="#99a" transform="rotate(-90 14 {height/2})">'
                 f'{y_label}</text>')
    # series
    for points, label, color in series:
        pts = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in points)
        parts.append(f'<polyline points="{pts}" fill="none" '
                     f'stroke="{color}" stroke-width="2" />')
        for x, y in points:
            parts.append(f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="3" '
                         f'fill="{color}" />')
    # legend
    for i, (_, label, color) in enumerate(series):
        lx, ly = pad_l + 10 + i * 110, height - pad_b + 36
        parts.append(f'<rect x="{lx}" y="{ly-9}" width="10" height="10" fill="{color}"/>')
        parts.append(f'<text x="{lx+14}" y="{ly}" font-size="11" fill="#dde">{label}</text>')
    parts.append("</svg>")
    return "".join(parts)


def build_report(all_rows):
    by_dist = {}
    for r in all_rows:
        by_dist.setdefault(r["distribution"], []).append(r)

    sections = []
    for kind, rows in by_dist.items():
        for metric, title in [("comparisons", "Comparisons"),
                              ("swaps", "Swaps / Writes"),
                              ("time_ms", "Wall-clock time")]:
            series = []
            for (name, (_, _fn)), color in zip(ALGORITHMS.items(), PALETTE):
                pts = [(r["n"], r[metric]) for r in rows
                       if r["algorithm"] == name and r[metric] > 0]
                series.append((pts, SHORT_NAMES[name], color))
            sections.append(svg_chart(series, f"{title} — {kind} input",
                                      "n", f"{metric} (log scale)"))

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Sorting Benchmark Report</title>
<style>body{{background:#181a20;color:#dde;font-family:sans-serif;
max-width:780px;margin:2em auto;padding:0 1em}}h1{{font-size:22px}}
p{{color:#99a;line-height:1.6}}</style></head><body>
<h1>Sorting Algorithm Empirical Complexity Report</h1>
<p>Sizes: {SIZES}, averaged over {REPEATS} runs per size.
Distributions: random / sorted / reversed / nearly-sorted (5% swapped).
Note how quick sort (last-element pivot) degrades to O(n^2) on sorted and
reversed inputs, while merge and heap sort stay near n·log n everywhere.</p>
{''.join(sections)}
</body></html>"""
    path = os.path.join(OUT_DIR, "benchmark_report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def main():
    sys.setrecursionlimit(100_000)  # worst-case quick sort depth is O(n)
    os.makedirs(OUT_DIR, exist_ok=True)
    all_rows = []
    for kind in ["random", "sorted", "reversed", "nearly_sorted"]:
        all_rows.extend(benchmark(kind))

    csv_path = os.path.join(OUT_DIR, "results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)

    report = build_report(all_rows)
    print(f"\nCSV: {csv_path}\nReport: {report}")


if __name__ == "__main__":
    main()
