#!/usr/bin/env bash
set -euo pipefail

# Required: set this in GitHub Secrets -> DEEPWIKI_REBUILD_CMD
# Example:
#   npx -y deepwiki generate --ci
#   python tools/deepwiki/rebuild.py
REBUILD_CMD="${DEEPWIKI_REBUILD_CMD:-}"

if [[ -z "${REBUILD_CMD}" ]]; then
  echo "[deepwiki] DEEPWIKI_REBUILD_CMD is empty."
  echo "[deepwiki] Please set repository secret DEEPWIKI_REBUILD_CMD."
  exit 1
fi

echo "[deepwiki] Running rebuild command..."
echo "[deepwiki] ${REBUILD_CMD}"

# shellcheck disable=SC2086
bash -lc "${REBUILD_CMD}"

echo "[deepwiki] Rebuild finished."
