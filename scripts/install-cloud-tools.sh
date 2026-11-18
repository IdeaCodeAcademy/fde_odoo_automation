#!/usr/bin/env bash
set -euo pipefail

# Run during Cloud environment setup, before starting the task session.
# Keep the environment's configured source revisions; do not silently git pull.
fde_cloud_root="${FDE_CLOUD_ROOT:-/workspace}"
fde_project_root="$fde_cloud_root/fde_odoo_automation"
python3 "$fde_project_root/scripts/sync_cloud_skills.py" \
  --source "$fde_cloud_root/odoo/skills" \
  --target "$fde_project_root/.agents/skills" \
  --target "$fde_cloud_root/odoo/.agents/skills"

# ECC uses the native plugin lifecycle; never copy its skill directories.
# The marketplace source is a configured local checkout, not a remote
# marketplace to upgrade. Its revision is managed by the Cloud environment.
codex plugin marketplace add "$fde_cloud_root/ecc"
codex plugin add ecc@ecc
codex plugin list --json

fde_ecc_version=$(node -p "require(process.argv[1]).version" "$fde_cloud_root/ecc/package.json")
fde_ecc_cache="${CODEX_HOME:-$HOME/.codex}/plugins/cache/ecc/ecc/$fde_ecc_version"
(
  cd "$fde_ecc_cache"
  npm ci --omit=dev --ignore-scripts --no-audit --no-fund --no-bin-links
  node -e "for (const p of ['js-yaml','@iarna/toml','ajv','sql.js','zod']) require(p)"
)
node "$fde_cloud_root/ecc/scripts/codex/check-plugin-cache.js" --plugin-dir "$fde_ecc_cache"
