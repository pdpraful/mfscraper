#!/bin/bash
set -e

echo "=========================================="
echo "Installing International MF Capacity Agent"
echo "=========================================="

# 1. Ensure we are in the script's directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 2. Setup Virtual Environment
echo "[1/4] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Install Python Dependencies
echo "[2/4] Installing Python dependencies..."
pip install -r requirements.txt
playwright install chromium

# 4. Make wrapper executable
echo "[3/4] Configuring CLI wrapper..."
chmod +x mfscraper.sh

# 5. Link the tool globally
echo "[4/4] Linking 'mfscraper' command globally..."
# Determine the user's shell profile file
PROFILE=""
if [ -n "$ZSH_VERSION" ] || [ -f "$HOME/.zshrc" ]; then
    PROFILE="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ] || [ -f "$HOME/.bashrc" ]; then
    PROFILE="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    PROFILE="$HOME/.bash_profile"
fi

if [ -n "$PROFILE" ]; then
    # Check if alias already exists
    if ! grep -q "alias mfscraper=" "$PROFILE"; then
        echo -e "\nalias mfscraper=\"$DIR/mfscraper.sh\"" >> "$PROFILE"
        echo "✅ Alias added to $PROFILE"
    else
        echo "ℹ️  Alias already exists in $PROFILE"
    fi
else
    echo "⚠️  Could not automatically determine your shell profile (.zshrc or .bashrc)."
    echo "Please add the following alias manually:"
    echo "alias mfscraper=\"$DIR/mfscraper.sh\""
fi

# 6. Setup Email Configuration
echo "[5/5] Setting up Email Configuration..."
if [ ! -f ".env" ]; then
    echo "Would you like to configure your daily email reports now? (y/n)"
    read -r -p "> " setup_email < /dev/tty || true
    if [[ "$setup_email" =~ ^[Yy]$ ]]; then
        read -r -p "Enter your Gmail address: " email < /dev/tty || true
        read -r -p "Enter your 16-character Google App Password: " app_pass < /dev/tty || true
        
        echo "SMTP_SERVER=smtp.gmail.com" > .env
        echo "SMTP_PORT=587" >> .env
        echo "SMTP_USERNAME=$email" >> .env
        echo "SMTP_PASSWORD=$app_pass" >> .env
        echo "EMAIL_TO=$email" >> .env
        echo "✅ .env file created successfully!"
    else
        echo "ℹ️  Skipping email setup. You can configure it later in $DIR/.env"
    fi
else
    echo "ℹ️  .env file already exists. Skipping email setup."
fi

echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Please restart your terminal or run the following command to use the tool immediately:"
if [ -n "$PROFILE" ]; then
    echo "source $PROFILE"
fi
echo ""
echo "Then, you can run:"
echo "  mfscraper --runonce    # To run a manual data sweep"
echo "  mfscraper --daemon     # To start the daily background scheduler"
