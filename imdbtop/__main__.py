"""Command line entry point: python -m imdbtop"""

import argparse
import sys
from pathlib import Path

from . import analyze, site, svg
from .build import MIN_VOTES, build_top
from .export import export
from .fetch import NEEDED, fetch_all


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="imdbtop", description="Build the IMDb Top 250 as an Excel workbook.")
    p.add_argument("--data-dir", type=Path, default=Path("data"), help="where the IMDb .tsv.gz files are kept")
    p.add_argument("--out", type=Path, default=Path("output/IMDb_Top_250_Movies.xlsx"), help="Excel file to write")
    p.add_argument("--top", type=int, default=250, help="how many movies to keep (default 250)")
    p.add_argument("--min-votes", type=int, default=MIN_VOTES, help="minimum votes to be listed")
    p.add_argument("--offline", action="store_true", help="use files already in --data-dir, do not download")
    p.add_argument("--force", action="store_true", help="download again even if the files are fresh")
    p.add_argument("--charts", type=Path, help="also write README SVG charts to this folder")
    p.add_argument("--site", type=Path, help="also write a one page HTML report to this folder")
    args = p.parse_args(argv)

    if args.offline:
        paths = {n: args.data_dir / f"{n}.tsv.gz" for n in NEEDED}
        missing = [str(x) for x in paths.values() if not x.exists()]
        if missing:
            print("Missing files: " + ", ".join(missing), file=sys.stderr)
            return 1
    else:
        print("Fetching IMDb datasets ...")
        paths = fetch_all(args.data_dir, force=args.force)

    print("Building the list ...")
    movies = build_top(paths, top=args.top, min_votes=args.min_votes)
    if not movies:
        print("No movies matched. Check the data files.", file=sys.stderr)
        return 1

    out = export(movies, args.out)
    print(f"Wrote {len(movies)} movies to {out}")
    for m in movies[:10]:
        print(f"  {m.rank:>3}. {m.title} ({m.year})  {m.rating}  {m.votes:,} votes")

    if args.charts:
        decades = [(f"{r['key']}s", r["count"]) for r in analyze.by_decade(movies)]
        genres = [(r["key"], r["count"]) for r in analyze.by_genre(movies)[:10]]
        svg.write(args.charts / "decades.svg", svg.bar_chart(decades, f"Top {len(movies)} movies per decade"))
        svg.write(args.charts / "genres.svg", svg.bar_chart(genres, "Ten most common genres"))
        print(f"Charts written to {args.charts}")

    if args.site:
        print(f"Web page written to {site.write(movies, args.site)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
