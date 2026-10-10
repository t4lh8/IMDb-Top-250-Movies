"""A one page HTML report for GitHub Pages.

The page shows the top 10 and the analysis. The full list stays in the Excel
file, since IMDb's data terms do not allow republishing it as a database.
"""

from datetime import date
from html import escape
from pathlib import Path

from . import analyze, svg
from .build import Movie

CSS = """
body { font-family: "Segoe UI", Helvetica, Arial, sans-serif; margin: 0; background: #f3f4f6; color: #111827; }
header { background: #111827; color: #fff; padding: 32px 20px; }
header h1 { margin: 0 0 6px; font-size: 28px; }
header p { margin: 0; color: #d1d5db; }
main { max-width: 960px; margin: 0 auto; padding: 24px 20px 48px; }
section { background: #fff; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 2px rgba(0,0,0,.06); }
h2 { margin: 0 0 14px; font-size: 19px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; }
.card { background: #f9fafb; border-radius: 8px; padding: 12px; }
.card b { display: block; font-size: 22px; }
.card span { color: #6b7280; font-size: 13px; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { text-align: left; padding: 7px 8px; border-bottom: 1px solid #e5e7eb; }
th { background: #f9fafb; }
.num { text-align: right; }
a { color: #2563eb; }
svg { max-width: 100%; height: auto; }
.charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 12px; }
footer { text-align: center; color: #6b7280; font-size: 13px; }
"""


def _table(headers: list[str], rows: list[list], numeric: set[int] = frozenset()) -> str:
    head = "".join(f'<th class="num">{escape(h)}</th>' if i in numeric else f"<th>{escape(h)}</th>" for i, h in enumerate(headers))
    body = "".join(
        "<tr>" + "".join(f'<td class="num">{c}</td>' if i in numeric else f"<td>{c}</td>" for i, c in enumerate(row)) + "</tr>" for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def render(movies: list[Movie], built: date | None = None) -> str:
    built = built or date.today()
    facts = analyze.overview(movies)
    cards = [
        (facts["movies"], "movies"),
        (f'{facts["avg_rating"]:.2f}', "average rating"),
        (f'{facts["median_votes"]:,}', "median votes"),
        (f'{facts["avg_runtime"]} min', "average runtime"),
        (facts["year_span"], "years covered"),
        (sum(1 for m in movies if m.year and m.year >= 2000), "from 2000 or later"),
    ]
    top10 = [
        [m.rank, f'<a href="{m.url}">{escape(m.title)}</a>', m.year or "", escape(", ".join(m.directors)), f"{m.rating:.1f}", f"{m.votes:,}"]
        for m in movies[:10]
    ]
    directors = [[escape(r["key"]), r["count"], f'{r["avg_rating"]:.2f}', escape(r["best"])] for r in analyze.by_director(movies)[:10]]

    decades = svg.bar_chart([(f"{r['key']}s", r["count"]) for r in analyze.by_decade(movies)], "Movies per decade")
    genres = svg.bar_chart([(r["key"], r["count"]) for r in analyze.by_genre(movies)[:10]], "Ten most common genres")
    runtime = svg.bar_chart([(r["key"], r["count"]) for r in analyze.runtime_buckets(movies)], "Movies by runtime")

    def strip_xml(s: str) -> str:
        return s.replace(' xmlns="http://www.w3.org/2000/svg"', "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IMDb Top 250 Movies - analysis</title>
<style>{CSS}</style>
</head>
<body>
<header>
<h1>IMDb Top 250 Movies</h1>
<p>Built from the official IMDb datasets on {built.isoformat()}. Updated every week by GitHub Actions.</p>
</header>
<main>
<section>
<h2>Overview</h2>
<div class="cards">{"".join(f"<div class='card'><b>{v}</b><span>{escape(label)}</span></div>" for v, label in cards)}</div>
</section>
<section>
<h2>Top 10</h2>
{_table(["#", "Title", "Year", "Director", "Rating", "Votes"], top10, {0, 4, 5})}
<p>The full list of 250 is in the Excel file the tool creates. See the <a href="https://github.com/t4lh8/IMDb-Top-250-Movies">GitHub repo</a>.</p>
</section>
<section>
<h2>Charts</h2>
<div class="charts">{strip_xml(decades)}{strip_xml(genres)}{strip_xml(runtime)}</div>
</section>
<section>
<h2>Directors with the most films in the list</h2>
{_table(["Director", "Films", "Avg rating", "Highest ranked"], directors, {1, 2})}
</section>
<footer>
<p>Information courtesy of IMDb (<a href="https://www.imdb.com">imdb.com</a>). Used with permission. Personal, non-commercial project.</p>
<p>Made by Talha Aker</p>
</footer>
</main>
</body>
</html>
"""


def write(movies: list[Movie], folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / "index.html"
    out.write_text(render(movies), encoding="utf-8")
    return out
