"""Small SVG bar charts for the README, so the repo needs no image files from elsewhere."""

from html import escape
from pathlib import Path


def bar_chart(rows: list[tuple[str, float]], title: str, value_fmt: str = "{:.0f}") -> str:
    """Horizontal bar chart, one row per (label, value)."""
    bar_h, gap, label_w, chart_w, top = 18, 6, 110, 420, 40
    height = top + len(rows) * (bar_h + gap) + 10
    width = label_w + chart_w + 60
    peak = max((v for _, v in rows), default=1) or 1

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="12">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="12" y="24" font-size="15" font-weight="600" fill="#111827">{escape(title)}</text>',
    ]
    for i, (label, value) in enumerate(rows):
        y = top + i * (bar_h + gap)
        w = max(1, round(value / peak * chart_w))
        parts.append(f'<text x="{label_w - 8}" y="{y + 13}" text-anchor="end" fill="#374151">{escape(str(label))}</text>')
        parts.append(f'<rect x="{label_w}" y="{y}" width="{w}" height="{bar_h}" rx="3" fill="#2563eb"/>')
        parts.append(f'<text x="{label_w + w + 6}" y="{y + 13}" fill="#111827">{value_fmt.format(value)}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write(path: Path, svg: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
