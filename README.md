# gh-menu

A macOS menu bar application that displays the number of GitHub PRs awaiting your review.

![gh-menu screenshot](screenshot.png)

## Quick Start

```bash
# Clone
git clone git@github.com:Decker87/gh-menu.git && cd gh-menu

# Install
./install.sh

# Uninstall
./uninstall.sh
```

The install script will prompt you for your GitHub API key and set everything up to run automatically on login.

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