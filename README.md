# Obsidian Kindle Sync

This repository contains a standalone Python script that exports your Kindle
library (metadata + cover images) into Markdown files that play nicely with an
Obsidian vault.

## Requirements

* Python 3.9+
* A modern web browser to copy the authentication cookies from Amazon's
  "Manage Your Content and Devices" page.

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

> **Note**: The project purposely has a tiny dependency footprint.  `requests`
> is the only third-party package required.

## Capturing your Amazon session

1. Visit <https://www.amazon.com/hz/mycd/myx> and make sure you can see your
   Kindle books.
2. Open the browser developer tools → Network tab.
3. Filter for `digital-console` and click on any `contentlist/books` request.
4. Copy the entire `Cookie` header value and paste it into a file, e.g.
   `~/.config/kindle_cookie.txt`.
5. Locate the `x-amzn-csrf-token` header (you can also grab it from the
   `csrf-token` cookie) and keep the value handy.

Both the cookie and CSRF token are short-lived.  If you receive HTTP 401/403
errors simply repeat the steps above to refresh the credentials.

## Exporting into Obsidian

```
python obsidian_kindle_sync.py \
  --vault /path/to/YourVault \
  --cookie-file ~/.config/kindle_cookie.txt \
  --csrf-token "TOKEN_FROM_STEP_5"
```

By default the script creates a `Kindle Library/` folder inside the vault and a
`covers/` subfolder for the artwork.  You can customise those names via
`--subdir-name` and `--cover-dir-name`.

Running the tool multiple times is idempotent: files are overwritten in-place so
your vault always reflects the most recent state of your Kindle library.

Pass `--dry-run` to preview which notes would be written without touching the
filesystem.  Use `--include-archived` if you want to capture archived titles as
well.

## Troubleshooting

* **HTTP 401 or 403** – Refresh the cookie and CSRF token as described above.
* **Covers missing** – Some Kindle items (e.g. personal documents) do not have
  cover art exposed through the API.  The Markdown notes will still be created.
* **Endpoint structure changed** – Amazon frequently tweaks the JSON schema.
  If you notice missing fields, search for the failing note in the raw payload
  (included at the bottom of each Markdown file) and update the parser logic in
  `obsidian_kindle_sync.py` accordingly.

