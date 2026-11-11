#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  echo "Create .env from .env.dist before running agent E2E." >&2
  exit 1
fi

suffix="${RANDOM}${RANDOM}"
fresh_project="solar-mars-e2e-fresh-${suffix}"
upgrade_project="solar-mars-e2e-upgrade-${suffix}"
fresh_port="${MARS_E2E_PORT:-$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')}"
upgrade_port="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')"

compose() {
  docker compose --project-name "$1" --profile worker --profile agent "${@:2}"
}

cleanup() {
  for project in "$fresh_project" "$upgrade_project"; do
    docker compose --project-name "$project" down --volumes --remove-orphans >/dev/null 2>&1 || true
  done
}
show_logs_on_failure() {
  local status=$?
  if (( status != 0 )); then
    for project in "$fresh_project" "$upgrade_project"; do
      docker compose --project-name "$project" --profile worker --profile agent logs --no-color >&2 || true
    done
  fi
  return "$status"
}
trap cleanup EXIT
trap show_logs_on_failure ERR

export MARS_AGENT_ENABLED=true MARS_API_PORT="$fresh_port" MARS_DB_PORT=0
export LLM_BASE_URL=http://mars_mock_llm:9000/v1
compose "$fresh_project" up --detach --build --wait mars_api mars_worker mars_mock_llm
api="http://127.0.0.1:${fresh_port}/v1"
curl --fail --silent --show-error --retry 30 --retry-connrefused --retry-delay 2 "$api/health/ready" >/dev/null

response="$(curl --fail --silent --show-error -X POST "$api/runs" \
  -H 'Content-Type: application/json' -H 'Idempotency-Key: solar-e2e-run' \
  -d '{"prompt":"Reply with a short greeting","token_budget":32}')"
run_id="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<<"$response")"
reused="$(curl --fail --silent --show-error -X POST "$api/runs" \
  -H 'Content-Type: application/json' -H 'Idempotency-Key: solar-e2e-run' \
  -d '{"prompt":"Reply with a short greeting","token_budget":32}')"
reused_id="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<<"$reused")"
[[ "$run_id" == "$reused_id" ]]

status_code="$(curl --silent --output /dev/null --write-out '%{http_code}' -X POST "$api/runs" \
  -H 'Content-Type: application/json' -H 'Idempotency-Key: solar-e2e-run' \
  -d '{"prompt":"A different prompt","token_budget":32}')"
[[ "$status_code" == 409 ]]
budget_limit="$(awk -F= '$1 == "RUN_TOKEN_BUDGET" { gsub(/["[:space:]]/, "", $2); print $2; exit }' .env)"
budget_limit="${budget_limit:-256}"
for invalid_budget in 0 "$((budget_limit + 1))"; do
  status_code="$(curl --silent --output /dev/null --write-out '%{http_code}' -X POST "$api/runs" \
    -H 'Content-Type: application/json' -H "Idempotency-Key: invalid-budget-${invalid_budget}" \
    -d "{\"prompt\":\"Invalid budget check\",\"token_budget\":${invalid_budget}}")"
  [[ "$status_code" == 400 ]]
done

completed=false
for _ in {1..60}; do
  run="$(curl --fail --silent --show-error "$api/runs/$run_id")"
  run_status="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])' <<<"$run")"
  if [[ "$run_status" == completed ]]; then
    completed=true
    break
  fi
  if [[ "$run_status" == failed ]]; then
    echo "Agent run failed: $run" >&2
    exit 1
  fi
  sleep 2
done
[[ "$completed" == true ]]
python3 -c 'import json,sys; assert json.load(sys.stdin)["result"]' <<<"$run"
echo "Mars fresh-schema agent E2E passed."

export MARS_API_PORT="$upgrade_port"
compose "$upgrade_project" up --detach --wait mars_db mars_cache
compose "$upgrade_project" run --rm --build --no-deps mars_migrate alembic upgrade 8a4f2c1d9e03
compose "$upgrade_project" run --rm --no-deps mars_migrate
# shellcheck disable=SC2016 # Expand the DB credentials inside the database container.
revision="$(compose "$upgrade_project" exec --no-TTY mars_db sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT version_num FROM alembic_version"')"
[[ "$revision" == 7f6c2e1a9b34 ]]
echo "Mars migration upgrade E2E passed (8a4f2c1d9e03 -> $revision)."
