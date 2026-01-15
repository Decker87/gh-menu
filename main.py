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

class GitHubPRMenuApp(rumps.App):
    def __init__(self):
        super(GitHubPRMenuApp, self).__init__("PRs: -", quit_button="Quit")
        self.api_key = os.environ.get("GH_API_KEY")
        self.pr_items = []

        logger.info("Starting gh-menu app")
        logger.info(f"Log file location: {log_file}")

        if not self.api_key:
            self.title = "⚠️ Set GH_API_KEY env var"
            logger.warning("GH_API_KEY environment variable not set")
            self.menu = ["Set GH_API_KEY environment variable", "See README for instructions"]
        else:
            self.check_prs()
            self.timer = rumps.Timer(self.check_prs, 5)
            self.timer.start()

    def check_prs(self, _=None):
        if not self.api_key:
            return

        try:
            headers = {
                "Authorization": f"token {self.api_key}",
                "Accept": "application/vnd.github.v3+json"
            }

            # Search for PRs where you are requested as a reviewer, sorted by oldest first
            url = "https://api.github.com/search/issues"
            params = {
                "q": "is:open is:pr user-review-requested:@me",
                "sort": "created",
                "order": "asc"
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            pr_count = data.get("total_count", 0)
            items = data.get("items", [])

            # Update menu bar title
            if pr_count == 0:
                self.title = "🟢 PRs: 0"
            else:
                # Get oldest PR details for menu bar
                oldest_pr = items[0]
                author = oldest_pr.get("user", {}).get("login", "unknown")
                title = oldest_pr.get("title", "")

                # Truncate title to ~30 chars
                max_title_length = 30
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
