#!/usr/bin/env bash
set -euo pipefail

CLI_BIN="${CLI_BIN:-/Applications/wechatwebdevtools.app/Contents/MacOS/cli}"
PROJECT_PATH="${PROJECT_PATH:-/Users/ilovemeiya/WeChatProjects/miniprogram-1}"
LANG_OPT="${LANG_OPT:-zh}"
VERSION="${1:-$(date +%y.%m.%d%H%M)}"
DESC="${2:-CLI pre-release check}"
INFO_OUTPUT="${INFO_OUTPUT:-$PROJECT_PATH/upload-check.json}"

if [[ ! -x "$CLI_BIN" ]]; then
  echo "[ERROR] CLI binary not found: $CLI_BIN"
  exit 1
fi

if [[ ! -d "$PROJECT_PATH" ]]; then
  echo "[ERROR] Project path not found: $PROJECT_PATH"
  exit 1
fi

run_preflight_checks() {
  local app_json="$PROJECT_PATH/app.json"
  local app_js="$PROJECT_PATH/app.js"
  local index_js="$PROJECT_PATH/pages/index/index.js"
  local tag_service="$PROJECT_PATH/utils/tagService.js"

  if [[ ! -f "$app_json" ]]; then
  echo "[ERROR] app.json not found: $app_json"
  exit 1
  fi

  echo "[preflight] checking project config"
  python3 - "$app_json" "$app_js" "$index_js" "$tag_service" <<'PY'
import json
import pathlib
import re
import sys

app_json_path = pathlib.Path(sys.argv[1])
app_js_path = pathlib.Path(sys.argv[2])
index_js_path = pathlib.Path(sys.argv[3])
tag_service_path = pathlib.Path(sys.argv[4])

data = json.loads(app_json_path.read_text(encoding="utf-8"))
permission = data.get("permission") or {}
errors = []
warnings = []

for scope_name, scope_cfg in permission.items():
  desc = ""
  if isinstance(scope_cfg, dict):
    desc = scope_cfg.get("desc") or ""
  desc_len = len(desc)
  if not desc:
    errors.append(f"{scope_name} desc is empty")
  elif desc_len > 30:
    errors.append(f"{scope_name} desc exceeds 30 chars ({desc_len}): {desc}")

def read_text(path: pathlib.Path) -> str:
  if not path.exists():
    return ""
  return path.read_text(encoding="utf-8")

app_js = read_text(app_js_path)
index_js = read_text(index_js_path)
tag_service = read_text(tag_service_path)

if re.search(r'const\s+CLOUD_ENV_ID\s*=\s*""', app_js):
  warnings.append("CLOUD_ENV_ID is empty; cloud capabilities stay disabled")

if re.search(r'const\s+QQ_MAP_KEY\s*=\s*""', index_js):
  warnings.append("QQ_MAP_KEY is empty; reverse geocoding falls back to coordinates only")

if re.search(r'mode:\s*"selfHosted"', tag_service) and re.search(r'url:\s*""', tag_service):
  warnings.append("TAG_PROVIDER.selfHosted.url is empty; image tag analysis returns empty tags")

if re.search(r'mode:\s*"tencentCloud"', tag_service) and re.search(r'env:\s*""', tag_service):
  warnings.append("TAG_PROVIDER.tencentCloud.env is empty; cloud tag analysis cannot run")

for warning in warnings:
  print(f"[WARN] {warning}")

if errors:
  for error in errors:
    print(f"[ERROR] {error}")
  sys.exit(1)

print("[OK] preflight checks passed")
PY
}

run_preflight_checks

echo "[1/4] islogin"
"$CLI_BIN" islogin --lang "$LANG_OPT"

echo "[2/4] preview"
"$CLI_BIN" preview --project "$PROJECT_PATH" --lang "$LANG_OPT"

echo "[3/4] upload"
"$CLI_BIN" upload \
  --project "$PROJECT_PATH" \
  --lang "$LANG_OPT" \
  --version "$VERSION" \
  --desc "$DESC" \
  --info-output "$INFO_OUTPUT"

echo "[4/4] done"
echo "[DONE] version=$VERSION"
echo "[DONE] info-output=$INFO_OUTPUT"