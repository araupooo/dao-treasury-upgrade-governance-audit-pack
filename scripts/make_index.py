#!/usr/bin/env python3
"""make_index.py — generate docs/index.html from the pack outputs.
Every number in the HTML is copied verbatim from the JSON outputs
(nothing is re-typed), so the page matches the logs by construction.
Usage: make_index.py [packdir]
"""
import html
import json
import os
import sys


def load(packdir, name):
    with open(os.path.join(packdir, "outputs", name)) as f:
        return json.load(f)


def esc(x):
    return html.escape(str(x))


def pct(x):
    return ("%.2f%%" % (x * 100)) if x is not None else "n/a"


def main():
    packdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..")
    outdir = os.path.join(packdir, "outputs")
    docsdir = os.path.join(packdir, "docs")
    os.makedirs(docsdir, exist_ok=True)
    treas = {s: load(packdir, "treasury-%s.json" % s) for s in ("cosmoshub", "osmosis")}
    props = {s: load(packdir, "proposals-%s.json" % s) for s in ("cosmoshub", "osmosis")}
    findings = load(packdir, "findings-scored.json")

    rows_pool = ""
    for slug, t in treas.items():
        ch = t["bond_pool_change"]["denom"]
        now = next((c["amount"] for c in t["community_pool_now"] if c["denom"] == ch), "")
        hist = next((c["amount"] for c in t["community_pool_hist"] if c["denom"] == ch), "")
        d = t["bond_pool_change"]
        rows_pool += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                      "<td>%s</td><td>%s</td></tr>\n" % (
                          esc(t["chain"]), esc(t["latest_height"]), esc(now),
                          esc(t["community_pool_hist_height"]), esc(hist),
                          esc(d["delta_whole"]), esc(d["blocks_span"])))

    rows_props = ""
    for slug, pp in props.items():
        for r in pp["proposals"]:
            q = r["quorum_evaluation"]
            vc = r.get("vote_concentration", {})
            rows_props += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                           "<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n" % (
                               esc(pp["chain"]), esc(r["id"]), esc(r["title"]),
                               esc(r["status"]), pct(q["turnout"]),
                               esc(q["quorum_met"]), pct(q["yes_share_non_abstain"]),
                               pct(vc.get("top10_share")), esc(r["votes_fetched"])))

    rows_find = ""
    for fd in findings:
        rows_find += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n" % (
            esc(fd["id"]), esc(fd["severity"]), esc(fd["title"]),
            esc(fd.get("amount_at_risk", ""))))

    rows_spends = ""
    for slug, t in treas.items():
        for s in t["community_pool_spends_recent"]:
            for a in s["amount"]:
                rows_spends += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                                "<td>%s</td><td>%s</td></tr>\n" % (
                                    esc(t["chain"]), esc(s["proposal_id"]), esc(s["title"]),
                                    esc(s["status"]), esc(a["denom"]), esc(a["amount"])))

    page = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>DAO Treasury and Upgrade-Governance Audit Pack — Evidence Index</title>
<style>body{font-family:system-ui,sans-serif;max-width:1000px;margin:2em auto;padding:0 1em}
table{border-collapse:collapse;margin:1em 0}td,th{border:1px solid #999;padding:.3em .6em;text-align:left}
code{background:#f2f2f2;padding:0 .2em}</style></head><body>
<h1>DAO Treasury and Upgrade-Governance Audit Pack</h1>
<p>Chains audited: <strong>Cosmos Hub (cosmoshub-4)</strong> and <strong>Osmosis (osmosis-1)</strong>.
All figures below are copied verbatim from the JSON outputs in <code>outputs/</code>;
see <code>docs/findings-report.md</code> and <code>docs/decision-memo.md</code> for the
rated findings and the decision memo, and <code>README.md</code> for reproduction commands.
No API key or private credential is needed to rerun the toolkit.</p>
<h2>Community pool balances (bond denom)</h2>
<table><tr><th>Chain</th><th>Height now</th><th>Pool now (base units)</th>
<th>Historical height</th><th>Pool then (base units)</th><th>Delta (whole tokens)</th><th>Blocks span</th></tr>
%s</table>
<h2>Proposals audited</h2>
<table><tr><th>Chain</th><th>ID</th><th>Title</th><th>Status</th><th>Turnout</th>
<th>Quorum met</th><th>Yes share (ex-abstain)</th><th>Top-10 voter stake share</th><th>Votes fetched</th></tr>
%s</table>
<h2>Community-pool spends found (recent scan)</h2>
<table><tr><th>Chain</th><th>Proposal</th><th>Title</th><th>Status</th><th>Denom</th><th>Amount (base units)</th></tr>
%s</table>
<h2>Findings (see docs/findings-report.md for evidence and remediation)</h2>
<table><tr><th>ID</th><th>Severity</th><th>Title</th><th>Amount at risk</th></tr>
%s</table>
<h2>Files</h2>
<ul>
<li><code>scripts/</code> — fetch_treasury.py, audit_proposals.py, score_findings.py, run_all.sh, clean_reproduce.sh, compare_reproduce.py, verify_digests.sh, make_sha256sums.sh, make_index.py</li>
<li><code>src/onchain.py</code> — public-LCD client (retries, backoff, fail-loud), concentration statistics</li>
<li><code>configs/</code> — rubric.md (severity rubric), chain-endpoints.md (pinned endpoints, heights, proposal IDs)</li>
<li><code>outputs/</code> — unedited run logs, treasury/proposal JSON + CSV, findings-scored JSON + CSV</li>
<li><code>fixtures/</code> — proposal and parameter snapshots exactly as fetched</li>
<li><code>docs/</code> — methodology.md, citations.md, evidence-index.md, findings-report.md, decision-memo.md</li>
<li><code>SHA256SUMS</code> — digests of every shipped file; verify with <code>bash scripts/verify_digests.sh</code></li>
</ul>
</body></html>
""" % (rows_pool, rows_props, rows_spends, rows_find)
    with open(os.path.join(docsdir, "index.html"), "w") as f:
        f.write(page)
    print("make_index: wrote %s (%d bytes)" % (os.path.join(docsdir, "index.html"), len(page)))


if __name__ == "__main__":
    main()
