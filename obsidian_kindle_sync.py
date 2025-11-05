"""Utility for syncing your Kindle library into Obsidian.

The script talks to Amazon's "Manage Your Content and Devices" backend to pull
your Kindle books, download their cover art, and render an Obsidian friendly
Markdown file for each title.

Authentication
---------------
The HTTP endpoints used by this integration are the same ones that power the
`https://www.amazon.com/hz/mycd/digital-console/contentlist/books` web UI.  The
API does not support programmatic logins, so you must copy two pieces of data
from a logged-in browser session before running the script:

* A `Cookie` header value – grab the full cookie string from any network request
  to the digital-console endpoint.
* The `x-amzn-csrf-token` header – available as the `csrf-token` cookie in
  modern browsers.  Amazon rotates the token frequently, so expect to refresh it
  occasionally.

Once you have those values you can feed them to the CLI via `--cookie`/`--cookie-file`
and `--csrf-token` respectively.

Typical usage
-------------
```
python obsidian_kindle_sync.py \
    --vault /path/to/ObsidianVault \
    --cookie-file ~/.config/kindle_cookie.txt \
    --csrf-token "..."
```

The script will create a `Kindle Library` folder (customisable with
`--subdir-name`) inside the vault, download cover images into a sibling `covers`
folder, and generate a Markdown file per book containing useful metadata in the
YAML front matter.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

import requests
from requests import Response, Session


AMAZON_LIBRARY_ENDPOINT = (
    "https://www.amazon.com/hz/mycd/digital-console/contentlist/books"
)


class KindleRequestError(RuntimeError):
    """Raised when the Amazon backend returns an unexpected response."""


def _slugify(value: str) -> str:
    """Return a filesystem friendly slug for *value*.

    On Windows the colon character is not allowed in filenames, therefore we
    normalise to lowercase alphanumerics joined by hyphens.  The slug is kept
    short but deterministic so we can safely re-run the tool without creating
    duplicate files.
    """

    value = value.strip().lower()
    # Replace any non-alphanumeric sequences with a single hyphen.
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "book"


@dataclass
class KindleBook:
    """Representation of a Kindle book as returned by Amazon's API."""

    asin: str
    title: str
    authors: List[str]
    cover_url: Optional[str]
    product_url: Optional[str]
    purchase_date: Optional[str]
    last_access: Optional[str]
    is_archived: bool
    raw: Dict[str, object]

    @classmethod
    def from_api(cls, payload: Dict[str, object]) -> "KindleBook":
        """Convert a raw API payload into :class:`KindleBook`.

        The Amazon JSON payload is not publicly documented and tends to change.
        To make the integration resilient we defensively look up keys and allow
        missing data.
        """

        asin = str(payload.get("asin") or payload.get("asinIdentifier") or "")
        title = str(payload.get("title") or payload.get("displayTitle") or "")
        authors_field = payload.get("authors") or payload.get("author") or []

        if isinstance(authors_field, str):
            authors = [authors_field]
        elif isinstance(authors_field, Iterable):
            authors = [str(a) for a in authors_field]
        else:
            authors = []

        cover = payload.get("cover") or payload.get("image") or {}
        cover_url: Optional[str]
        if isinstance(cover, dict):
            cover_url = cover.get("small") or cover.get("medium") or cover.get(
                "large"
            )
        elif isinstance(cover, str):
            cover_url = cover
        else:
            cover_url = None

        last_access = None
        for key in ("lastAccess", "lastAccessedDate", "lastReadTimestamp"):
            if payload.get(key):
                last_access = str(payload[key])
                break

        product_url = None
        for key in ("productUrl", "productLink", "titleWebUrl"):
            if payload.get(key):
                product_url = str(payload[key])
                break

        purchase_date = None
        for key in ("purchaseDate", "acquiredTime", "acquiredDate"):
            if payload.get(key):
                purchase_date = str(payload[key])
                break

        is_archived = bool(payload.get("archived") or payload.get("isArchived"))

        if not asin:
            raise KindleRequestError("Book payload missing ASIN identifier")

        return cls(
            asin=asin,
            title=title or f"Unknown title ({asin})",
            authors=authors,
            cover_url=cover_url,
            product_url=product_url,
            purchase_date=purchase_date,
            last_access=last_access,
            is_archived=is_archived,
            raw=payload,
        )


def iter_library(
    session: Session,
    page_size: int = 50,
    max_pages: Optional[int] = None,
    include_archived: bool = False,
) -> Iterator[KindleBook]:
    """Yield Kindle books from the Amazon content API."""

    page = 1
    while True:
        params = {
            "sortBy": "TITLE",
            "order": "ASCENDING",
            "startIndex": (page - 1) * page_size,
            "pageSize": page_size,
            "contentType": "Ebook",
            "excludeDocs": "true",
            "hideFurled": "true",
        }
        if include_archived:
            params["showAll"] = "true"

        response = session.get(AMAZON_LIBRARY_ENDPOINT, params=params, timeout=30)
        _ensure_ok(response)
        try:
            payload = response.json()
        except ValueError as exc:  # pragma: no cover - defensive
            raise KindleRequestError("Amazon responded with invalid JSON") from exc

        items = payload.get("items") or payload.get("contentList") or []
        if not isinstance(items, list):
            raise KindleRequestError("Unexpected payload structure: missing items list")

        if not items:
            break

        for item in items:
            try:
                book = KindleBook.from_api(item)
            except KindleRequestError:
                continue

            if not include_archived and book.is_archived:
                continue

            yield book

        page += 1
        if max_pages is not None and page > max_pages:
            break

        if payload.get("hasMore") is False:
            break


def _ensure_ok(response: Response) -> None:
    """Raise :class:`KindleRequestError` if the response is not HTTP 200."""

    if response.status_code != 200:
        raise KindleRequestError(
            f"Amazon request failed: {response.status_code} {response.text[:200]}"
        )


def _prepare_session(cookie: str, csrf_token: str) -> Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/117.0 Safari/537.36"
            ),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.amazon.com/hz/mycd/myx",
            "Cookie": cookie,
            "X-Requested-With": "XMLHttpRequest",
            "x-amzn-csrf-token": csrf_token,
        }
    )
    return session


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _download_cover(session: Session, url: str, destination: Path) -> None:
    response = session.get(url, timeout=30)
    _ensure_ok(response)
    destination.write_bytes(response.content)


def _render_markdown(book: KindleBook, cover_rel_path: Optional[Path]) -> str:
    authors = ", ".join(book.authors) if book.authors else "Unknown"
    front_matter = {
        "asin": book.asin,
        "title": book.title,
        "authors": book.authors if book.authors else None,
        "purchase_date": book.purchase_date,
        "last_access": book.last_access,
        "archived": book.is_archived,
        "product_url": book.product_url,
    }

    front_matter_lines = ["---"]
    for key, value in front_matter.items():
        if value is None:
            continue
        front_matter_lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    front_matter_lines.append("---")
    metadata = "\n".join(front_matter_lines)

    body_lines = [metadata, "", f"# {book.title}", "", f"**Author(s):** {authors}"]

    if cover_rel_path:
        body_lines.append("")
        body_lines.append(f"![[{cover_rel_path.as_posix()}]]")

    if book.product_url:
        body_lines.extend(["", f"[View on Amazon]({book.product_url})"])

    body_lines.extend(
        [
            "",
            "## Raw payload",
            "",
            "```json",
            json.dumps(book.raw, indent=2, ensure_ascii=False),
            "```",
        ]
    )

    return "\n".join(body_lines) + "\n"


def sync(
    vault_path: Path,
    session: Session,
    subdir_name: str,
    cover_dir_name: str,
    page_size: int,
    max_pages: Optional[int],
    include_archived: bool,
    dry_run: bool,
) -> None:
    """Synchronise the Kindle library into the Obsidian vault."""

    library_dir = vault_path / subdir_name
    cover_dir = library_dir / cover_dir_name

    _ensure_directory(library_dir)
    _ensure_directory(cover_dir)

    for book in iter_library(
        session,
        page_size=page_size,
        max_pages=max_pages,
        include_archived=include_archived,
    ):
        slug = _slugify(f"{book.title}-{book.asin}")
        markdown_path = library_dir / f"{slug}.md"
        cover_path = cover_dir / f"{slug}.jpg"
        cover_rel_path: Optional[Path] = (
            cover_path.relative_to(vault_path) if cover_path.exists() else None
        )

        if dry_run:
            print(f"[DRY-RUN] Would update {markdown_path}")
            continue

        if book.cover_url:
            try:
                _download_cover(session, book.cover_url, cover_path)
                cover_rel_path = cover_path.relative_to(vault_path)
            except KindleRequestError as exc:
                print(f"Failed to download cover for {book.title}: {exc}")

        markdown_content = _render_markdown(book, cover_rel_path)
        markdown_path.write_text(markdown_content, encoding="utf-8")
        print(f"Wrote {markdown_path}")


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vault",
        type=Path,
        required=True,
        help="Path to your Obsidian vault",
    )
    parser.add_argument(
        "--cookie",
        help="Raw Cookie header string captured from an authenticated Amazon session",
    )
    parser.add_argument(
        "--cookie-file",
        type=Path,
        help="File containing the Cookie header (alternative to --cookie)",
    )
    parser.add_argument(
        "--csrf-token",
        required=True,
        help="Value of the x-amzn-csrf-token header",
    )
    parser.add_argument(
        "--subdir-name",
        default="Kindle Library",
        help="Folder inside the vault that will contain the generated notes",
    )
    parser.add_argument(
        "--cover-dir-name",
        default="covers",
        help="Name of the folder (inside the subdir) that will store cover images",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=50,
        help="Number of books to request per page",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Optional limit of pages to fetch",
    )
    parser.add_argument(
        "--include-archived",
        action="store_true",
        help="Include archived books in the export",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the actions without writing files",
    )
    return parser.parse_args(argv)


def _load_cookie(args: argparse.Namespace) -> str:
    cookie = args.cookie
    if args.cookie_file:
        cookie = args.cookie_file.read_text(encoding="utf-8").strip()

    if not cookie:
        raise SystemExit("You must provide --cookie or --cookie-file")

    return cookie


def main(argv: Optional[List[str]] = None) -> None:
    args = _parse_args(argv)
    vault_path = args.vault.expanduser().resolve()
    _ensure_directory(vault_path)

    cookie = _load_cookie(args)
    session = _prepare_session(cookie=cookie, csrf_token=args.csrf_token)

    sync(
        vault_path=vault_path,
        session=session,
        subdir_name=args.subdir_name,
        cover_dir_name=args.cover_dir_name,
        page_size=args.page_size,
        max_pages=args.max_pages,
        include_archived=args.include_archived,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()

