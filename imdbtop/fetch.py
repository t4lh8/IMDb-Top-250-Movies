"""Find and download the IMDb datasets with Requests and BeautifulSoup.

The files come from IMDb's official non-commercial dataset page, which is meant
to be downloaded from. The imdb.com chart page itself is not scraped: it sits
behind a bot challenge and IMDb's terms do not allow it.
"""

import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

INDEX_URL = "https://datasets.imdbws.com/"
NEEDED = ("title.ratings", "title.basics", "title.crew", "name.basics")
HEADERS = {"User-Agent": "imdb-top250-student-project/1.0 (personal, non-commercial use)"}
MAX_AGE_HOURS = 24  # IMDb refreshes the files once a day


def find_dataset_links(html: str, base_url: str = INDEX_URL) -> dict[str, str]:
    """Return {"title.ratings": url, ...} for every .tsv.gz link on the index page."""
    soup = BeautifulSoup(html, "html.parser")
    links = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.endswith(".tsv.gz"):
            name = href.rsplit("/", 1)[-1].removesuffix(".tsv.gz")
            links[name] = urljoin(base_url, href)
    return links


def is_fresh(path: Path, max_age_hours: float = MAX_AGE_HOURS) -> bool:
    return path.exists() and path.stat().st_size > 0 and (time.time() - path.stat().st_mtime) < max_age_hours * 3600


def download(url: str, dest: Path, session: requests.Session) -> None:
    """Stream a file to disk so a 300 MB download never sits in memory."""
    tmp = dest.with_suffix(dest.suffix + ".part")
    with session.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(tmp, "wb") as fh:
            fh.writelines(resp.iter_content(chunk_size=1 << 20))
    tmp.replace(dest)


def fetch_all(data_dir: Path, force: bool = False, log=print) -> dict[str, Path]:
    """Download the four files we need into data_dir. Skips files younger than a day."""
    data_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)

    resp = session.get(INDEX_URL, timeout=30)
    resp.raise_for_status()
    links = find_dataset_links(resp.text)
    missing = [n for n in NEEDED if n not in links]
    if missing:
        raise RuntimeError(f"Dataset page no longer lists: {', '.join(missing)}")

    paths = {}
    for name in NEEDED:
        dest = data_dir / f"{name}.tsv.gz"
        if not force and is_fresh(dest):
            log(f"  {dest.name}: up to date, skipping")
        else:
            log(f"  {dest.name}: downloading ...")
            download(links[name], dest, session)
        paths[name] = dest
    return paths
