#!/usr/bin/env python3
"""Render a factual GitHub public-activity snapshot as an SVG for the profile README.

Only calls the public GitHub REST API. No personal profile details or arbitrary HTML
are injected into the output. Designed for GitHub Actions on a daily schedule.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
import urllib.request

USER = "aakashghartichhetri"
API = "https://api.github.com"


def fetch_json(path: str) -> dict | list:
    url = API + path
    headers = {
        "User-Agent": "aakash-profile-public-activity/1.0",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def one_line(value: object, limit: int = 62) -> str:
    s = re.sub(r"\s+", " ", str(value or "")).strip()
    return s if len(s) <= limit else s[:limit - 1] + "…"


def summarize_event(events: list) -> tuple[str, str, str]:
    """Summarize the latest public event only; don't invent a commit count or title."""
    if not events:
        return "No recent public activity available", "Events API returns a limited window", ""
    item = next((e for e in events if isinstance(e, dict) and e.get("repo", {}).get("name")), None)
    if not item:
        return "No public repository event available", "Events API response has no usable repository event", ""
    event_type = item.get("type", "Event")
    repo = one_line(item.get("repo", {}).get("name", "unknown"), 60)
    action = one_line(item.get("payload", {}).get("action", ""), 20)
    event_display = {
        "PushEvent": "Pushed changes",
        "PullRequestEvent": "Pull request activity",
        "IssuesEvent": "Issue activity",
        "IssueCommentEvent": "Issue discussion",
        "CreateEvent": "Created a Git reference",
        "DeleteEvent": "Removed a Git reference",
        "WatchEvent": "Starred a repository",
        "ForkEvent": "Forked a repository",
        "ReleaseEvent": "Release activity",
        "PullRequestReviewEvent": "Reviewed a pull request",
    }.get(event_type, "Public GitHub activity")
    if action and event_type not in ("PushEvent", "CreateEvent", "DeleteEvent"):
        event_display += f" · {action}"
    when = item.get("created_at", "")
    date = ""
    if when:
        try:
            date = datetime.fromisoformat(when.replace("Z", "+00:00")).strftime("%d %b %Y")
        except ValueError:
            pass
    return one_line(event_display, 60), repo, date


def render_svg(user: dict, events: list, checked_at: datetime) -> str:
    count = user.get("public_repos")
    if not isinstance(count, int) or count < 0:
        raise ValueError("Expected public_repos to be a nonnegative integer")
    event_title, repo_name, event_date = summarize_event(events)
    checked = checked_at.astimezone(timezone.utc).strftime("%d %b %Y · %H:%M UTC")
    # Escaping is important: GitHub metadata may contain characters meaningful to XML.
    def x(v: object) -> str:
        return escape(one_line(v, 65), quote=True)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="205" viewBox="0 0 960 205" role="img" aria-label="Latest available public GitHub activity snapshot">
<defs>
  <linearGradient id="background" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#10192f"/><stop offset="0.7" stop-color="#162d47"/><stop offset="1" stop-color="#24204d"/></linearGradient>
</defs>
<rect x="1" y="1" width="958" height="203" rx="20" fill="url(#background)" stroke="#315c83" stroke-width="2"/>
<circle cx="40" cy="35" r="6" fill="#55e7cb"/>
<text x="59" y="41" font-size="19" font-family="Arial,sans-serif" font-weight="bold" fill="#d8efff">PUBLIC ACTIVITY SNAPSHOT</text>
<text x="918" y="39" font-size="13" font-family="monospace" text-anchor="end" fill="#99bdd5">UPDATED {x(checked)}</text>
<line x1="30" y1="59" x2="930" y2="59" stroke="#355b7b" stroke-width="1"/>
<text x="40" y="91" font-size="13" font-family="monospace" fill="#9bb9d0">PUBLIC REPOS</text>
<text x="40" y="140" font-size="44" font-family="Arial,sans-serif" font-weight="bold" fill="#70f3ef">{count}</text>
<line x1="200" y1="75" x2="200" y2="160" stroke="#355b7b" stroke-width="1"/>
<text x="235" y="91" font-size="13" font-family="monospace" fill="#9bb9d0">LATEST AVAILABLE PUBLIC EVENT</text>
<text x="235" y="119" font-size="23" font-family="Arial,sans-serif" font-weight="bold" fill="#e4f0ff">{x(event_title)}</text>
<text x="235" y="145" font-size="17" font-family="monospace" fill="#81d7ee">{x(repo_name)}</text>
<text x="917" y="145" font-size="15" font-family="monospace" text-anchor="end" fill="#a9b8ce">{x(event_date)}</text>
<text x="40" y="187" font-size="13" font-family="Arial,sans-serif" fill="#aec2d6">Source: GitHub public REST API · Daily snapshot, not a live connection · Private activity is excluded</text>
</svg>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("dist/public-activity.svg"))
    parser.add_argument("--fixture", type=Path, help="For local test/preview only: input JSON fixture")
    args = parser.parse_args()
    if args.fixture:
        data = json.loads(args.fixture.read_text(encoding="utf-8"))
        user, events = data["user"], data["events"]
    else:
        user = fetch_json(f"/users/{USER}")
        events = fetch_json(f"/users/{USER}/events/public?per_page=30")
    if not isinstance(user, dict) or not isinstance(events, list):
        raise ValueError("Unexpected GitHub API response shape")
    output = render_svg(user, events, datetime.now(timezone.utc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote {args.output} from {'fixture' if args.fixture else 'public GitHub API'}")


if __name__ == "__main__":
    main()
