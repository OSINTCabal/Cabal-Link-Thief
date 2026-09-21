# Cabal-Link-Thief

**Cabal-Link-Thief** is a terminal-based OSINT link and contact-information extractor for a single domain.

Give it a domain and it will attempt common-subdomain discovery, fetch publicly accessible pages, extract contact-style intelligence from returned HTML, organize findings by subdomain, and optionally export the results to JSON and Markdown.

## Features

- Common-subdomain discovery through DNS resolution
- Root-domain inclusion
- HTTP and HTTPS probing
- Asynchronous HTTP requests with `httpx`
- Per-subdomain result aggregation and deduplication
- Email extraction
- Phone-number extraction
- IPv4 extraction
- Street-address extraction
- Social-profile discovery for:
  - X / Twitter
  - Facebook
  - LinkedIn
  - Instagram
  - YouTube
  - TikTok
  - Reddit
  - GitHub
- Basic person-name extraction
- Basic job-title extraction
- HTML link extraction with relative-to-absolute URL conversion
- Animated terminal UI
- JSON export
- Markdown export

## How It Works

### 1. Subdomain discovery

Cabal-Link-Thief checks a built-in wordlist of common subdomains such as:

```text
www
mail
admin
api
portal
support
blog
cdn
assets
cpanel
staff
team
```

Each candidate is tested through DNS resolution. The root domain is checked separately and included when resolvable.

### 2. Page fetching

For every discovered hostname, the scanner attempts both:

```text
https://hostname.example.com
http://hostname.example.com
```

The default scan is limited to 50 root URLs. Requests follow redirects and use a browser-like User-Agent.

### 3. Extraction

Returned HTML is searched for:

- Email addresses
- Phone numbers
- IPv4 addresses
- Street addresses
- Social-media profile URLs
- Person-like capitalized names
- Common job titles
- Links from HTML `<a href="...">` elements

Relative URLs are normalized with `urljoin()` before being stored.

### 4. Aggregation

Findings are stored per subdomain and deduplicated with Python sets.

### 5. Output

The terminal report is grouped by subdomain and includes finding counts. At the end of the scan you can save:

```text
json
md
both
none
```

Generated reports use timestamped filenames such as:

```text
example_com_scan_20260921_181500.json
example_com_scan_20260921_181500.md
```

## Requirements

- Python 3.10+
- `httpx`
- `beautifulsoup4`

## Installation

```bash
git clone https://github.com/OSINTCabal/Cabal-Link-Thief.git
cd Cabal-Link-Thief
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Usage

```bash
python CabalLinkThief.py
```

The program will prompt for a domain:

```text
Enter a domain to scan: example.com
```

Enter the hostname only. You do not need to include `https://` or a path.

## Example Workflow

```bash
cd Cabal-Link-Thief
source .venv/bin/activate
python CabalLinkThief.py
```

Then:

```text
Enter a domain to scan: example.com
```

After the scan finishes:

```text
Do you want to save the results? (json/md/both/none): both
```

## JSON Output

JSON reports contain the scanned domain, scan timestamp, discovered subdomains, page count, per-subdomain summary counts, and full deduplicated result collections.

Simplified structure:

```json
{
  "domain": "example.com",
  "scanned_at": "2026-09-21T18:15:00",
  "subdomains_found": [
    "example.com",
    "www.example.com"
  ],
  "pages_scanned": 4,
  "summary": {},
  "results": {}
}
```

## Markdown Output

Markdown reports include:

- Scan metadata
- Summary table by subdomain
- Emails
- Phone numbers
- Social profiles
- Addresses
- IP addresses
- Names / key terms
- Job titles
- URLs

## Project Structure

```text
Cabal-Link-Thief/
├── CabalLinkThief.py
├── README.md
├── requirements.txt
├── LICENSE
└── .gitignore
```

## Current Limitations

- Subdomain discovery uses a built-in dictionary rather than certificate-transparency logs or exhaustive enumeration.
- DNS resolution uses `socket.gethostbyname_ex()` and is blocking, even though discovery is scheduled from async code.
- The crawler currently fetches discovered subdomain roots rather than recursively following discovered links.
- The default page cap is 50 URLs.
- Name extraction intentionally uses a broad capitalization regex and can generate false positives.
- Street-address extraction is heuristic and primarily oriented toward common English-language address formats.
- IPv4 matching is syntactic and does not validate every octet as `0-255`.
- JavaScript-rendered content is not executed.

## Dependencies

`requirements.txt`:

```text
httpx>=0.27.0,<1.0.0
beautifulsoup4>=4.12.0,<5.0.0
```

## License

Released under the MIT License. See [`LICENSE`](LICENSE).
