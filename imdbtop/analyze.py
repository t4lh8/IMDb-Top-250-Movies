"""Summaries of the Top 250 used for the analysis sheets and the README chart."""

from collections import defaultdict
from statistics import mean, median

from .build import Movie


def _group_stats(groups: dict, order=None) -> list[dict]:
    rows = []
    for key, items in groups.items():
        rows.append(
            {
                "key": key,
                "count": len(items),
                "avg_rating": round(mean(m.rating for m in items), 2),
                "avg_votes": round(mean(m.votes for m in items)),
                "best": min(items, key=lambda m: m.rank).title,
            }
        )
    if order == "key":
        rows.sort(key=lambda r: r["key"])
    else:
        rows.sort(key=lambda r: (-r["count"], -r["avg_rating"], str(r["key"])))
    return rows


def by_decade(movies: list[Movie]) -> list[dict]:
    groups = defaultdict(list)
    for m in movies:
        if m.decade is not None:
            groups[m.decade].append(m)
    return _group_stats(groups, order="key")


def by_genre(movies: list[Movie]) -> list[dict]:
    """A movie with three genres counts once in each of them."""
    groups = defaultdict(list)
    for m in movies:
        for g in m.genres:
            groups[g].append(m)
    return _group_stats(groups)


def by_director(movies: list[Movie], min_films: int = 2) -> list[dict]:
    groups = defaultdict(list)
    for m in movies:
        for d in m.directors:
            groups[d].append(m)
    return [r for r in _group_stats(groups) if r["count"] >= min_films]


def runtime_buckets(movies: list[Movie]) -> list[dict]:
    edges = [(0, 90, "Under 90 min"), (90, 120, "90-119 min"), (120, 150, "120-149 min"), (150, 180, "150-179 min"), (180, 10_000, "180+ min")]
    groups = {label: [] for *_, label in edges}
    for m in movies:
        if m.runtime is None:
            continue
        for lo, hi, label in edges:
            if lo <= m.runtime < hi:
                groups[label].append(m)
                break
    rows = _group_stats({k: v for k, v in groups.items() if v})
    order = [label for *_, label in edges]
    return sorted(rows, key=lambda r: order.index(r["key"]))


def overview(movies: list[Movie]) -> dict:
    runtimes = [m.runtime for m in movies if m.runtime]
    years = [m.year for m in movies if m.year]
    most_voted = max(movies, key=lambda m: m.votes)
    oldest = min((m for m in movies if m.year), key=lambda m: m.year)
    newest = max((m for m in movies if m.year), key=lambda m: m.year)
    return {
        "movies": len(movies),
        "avg_rating": round(mean(m.rating for m in movies), 2),
        "median_votes": round(median(m.votes for m in movies)),
        "avg_runtime": round(mean(runtimes)) if runtimes else None,
        "year_span": f"{min(years)}-{max(years)}" if years else "",
        "most_voted": f"{most_voted.title} ({most_voted.votes:,} votes)",
        "oldest": f"{oldest.title} ({oldest.year})",
        "newest": f"{newest.title} ({newest.year})",
        "translated_titles": sum(1 for m in movies if m.original_title != m.title),
    }
