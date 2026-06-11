#!/bin/bash
# Launcher script for macOS — sets fork safety env vars before Python starts.
# Usage: ./run.sh

export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export no_proxy="*"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Use venv if available
if [ -f "$SCRIPT_DIR/.venv/bin/streamlit" ]; then
    exec "$SCRIPT_DIR/.venv/bin/streamlit" run "$SCRIPT_DIR/app/streamlit_app.py" "$@"
else
    exec streamlit run "$SCRIPT_DIR/app/streamlit_app.py" "$@"
fi
