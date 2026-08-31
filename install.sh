#!/usr/bin/env bash
# Installs/updates the smieci_wroclaw custom component on a remote Home Assistant instance over
# SSH — for HA Container / HA Core setups without Supervisor or HACS, where a plain rsync into
# custom_components/ is the only install path. If your Home Assistant has HACS, use that instead
# (see README.md) — it's simpler and handles updates for you.
#
# Usage: ./install.sh <user@host> <remote_config_dir>
# Example: ./install.sh ha@homeassistant.local /home/ha/config

set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <user@host> <remote_config_dir>" >&2
  echo "Example: $0 ha@homeassistant.local /home/ha/config" >&2
  exit 1
fi

REMOTE="$1"
REMOTE_CONFIG_DIR="$2"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/custom_components/smieci_wroclaw"

if [ ! -d "$SRC" ]; then
  echo "Nie znaleziono $SRC" >&2
  exit 1
fi

echo "Kopiowanie $SRC -> $REMOTE:$REMOTE_CONFIG_DIR/custom_components/smieci_wroclaw"
rsync -av --delete \
  --exclude '__pycache__' \
  "$SRC" "$REMOTE:$REMOTE_CONFIG_DIR/custom_components/"

echo "Restart kontenera Home Assistant..."
ssh "$REMOTE" 'cd '"$REMOTE_CONFIG_DIR"'/docker && docker compose restart home-assistant || docker restart home-assistant'

echo "Gotowe. Dodaj integrację w Ustawienia -> Urządzenia i usługi -> Dodaj integrację -> \"Harmonogram odpadow\"."
