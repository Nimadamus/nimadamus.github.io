#!/usr/bin/env bash
# Push the commit a bot workflow just made, then deploy it.
#
# Why (Oct 1 2026): pushes made with GITHUB_TOKEN never trigger the push-based
# pages-deploy.yml, so daily bot commits (hub, records, NHL data, injuries)
# sat in main without going live until a person pushed something. Several jobs
# also ended with `git push || echo ...`, so a failed push still showed green.
#
# This script rebases and pushes (3 attempts), then dispatches pages-deploy.yml.
# Any failure exits non-zero so the run turns red. Needs GH_TOKEN in the env and
# `permissions: contents: write, actions: write` on the job.
set -uo pipefail

if [ "$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)" = "0" ]; then
  echo "ci_push_and_deploy: nothing to push"
  exit 0
fi

pushed=0
for i in 1 2 3; do
  if git pull --rebase origin main && git push origin HEAD:main; then
    pushed=1
    break
  fi
  echo "ci_push_and_deploy: push attempt $i failed, retrying"
  git rebase --abort 2>/dev/null || true
  sleep $((i * 5))
done
if [ "$pushed" != "1" ]; then
  echo "::error::ci_push_and_deploy: push failed after 3 attempts"
  exit 1
fi
echo "ci_push_and_deploy: pushed $(git rev-parse --short HEAD)"

if ! gh workflow run pages-deploy.yml --ref main; then
  echo "::error::ci_push_and_deploy: pushed, but dispatching pages-deploy.yml failed; the change is NOT live"
  exit 1
fi
echo "ci_push_and_deploy: pages-deploy.yml dispatched"
