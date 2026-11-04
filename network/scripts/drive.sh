#!/usr/bin/env bash
# Mount Google Drive read-only at ~/gdrive, so field data are read in place (the laptop disk is nearly full).
# Colab's /content/drive/MyDrive/X is ~/gdrive/X here, e.g. ~/gdrive/IC/Sideseeing/UIC/data/west_loop.
#
# One-time setup (opens a browser to sign in):  rclone config create gdrive drive scope=drive.readonly
# Usage:  network/scripts/drive.sh mount | unmount | status
set -euo pipefail
RCLONE=${RCLONE:-$HOME/.local/bin/rclone}
MNT=$HOME/gdrive

case "${1:-mount}" in
  mount)
    mkdir -p "$MNT"
    mountpoint -q "$MNT" && { echo "already mounted at $MNT"; exit 0; }
    # Files read are cached locally; the cache is capped at 5 GB and dropped after 24 h.
    "$RCLONE" mount gdrive: "$MNT" --read-only --daemon \
      --vfs-cache-mode full --vfs-cache-max-size 5G --vfs-cache-max-age 24h --dir-cache-time 1h
    echo "mounted at $MNT" ;;
  unmount) fusermount -u "$MNT" && echo "unmounted $MNT" ;;
  status) mountpoint "$MNT" && ls "$MNT/IC/Sideseeing/UIC/data/west_loop" | head ;;
  *) echo "usage: $0 mount|unmount|status"; exit 1 ;;
esac
