"""Shared on-chain client and statistics helpers for the DAO treasury and
upgrade-governance audit pack.

Only public, no-key HTTP endpoints are used (Cosmos SDK LCD / REST).
Every request retries with exponential backoff on 403/429/5xx and on
transport errors, and raises (fail-loud) after the retry budget is spent,
so a broken endpoint can never silently produce an empty result.
"""

import hashlib
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "dao-treasury-audit-pack/1.0 (independent verification; public LCD)"
REQUEST_DELAY_S = 0.5          # polite gap between requests to one LCD
MAX_RETRIES = 5
BACKOFF_BASE_S = 5.0


class FetchError(RuntimeError):
    pass


def get_json(url, height=None, timeout=30):
    """GET a JSON document from a public LCD endpoint. Raises FetchError
    after retries are exhausted. `height` adds the x-cosmos-block-height
    header for a historical query."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if height is not None:
        headers["x-cosmos-block-height"] = str(height)
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
            time.sleep(REQUEST_DELAY_S)
            data = json.loads(body)
            if isinstance(data, dict) and "code" in data and data.get("code") not in (0,):
                # LCD-level error payload, e.g. {"code": 12, "message": "Not Implemented"}
                raise FetchError("LCD error %s for %s: %s" % (data.get("code"), url, data.get("message")))
            return data
        except FetchError:
            raise
        except urllib.error.HTTPError as e:
            last_err = "HTTP %s for %s" % (e.code, url)
            if e.code in (403, 429, 500, 502, 503, 504):
                time.sleep(BACKOFF_BASE_S * (2 ** attempt))
                continue
            raise FetchError(last_err)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = "%s for %s" % (type(e).__name__, url)
            time.sleep(BACKOFF_BASE_S * (2 ** attempt))
    raise FetchError("FAILED after %d retries: %s" % (MAX_RETRIES, last_err))


def get_json_optional(url, height=None, timeout=30):
    """Like get_json but returns None instead of raising when the LCD
    answers with an error payload (used only for endpoints that are
    documented as possibly unimplemented, e.g. mint on Osmosis).
    Transport failures still raise."""
    try:
        return get_json(url, height=height, timeout=timeout)
    except FetchError:
        return None


def paginate(base_url, key, limit=100, timeout=30):
    """Follow LCD pagination (pagination.next_key) and return the full
    list under `key`. Raises FetchError on any page failure."""
    items = []
    next_key = None
    while True:
        url = base_url + ("&" if "?" in base_url else "?") + "pagination.limit=%d" % limit
        if next_key:
            url += "&pagination.key=" + urllib.parse.quote(next_key, safe="")
        data = get_json(url, timeout=timeout)
        items.extend(data.get(key, []))
        pg = data.get("pagination", {}) or {}
        next_key = pg.get("next_key")
        if not next_key:
            return items


def ibc_denom_hash(path):
    """IBC denom hash for a trace path, e.g.
    'transfer/channel-220/erc20:0xa00C...'. Returns the uppercase hex
    digest; the on-chain denom is 'ibc/' + this value."""
    return hashlib.sha256(path.encode("utf-8")).hexdigest().upper()


def to_base_units(amount_str, decimals):
    """Convert a decimal-coin amount string to integer base units."""
    return int(round(float(amount_str) * (10 ** decimals)))


def from_base_units(amount_int, decimals):
    return amount_int / (10 ** decimals)


def concentration(values):
    """Top-1/4/10 shares, Herfindahl-Hirschman Index (0..1) and Gini
    coefficient over a list of non-negative weights. Returns a dict of
    floats/ints; empty input yields None fields."""
    vals = sorted((float(v) for v in values), reverse=True)
    total = sum(vals)
    n = len(vals)
    if n == 0 or total <= 0:
        return {"n": n, "total": total, "top1_share": None, "top4_share": None,
                "top10_share": None, "hhi": None, "gini": None}
    def share(k):
        return sum(vals[:k]) / total
    hhi = sum((v / total) ** 2 for v in vals)
    # Gini over ascending values
    asc = sorted(vals)
    cum = 0.0
    for i, v in enumerate(asc, start=1):
        cum += (2 * i - n - 1) * v
    gini = cum / (n * total) if n > 0 and total > 0 else None
    return {"n": n, "total": total,
            "top1_share": share(1), "top4_share": share(4),
            "top10_share": share(10), "hhi": hhi, "gini": gini}


def quorum_outcome(tally, bonded_tokens, quorum, threshold, veto_threshold):
    """Evaluate a governance tally against quorum/threshold/veto rules.
    All token amounts are integers in base units. Returns a dict with
    turnout, quorum met, yes share of non-abstain votes, veto share,
    and the pass/fail verdict under the standard Cosmos SDK tally rule
    (yes > threshold of (yes+no+veto); veto < veto_threshold of all
    votes incl. abstain; turnout >= quorum)."""
    yes = int(tally.get("yes_count", 0))
    no = int(tally.get("no_count", 0))
    abstain = int(tally.get("abstain_count", 0))
    veto = int(tally.get("no_with_veto_count", 0))
    total_voted = yes + no + abstain + veto
    counted = yes + no + veto  # abstain counts toward quorum, not toward threshold
    turnout = total_voted / bonded_tokens if bonded_tokens else None
    quorum_met = turnout is not None and turnout >= quorum
    yes_share = yes / counted if counted else None
    veto_share = veto / total_voted if total_voted else None
    passes = bool(quorum_met and yes_share is not None and yes_share > threshold
                  and veto_share is not None and veto_share < veto_threshold)
    return {"yes": yes, "no": no, "abstain": abstain, "veto": veto,
            "total_voted": total_voted, "turnout": turnout,
            "quorum": quorum, "quorum_met": quorum_met,
            "yes_share_non_abstain": yes_share,
            "veto_share": veto_share, "passes_by_tally": passes}
