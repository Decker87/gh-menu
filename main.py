import os
import sys
import webbrowser
import logging
import atexit
from datetime import datetime, timezone
from pathlib import Path
import rumps
import requests

# Setup logging
log_dir = Path.home() / "Library" / "Logs" / "gh-menu"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "gh-menu.log"
pid_file = log_dir / "gh-menu.pid"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_single_instance():
    """Ensure only one instance of gh-menu is running."""
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())

            # Check if process is still running
            try:
                os.kill(old_pid, 0)  # Doesn't actually kill, just checks if process exists
                logger.info(f"Another instance is already running (PID: {old_pid}). Exiting.")
                sys.exit(0)
            except OSError:
                # Process doesn't exist, stale PID file
                logger.info(f"Removing stale PID file (PID: {old_pid})")
        except (ValueError, IOError):
            # Invalid PID file, ignore
            pass

    # Write current PID
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    logger.info(f"Started with PID: {os.getpid()}")

    # Clean up PID file on exit
    atexit.register(lambda: pid_file.unlink(missing_ok=True))

def get_relative_time(created_at_str):
    """Calculate relative time from ISO timestamp."""
    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    delta = now - created_at

    seconds = delta.total_seconds()
    if seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days}d ago"
    else:
        weeks = int(seconds / 604800)
        return f"{weeks}w ago"

def needs_review(headers, pr, current_user):
    """Determine if PR needs review based on push/review timeline."""
    repo_url = pr.get("repository_url", "")
    pr_number = pr.get("number")

    if not repo_url or not pr_number:
        return False

    parts = repo_url.split("/")
    if len(parts) < 2:
        return False

    owner = parts[-2]
    repo = parts[-1]

    try:
        # Get timeline events
        timeline_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/timeline"
        timeline_headers = headers.copy()
        timeline_headers["Accept"] = "application/vnd.github.mockingbird-preview+json"

        timeline_response = requests.get(timeline_url, headers=timeline_headers, timeout=10)
        timeline_response.raise_for_status()
        timeline_events = timeline_response.json()

        # Get reviews
        reviews_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        reviews_response = requests.get(reviews_url, headers=headers, timeout=10)
        reviews_response.raise_for_status()
        reviews = reviews_response.json()

        # Find your last review
        your_reviews = [r for r in reviews if r.get("user", {}).get("login") == current_user]

        # If you haven't reviewed yet, it needs review
        if not your_reviews:
            return True

        # Get your last review timestamp
        last_review = max(your_reviews, key=lambda r: r.get("submitted_at", ""))
        last_review_time = datetime.fromisoformat(last_review.get("submitted_at", "").replace('Z', '+00:00'))

        # Find last commit after your review
        commits = [e for e in timeline_events if e.get("event") == "committed"]
        for commit in reversed(commits):
            commit_date_str = commit.get("committer", {}).get("date", commit.get("author", {}).get("date", ""))
            if commit_date_str:
                commit_time = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
                # If there's a commit after your review, you need to review again
                if commit_time > last_review_time:
                    return True

        # No commits after your last review, so your review is still current
        return False

    except Exception as e:
        logger.error(f"Error checking review status for PR #{pr_number}: {e}")
        # On error, assume it needs review to be safe
        return True

class GitHubPRMenuApp(rumps.App):
    def __init__(self):
        super(GitHubPRMenuApp, self).__init__("PRs: -", quit_button="Quit")
        self.api_key = os.environ.get("GH_API_KEY")
        self.pr_items = []
        self.current_user = None

        logger.info("Starting gh-menu app")
        logger.info(f"Log file location: {log_file}")

        if not self.api_key:
            self.title = "⚠️ Set GH_API_KEY env var"
            logger.warning("GH_API_KEY environment variable not set")
            self.menu = ["Set GH_API_KEY environment variable", "See README for instructions"]
        else:
            # Get current user info
            try:
                headers = {
                    "Authorization": f"token {self.api_key}",
                    "Accept": "application/vnd.github.v3+json"
                }
                user_response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
                user_response.raise_for_status()
                self.current_user = user_response.json().get("login", "")
                logger.info(f"Logged in as: {self.current_user}")
            except Exception as e:
                logger.error(f"Error getting user info: {e}")

            self.check_prs()
            self.timer = rumps.Timer(self.check_prs, 5)
            self.timer.start()

    def check_prs(self, _=None):
        if not self.api_key or not self.current_user:
            return

        try:
            headers = {
                "Authorization": f"token {self.api_key}",
                "Accept": "application/vnd.github.v3+json"
            }

            url = "https://api.github.com/search/issues"

            # Get PRs currently awaiting your review
            params_awaiting = {
                "q": "is:open is:pr user-review-requested:@me",
                "sort": "created",
                "order": "asc",
                "per_page": 100
            }

            response_awaiting = requests.get(url, headers=headers, params=params_awaiting, timeout=10)
            response_awaiting.raise_for_status()
            awaiting_items = response_awaiting.json().get("items", [])

            # Get PRs you've already reviewed
            params_reviewed = {
                "q": "is:open is:pr reviewed-by:@me",
                "sort": "created",
                "order": "asc",
                "per_page": 100
            }

            response_reviewed = requests.get(url, headers=headers, params=params_reviewed, timeout=10)
            response_reviewed.raise_for_status()
            reviewed_items = response_reviewed.json().get("items", [])

            # Combine and deduplicate by PR URL
            seen_urls = set()
            all_items = []
            for pr in awaiting_items + reviewed_items:
                pr_url = pr.get("html_url", "")
                if pr_url and pr_url not in seen_urls:
                    seen_urls.add(pr_url)
                    all_items.append(pr)

            # Sort by created date (oldest first)
            all_items.sort(key=lambda x: x.get("created_at", ""))

            # Filter PRs to only those that need review
            items = []
            for pr in all_items:
                if needs_review(headers, pr, self.current_user):
                    items.append(pr)

            pr_count = len(items)

            # Update menu bar title
            if pr_count == 0:
                self.title = "🟢 PRs: 0"
            else:
                # Get oldest PR details for menu bar
                oldest_pr = items[0]
                author = oldest_pr.get("user", {}).get("login", "unknown")
                title = oldest_pr.get("title", "")

                # Truncate title to ~20 chars
                max_title_length = 20
                if len(title) > max_title_length:
                    title = title[:max_title_length] + "..."

                # Show warning indicator and oldest PR info
                self.title = f"🔴 PRs: {pr_count} | [{author}] {title}"

            # Clear old PR menu items
            for item in self.pr_items:
                if item in self.menu:
                    del self.menu[item]
            self.pr_items = []

            # Add new PR menu items (newest first, so oldest at bottom)
            for pr in reversed(items):
                author = pr.get("user", {}).get("login", "unknown")
                pr_title = pr.get("title", "")
                pr_url = pr.get("html_url", "")
                created_at = pr.get("created_at", "")

                # Truncate title to ~50 chars for menu
                max_title_length = 50
                if len(pr_title) > max_title_length:
                    pr_title = pr_title[:max_title_length] + "..."

                # Calculate age
                age = get_relative_time(created_at)

                # Create menu item text with PR icon
                menu_text = f"🔀 [{author}] {pr_title} ({age})"

                # Create menu item with click handler
                menu_item = rumps.MenuItem(menu_text, callback=lambda _, url=pr_url: webbrowser.open(url))
                self.menu.add(menu_item)
                self.pr_items.append(menu_text)

            logger.info(f"Found {pr_count} PRs awaiting your review")
            if pr_count > 0:
                oldest_pr = items[0]
                author = oldest_pr.get("user", {}).get("login", "unknown")
                logger.info(f"Oldest PR: [{author}] {oldest_pr.get('title', '')}")

        except requests.exceptions.RequestException as e:
            error_msg = str(e)[:50]  # Truncate to keep menu bar readable
            self.title = f"❌ {error_msg}"
            logger.error(f"Error checking GitHub: {e}")
        except Exception as e:
            error_msg = str(e)[:50]  # Truncate to keep menu bar readable
            self.title = f"❌ {error_msg}"
            logger.error(f"Unexpected error: {e}")

def main():
    check_single_instance()
    GitHubPRMenuApp().run()

if __name__ == "__main__":
    main()
