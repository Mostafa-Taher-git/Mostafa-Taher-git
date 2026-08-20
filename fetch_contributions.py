#!/usr/bin/env python3
"""Fetch the last year of GitHub contributions into contributions.json.

Requires a token with `read:user` in GITHUB_TOKEN (the default Actions token
works). Usage:

    USERNAME=Mostafa-Taher-git GITHUB_TOKEN=xxx python fetch_contributions.py
"""
import json
import os
import urllib.request

USERNAME = os.environ.get("USERNAME", "Mostafa-Taher-git")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = os.environ.get("DATA", "contributions.json")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
"""

LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def main():
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN is required")
    body = json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "dragon-feeder",
        },
    )
    with urllib.request.urlopen(req) as resp:
        payload = json.load(resp)

    weeks = (payload["data"]["user"]["contributionsCollection"]
             ["contributionCalendar"]["weeks"])
    days = [
        {
            "date": d["date"],
            "count": d["contributionCount"],
            "level": LEVELS.get(d["contributionLevel"], 0),
        }
        for w in weeks for d in w["contributionDays"]
    ]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(days, f)
    print(f"Wrote {OUT} ({len(days)} days)")


if __name__ == "__main__":
    main()
