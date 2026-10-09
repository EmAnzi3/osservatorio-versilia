#!/usr/bin/env bash
# Shared failed-run memory for primary and manual shadow; no source reset.
set -euo pipefail
previous_run_id="$(
  gh api "repos/${GITHUB_REPOSITORY}/actions/workflows/opportunity-radar-daily.yml/runs?per_page=20" \
    --jq ".workflow_runs | map(select(.id != ${GITHUB_RUN_ID} and .head_branch == \"main\" and .status == \"completed\")) | first | .id // empty"
)"
if [ -z "$previous_run_id" ]; then
  echo "Nessun run precedente: salute fonti inizializzata dallo snapshot accettato."
  exit 0
fi
previous_conclusion="$(
  gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${previous_run_id}" --jq '.conclusion // empty'
)"
if [ "$previous_conclusion" != "failure" ]; then
  echo "Il run precedente ${previous_run_id} non è fallito: salute fonti inizializzata dallo snapshot accettato."
  exit 0
fi
artifact_id="$(
  gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${previous_run_id}/artifacts?per_page=100" \
    --jq '.artifacts | map(select(.name == "opportunity-radar-publishability-diagnostic")) | last | .id // empty'
)"
if [ -z "$artifact_id" ]; then
  echo "Il run fallito ${previous_run_id} non ha diagnostica: uso lo snapshot accettato."
  exit 0
fi
seed_dir="/tmp/opportunity-source-health-seed"
mkdir -p "$seed_dir"
gh api "repos/${GITHUB_REPOSITORY}/actions/artifacts/${artifact_id}/zip" > "$seed_dir/artifact.zip"
unzip -q -o "$seed_dir/artifact.zip" -d "$seed_dir"
seed_path="$seed_dir/opportunity-publishability-diagnostic.json"
if [ ! -s "$seed_path" ]; then
  echo "Artifact diagnostico ${artifact_id} privo del JSON atteso: uso lo snapshot accettato."
  exit 0
fi
echo "OPPORTUNITY_SOURCE_HEALTH_SEED=$seed_path" >> "$GITHUB_ENV"
echo "Salute fonti ereditata dall'artifact diagnostico ${artifact_id}."
