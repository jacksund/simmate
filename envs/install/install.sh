#!/bin/sh
# Installs uv (if needed) and then Simmate as a uv tool:
#   curl -LsSf https://simmate.org/install.sh | sh
set -eu

# uv's installer adds itself to PATH through shell configs, which this shell
# hasn't loaded, so we call it from its default install location instead
if command -v uv >/dev/null 2>&1; then
    UV=uv
else
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    UV="$HOME/.local/bin/uv"
fi

echo "Installing Simmate..."
"$UV" tool install --upgrade --python 3.13 "simmate[all]"
# this fails when the shell can't be detected (e.g. $SHELL unset), but uv
# already warns about PATH above, so it shouldn't stop the install
"$UV" tool update-shell || true

cat <<'EOF'

Simmate is installed! Restart your terminal, then run:
    simmate --help

To import simmate in your own Python scripts (or Spyder), create a virtual
environment instead:
    https://jacksund.github.io/simmate/getting_started/installation/create_your_env/
EOF
