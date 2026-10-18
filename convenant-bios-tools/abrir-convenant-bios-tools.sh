#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [ -x './Convenant-BIOS-Tools' ]; then
  exec './Convenant-BIOS-Tools' "$@"
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3 ausente. No CachyOS: sudo pacman -S --needed python'
  exit 1
fi
exec python3 -E -s convenant_bios_tools.py "$@"
