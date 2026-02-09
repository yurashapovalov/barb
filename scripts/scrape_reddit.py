"""Scrape r/futures posts and comments via PullPush API."""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

SUBREDDIT = "FuturesTrading"
DAYS_BACK = 30
OUTPUT_DIR = Path(__file__).parent / "reddit_data"

BASE_URL = "https://api.pullpush.io/reddit"


def fetch_submissions(subreddit: str, after: int, before: int) -> list[dict]:
    """Fetch all submissions in date range."""
    submissions = []
    current_before = before
    seen_ids = set()

    while True:
        params = {
            "subreddit": subreddit,
            "after": after,
            "before": current_before,
            "size": 100,
            "sort": "desc",
            "sort_type": "created_utc",
        }

        print(f"  Fetching posts before {datetime.fromtimestamp(current_before)}...")

        try:
            resp = requests.get(f"{BASE_URL}/search/submission/", params=params, timeout=30)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("    Rate limited, waiting 60s...")
                time.sleep(60)
                continue
            raise

        data = resp.json().get("data", [])
        if not data:
            break

        # Filter out duplicates
        new_posts = [p for p in data if p["id"] not in seen_ids]
        if not new_posts:
            break  # No new posts, we're done

        for p in new_posts:
            seen_ids.add(p["id"])

        submissions.extend(new_posts)
        print(f"    Got {len(new_posts)} new posts, total: {len(submissions)}")

        # Next page: before oldest post in this batch
        current_before = min(p["created_utc"] for p in data) - 1

        # Rate limit
        time.sleep(1.5)

    return submissions


def fetch_comments(submission_id: str) -> list[dict]:
    """Fetch comments for a submission."""
    params = {
        "link_id": submission_id,
        "size": 100,
    }

    resp = requests.get(f"{BASE_URL}/search/comment/", params=params, timeout=30)
    resp.raise_for_status()

    return resp.json().get("data", [])


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # PullPush has ~9 month lag, use May 2025 as "now"
    pullpush_latest = datetime(2025, 5, 19)
    after = int((pullpush_latest - timedelta(days=DAYS_BACK)).timestamp())
    before = int(pullpush_latest.timestamp())

    print(f"Scraping r/{SUBREDDIT} for last {DAYS_BACK} days...")
    print(f"  From: {datetime.fromtimestamp(after)}")
    print(f"  To:   {datetime.fromtimestamp(before)}")

    # Fetch submissions
    submissions = fetch_submissions(SUBREDDIT, after, before)
    print(f"\nTotal submissions: {len(submissions)}")

    # Save posts (skip comments to avoid rate limits)
    output_file = OUTPUT_DIR / f"{SUBREDDIT}_{DAYS_BACK}d.json"
    with open(output_file, "w") as f:
        json.dump(submissions, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {output_file}")
    print(f"Total posts: {len(submissions)}")


if __name__ == "__main__":
    main()
