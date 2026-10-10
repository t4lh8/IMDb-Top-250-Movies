import pytest

from imdbtop import analyze
from imdbtop.build import build_top, load_movies, load_ratings, rank, weighted_score


def test_weighted_score_pulls_low_vote_titles_toward_the_mean():
    assert weighted_score(9.0, 25_000, 7.0) == pytest.approx(8.0)
    assert weighted_score(9.0, 10_000_000, 7.0) == pytest.approx(9.0, abs=0.01)


def test_ratings_below_vote_limit_are_dropped(dataset):
    ratings = load_ratings(dataset["title.ratings"])
    assert "tt0000004" not in ratings
    assert ratings["tt0000001"] == (9.0, 2_000_000)


def test_only_feature_films_are_kept(dataset):
    movies = load_movies(dataset["title.basics"], load_ratings(dataset["title.ratings"]))
    ids = {m.tconst for m in movies}
    assert "tt0000005" not in ids  # tvSeries
    assert ids == {"tt0000001", "tt0000002", "tt0000003", "tt0000006", "tt0000007"}


def test_null_fields_and_quotes_are_parsed(dataset):
    movies = {m.tconst: m for m in load_movies(dataset["title.basics"], load_ratings(dataset["title.ratings"]))}
    slow = movies["tt0000006"]
    assert slow.runtime is None and slow.genres == []
    assert movies["tt0000007"].title == '"Quote" Story'
    assert movies["tt0000003"].original_title == "Fjordløpet"


def test_many_votes_beat_a_higher_rating_with_few_votes(dataset):
    top = build_top(dataset, log=lambda *_: None)
    # 9.0 with 2M votes beats 9.2 with 30k votes.
    assert [m.tconst for m in top] == ["tt0000001", "tt0000002", "tt0000007", "tt0000003", "tt0000006"]
    assert [m.rank for m in top] == list(range(1, len(top) + 1))


def test_top_limit(dataset):
    assert len(build_top(dataset, top=2, log=lambda *_: None)) == 2


def test_directors_are_resolved_and_unknown_ids_kept(dataset):
    top = {m.tconst: m for m in build_top(dataset, log=lambda *_: None)}
    assert top["tt0000002"].directors == ["Ola Nordmann", "Kari Hansen"]
    assert top["tt0000007"].directors == ["nm0000009"]
    assert top["tt0000006"].directors == []


def test_rank_handles_empty_list():
    assert rank([]) == []


def test_analysis_groups(dataset):
    top = build_top(dataset, log=lambda *_: None)
    decades = analyze.by_decade(top)
    assert [r["key"] for r in decades] == [1950, 1970, 1990, 2000, 2020]

    genres = {r["key"]: r for r in analyze.by_genre(top)}
    assert genres["Drama"]["count"] == 4
    assert genres["Drama"]["best"] == "Harbour Lights"

    directors = analyze.by_director(top)
    assert [(r["key"], r["count"]) for r in directors] == [("Ingrid Solberg", 2)]

    buckets = [r["key"] for r in analyze.runtime_buckets(top)]
    assert buckets == ["90-119 min", "120-149 min", "150-179 min", "180+ min"]

    facts = analyze.overview(top)
    assert facts["movies"] == 5
    assert facts["oldest"] == "Slow Train (1958)"
    assert facts["translated_titles"] == 1
