import json
import time
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger('domainupdater')

WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/Anna%27s_Archive"
UPDATE_INTERVAL = 6 * 3600  # 6 hours in seconds


def _wiki_domains_file():
    from stacks.constants import CONFIG_PATH
    return CONFIG_PATH / "wiki_domains.json"


def fetch_annas_archive_domains():
    """Fetch current Anna's Archive domains from Wikipedia. Returns list of bare domains."""
    import requests

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(WIKIPEDIA_URL, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Wikipedia returned status {response.status_code}")
            return []
    except Exception as e:
        logger.warning(f"Failed to fetch domains from Wikipedia: {e}")
        return []

    pattern_table = re.compile(
        r'<table[^>]*class="[^"]*infobox vcard[^"]*"[^>]*>(.*?)(?:<h2|</table)',
        re.DOTALL | re.IGNORECASE
    )
    pattern_span = re.compile(
        r'<span[^>]*class="[^"]*url[^"]*"[^>]*>(.*?)</span>',
        re.DOTALL | re.IGNORECASE
    )
    pattern_link = re.compile(
        r'<a[^>]*class="[^"]*external text[^"]*"[^>]*href="([^"]+)"',
        re.IGNORECASE
    )

    table_match = pattern_table.search(response.text)
    if not table_match:
        logger.warning("Could not find infobox table in Wikipedia page")
        return []

    domains = []
    for span_html in pattern_span.findall(table_match.group(0)):
        for href in pattern_link.findall(span_html):
            parsed = urlparse(href if '://' in href else 'https:' + href)
            if parsed.netloc:
                domains.append(parsed.netloc)

    logger.info(f"Fetched {len(domains)} domain(s) from Wikipedia: {domains}")
    return domains


def is_cache_stale():
    """Return True if the wiki domains cache is missing or older than UPDATE_INTERVAL."""
    try:
        wiki_file = _wiki_domains_file()
        if wiki_file.exists():
            with open(wiki_file, 'r') as f:
                data = json.load(f)
            return time.time() - data.get('timestamp', 0) > UPDATE_INTERVAL
    except Exception:
        pass
    return True


def get_wiki_mirrors():
    """Return cached wiki-only domains (extras not in ANNAS_ARCHIVE_DOMAINS)."""
    try:
        wiki_file = _wiki_domains_file()
        if wiki_file.exists():
            with open(wiki_file, 'r') as f:
                data = json.load(f)
            return data.get('domains', [])
    except Exception as e:
        logger.debug(f"Failed to load wiki domains cache: {e}")
    return []


def update_wiki_domains():
    """Fetch from Wikipedia if stale, store only domains not already in the hardcoded list."""
    if not is_cache_stale():
        return

    from stacks.constants import ANNAS_ARCHIVE_DOMAINS

    fetched = fetch_annas_archive_domains()
    extras = [d for d in fetched if d not in ANNAS_ARCHIVE_DOMAINS]

    try:
        wiki_file = _wiki_domains_file()
        wiki_file.parent.mkdir(parents=True, exist_ok=True)
        with open(wiki_file, 'w') as f:
            json.dump({'domains': extras, 'timestamp': time.time()}, f)
        if extras:
            logger.info(f"Wiki domain update: {len(extras)} new domain(s): {extras}")
        else:
            logger.debug("Wiki domain update: no new domains beyond hardcoded list")
    except Exception as e:
        logger.warning(f"Failed to save wiki domains cache: {e}")
