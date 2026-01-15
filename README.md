# gh-menu

A macOS menu bar application that displays the number of GitHub PRs awaiting your review.

## Quick Start

1. Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Clone this repo and cd into it
3. Set your GitHub token: `export GH_API_KEY="your_token"` (add to `~/.zshrc` for persistence)
4. From the repo directory, run: `nohup uv run main.py > /dev/null 2>&1 &`

**Recommended:** Add this to your `~/.zshrc` so it runs automatically when you open a terminal:
```bash
# Start gh-menu in background
(cd /path/to/gh-menu && nohup uv run main.py > /dev/null 2>&1 &)
```
The script automatically prevents multiple instances from running.

**Stop the app:** `pkill -f "uv run main.py"`

**Logs:** `~/Library/Logs/gh-menu/gh-menu.log`

## How It Works

The app will:
- Display "🟢 PRs: 0" when you have no PRs awaiting review (inbox zero!)
- Display "🔴 PRs: X | [username] PR title..." when you have PRs awaiting review
  - Shows a red circle indicator to catch your attention
  - Shows the count and details of the oldest PR (author + truncated title)
- Check GitHub every 5 seconds for updates
- Show "⚠️ Set GH_API_KEY env var" if the API key is not set
- Show "❌ error message..." if there's an error (shows actual exception details)

Dropdown menu:
- Shows all PRs awaiting review (newest first, oldest at bottom)
- Format: `🔀 [author] PR title... (age)`
- Click any PR to open it in your browser
- Age is calculated from PR creation time
- Auto-refreshes every 5 seconds
- "Quit" button at the bottom to exit the app

## UV Quick Reference

### Project Setup
```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize a new project
uv init

# Add UV bin to PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="$HOME/.local/bin:$PATH"
```

### Managing Dependencies
```bash
# Add a dependency
uv add package-name

# Remove a dependency
uv remove package-name

# Update dependencies
uv lock --upgrade

# Install all dependencies (creates .venv if needed)
uv sync
```

### Running Code
```bash
# Run a script with dependencies
uv run script.py

# Run a command in the virtual environment
uv run python -c "import rumps; print(rumps.__version__)"

# Activate the virtual environment manually
source .venv/bin/activate
```

### Python Version Management
```bash
# Use a specific Python version
uv python pin 3.11

# Install a Python version
uv python install 3.12
```

## Project Structure
- `main.py` - Main menu bar application
- `pyproject.toml` - Project configuration and dependencies
- `.venv/` - Virtual environment (auto-created by UV)

## Dependencies
- `rumps` - Ridiculously Uncomplicated macOS Python Statusbar apps
- `requests` - HTTP library for making API calls to GitHub