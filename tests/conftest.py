import gzip
from pathlib import Path

import pytest


def write_tsv(path: Path, header: str, rows: list[str]) -> Path:
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as fh:
        fh.write(header + "\n")
        for row in rows:
            fh.write(row + "\n")
    return path


@pytest.fixture
def dataset(tmp_path: Path) -> dict[str, Path]:
    """A tiny fake copy of the four IMDb files with the real column layout."""
    ratings = write_tsv(
        tmp_path / "title.ratings.tsv.gz",
        "tconst\taverageRating\tnumVotes",
        [
            "tt0000001\t9.0\t2000000",  # big and good
            "tt0000002\t9.2\t30000",  # higher rating, few votes
            "tt0000003\t8.0\t1000000",
            "tt0000004\t9.9\t5000",  # under the vote limit
            "tt0000005\t9.8\t900000",  # a TV series, not a movie
            "tt0000006\t7.0\t100000",
            "tt0000007\t8.5\t400000",  # stray quote in the title
        ],
    )
    basics = write_tsv(
        tmp_path / "title.basics.tsv.gz",
        "tconst\ttitleType\tprimaryTitle\toriginalTitle\tisAdult\tstartYear\tendYear\truntimeMinutes\tgenres",
        [
            "tt0000001\tmovie\tHarbour Lights\tHarbour Lights\t0\t1994\t\\N\t142\tDrama",
            "tt0000002\tmovie\tNordlys\tNordlys\t0\t2021\t\\N\t95\tDrama,Romance",
            "tt0000003\tmovie\tFjord Run\tFjordløpet\t0\t1972\t\\N\t175\tCrime,Drama",
            "tt0000004\tmovie\tTiny Film\tTiny Film\t0\t2020\t\\N\t80\tComedy",
            "tt0000005\ttvSeries\tA Show\tA Show\t0\t2008\t2013\t47\tDrama",
            "tt0000006\tmovie\tSlow Train\tSlow Train\t0\t1958\t\\N\t\\N\t\\N",
            'tt0000007\tmovie\t"Quote" Story\t"Quote" Story\t0\t2001\t\\N\t201\tAdventure,Drama',
        ],
    )
    crew = write_tsv(
        tmp_path / "title.crew.tsv.gz",
        "tconst\tdirectors\twriters",
        [
            "tt0000001\tnm0000001\t\\N",
            "tt0000002\tnm0000002,nm0000003\t\\N",
            "tt0000003\tnm0000001\t\\N",
            "tt0000006\t\\N\t\\N",
            "tt0000007\tnm0000009\t\\N",  # not in name.basics
        ],
    )
    names = write_tsv(
        tmp_path / "name.basics.tsv.gz",
        "nconst\tprimaryName\tbirthYear\tdeathYear\tprimaryProfession\tknownForTitles",
        [
            "nm0000001\tIngrid Solberg\t1960\t\\N\tdirector\ttt0000001",
            "nm0000002\tOla Nordmann\t1980\t\\N\tdirector\ttt0000002",
            "nm0000003\tKari Hansen\t1985\t\\N\tdirector\ttt0000002",
        ],
    )
    return {"title.ratings": ratings, "title.basics": basics, "title.crew": crew, "name.basics": names}
