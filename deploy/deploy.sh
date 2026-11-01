#!/usr/bin/env bash
set -euo pipefail

required=(DEPLOY_HOST DEPLOY_USER SITE_DOMAIN)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    printf 'Missing required environment variable: %s\n' "$name" >&2
    exit 2
  fi
done

if [[ ! "$SITE_DOMAIN" =~ ^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$ ]]; then
  printf 'SITE_DOMAIN must be a valid DNS hostname.\n' >&2
  exit 2
fi

for command in ssh rsync curl; do
  if ! command -v "$command" >/dev/null 2>&1; then
    printf 'Required deployment command not found: %s\n' "$command" >&2
    exit 2
  fi
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
remote="${DEPLOY_USER}@${DEPLOY_HOST}"
remote_dir="earth-trends-detective"
ssh_options=(-o BatchMode=yes)
if [[ -n "${DEPLOY_SSH_KEY:-}" ]]; then
  ssh_options+=(-i "$DEPLOY_SSH_KEY")
fi
printf -v rsync_ssh '%q ' ssh "${ssh_options[@]}"

ssh "${ssh_options[@]}" "$remote" \
  "mkdir -p '$remote_dir/data/processed' '$remote_dir/data/tiles'"
rsync -az -e "$rsync_ssh" \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='web/node_modules/' \
  --exclude='.env' \
  --exclude='data/raw/' \
  --exclude='data/processed/' \
  --exclude='data/tiles/' \
  "$repo_root/" "$remote:$remote_dir/"

# Upload processed variables and map tiles; raw NASA source files stay local.
rsync -az -e "$rsync_ssh" \
  "$repo_root/data/processed/" \
  "$remote:$remote_dir/data/processed/"
rsync -az -e "$rsync_ssh" \
  "$repo_root/data/tiles/" \
  "$remote:$remote_dir/data/tiles/"

ssh "${ssh_options[@]}" "$remote" \
  "cd '$remote_dir' && printf '%s\\n' 'SITE_DOMAIN=$SITE_DOMAIN' > .env && docker compose up --build -d"

curl --fail --silent --show-error --retry 12 --retry-all-errors --retry-delay 5 \
  --retry-max-time 90 "https://$SITE_DOMAIN/api/health"

printf 'Deployment started at https://%s\n' "$SITE_DOMAIN"
