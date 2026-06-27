#!/usr/bin/env bash
set -e

INSTALL_DIR="$HOME/.spotlight"
BIN_DIR="$HOME/.local/bin"

# Step 1: clone or update the project
if [ -d "$INSTALL_DIR" ]; then
  echo "[spotlight] Updating existing installation..."
  cd "$INSTALL_DIR" && git pull
else
  echo "[spotlight] Installing to $INSTALL_DIR ..."
  git clone https://github.com/YOUR_USERNAME/spotlight.git "$INSTALL_DIR"
fi

# Step 2: install Python dependencies
pip install -q -r "$INSTALL_DIR/requirements.txt"

# Step 3: create executable symlink
mkdir -p "$BIN_DIR"
ln -sf "$INSTALL_DIR/spotlight.py" "$BIN_DIR/spotlight"
chmod +x "$INSTALL_DIR/spotlight.py"

# Step 4: prompt for API key

echo "[spotlight] ✅ Installation complete!"
echo ""
echo "Next step: set your API key"
echo "  export OPENAI_API_KEY=your_key_here"
echo ""
echo "Then run: spotlight"
echo ""

# Step 5: warn if ~/.local/bin is not in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo "[spotlight] ⚠️  Add this to your shell config:"
  echo '  export PATH="$HOME/.local/bin:$PATH"'
fi
