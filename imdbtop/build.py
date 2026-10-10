"""Turn the raw IMDb TSV files into a ranked Top 250 list.

The files are large (title.basics alone is over 12 million rows), so every file
is streamed line by line and only the rows we need are kept.

Ranking uses the weighted rating IMDb published for its Top 250 for many years:

    WR = v / (v + m) * R + m / (v + m) * C

R = average rating, v = number of votes, m = minimum votes to be listed (25,000),
C = mean rating across all eligible movies. IMDb's current formula is not public
and only counts "regular voters", so the order is close to the live chart but
not identical.
"""

import gzip
from dataclasses import dataclass, field
from pathlib import Path

MIN_VOTES = 25_000
NULL = r"\N"


@dataclass
class Movie:
    tconst: str
    title: str
    original_title: str
    year: int | None
    runtime: int | None
    genres: list[str]
    rating: float
    votes: int
    score: float = 0.0
    directors: list[str] = field(default_factory=list)
    rank: int = 0

    @property
    def decade(self) -> int | None:
        return self.year // 10 * 10 if self.year else None

    @property
    def url(self) -> str:
        return f"https://www.imdb.com/title/{self.tconst}/"


def _rows(path: Path):
    """Yield each data row of a gzipped TSV as a list of strings (header skipped).

    IMDb's files contain stray quote characters, so the csv module would merge
    lines. A plain split on tabs is both safe and faster here.
    """
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="\n") as fh:
        next(fh, None)
        for line in fh:
            yield line.rstrip("\n").split("\t")


def _int(value: str) -> int | None:
    return None if value == NULL or not value.isdigit() else int(value)


def weighted_score(rating: float, votes: int, mean: float, min_votes: int = MIN_VOTES) -> float:
    return votes / (votes + min_votes) * rating + min_votes / (votes + min_votes) * mean


def load_ratings(path: Path, min_votes: int = MIN_VOTES) -> dict[str, tuple[float, int]]:
    """tconst -> (rating, votes) for titles with at least min_votes."""
    out = {}
    for tconst, rating, votes in _rows(path):
        v = int(votes)
        if v >= min_votes:
            out[tconst] = (float(rating), v)
    return out


def load_movies(path: Path, ratings: dict[str, tuple[float, int]]) -> list[Movie]:
    """Feature films (no TV, shorts or adult titles) that are in the ratings set."""
    movies = []
    for row in _rows(path):
        tconst, title_type, primary, original, is_adult, start_year, _end, runtime, genres = row[:9]
        if title_type != "movie" or is_adult == "1" or tconst not in ratings:
            continue
        rating, votes = ratings[tconst]
        movies.append(
            Movie(
                tconst=tconst,
                title=primary,
                original_title=original,
                year=_int(start_year),
                runtime=_int(runtime),
                genres=[] if genres == NULL else genres.split(","),
                rating=rating,
                votes=votes,
            )
        )
    return movies


def rank(movies: list[Movie], top: int = 250, min_votes: int = MIN_VOTES) -> list[Movie]:
    """Score every eligible movie and return the best `top`, ranked from 1."""
    if not movies:
        return []
    mean = sum(m.rating for m in movies) / len(movies)
    for m in movies:
        m.score = weighted_score(m.rating, m.votes, mean, min_votes)
    best = sorted(movies, key=lambda m: (-m.score, -m.votes, m.title))[:top]
    for i, m in enumerate(best, start=1):
        m.rank = i
    return best


def attach_directors(movies: list[Movie], crew_path: Path, names_path: Path) -> None:
    by_id = {m.tconst: m for m in movies}
    director_ids: dict[str, list[str]] = {}
    for tconst, directors, *_ in _rows(crew_path):
        if tconst in by_id and directors != NULL:
            director_ids[tconst] = directors.split(",")

    wanted = {d for ids in director_ids.values() for d in ids}
    names = {}
    for nconst, name, *_ in _rows(names_path):
        if nconst in wanted:
            names[nconst] = name

    for tconst, ids in director_ids.items():
        by_id[tconst].directors = [names.get(i, i) for i in ids]


def build_top(paths: dict[str, Path], top: int = 250, min_votes: int = MIN_VOTES, log=print) -> list[Movie]:
    log("  reading ratings ...")
    ratings = load_ratings(paths["title.ratings"], min_votes)
    log(f"  {len(ratings):,} titles have {min_votes:,}+ votes; reading titles ...")
    movies = load_movies(paths["title.basics"], ratings)
    log(f"  {len(movies):,} of them are feature films; ranking ...")
    best = rank(movies, top, min_votes)
    log("  looking up directors ...")
    attach_directors(best, paths["title.crew"], paths["name.basics"])
    return best
