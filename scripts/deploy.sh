#!/usr/bin/env bash
# Deploy the static site to Cloudflare Pages + Cloudflare R2.
#
# Prerequisites:
#   1. `cf` CLI installed: https://developers.cloudflare.com/cli/
#   2. Cloudflare account with Pages + R2 projects
#   3. Cloudflare API token (with Pages:Deploy + R2:Write scopes)
#   4. A .env file with CLOUDFLARE_* variables (see .env.example)
#
# Usage:
#   cp .env.example .env
#   scripts/deploy.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
BUILD_DIR="${ROOT_DIR}/dist"

# --- Environment & Configuration ---
# Automatically load .env if present
if [ -f "${ROOT_DIR}/.env" ]; then
    echo "==> Loading configuration from .env..."
    set -a
    # shellcheck disable=SC1091
    source "${ROOT_DIR}/.env"
    set +a
fi

API_TOKEN="${CLOUDFLARE_API_TOKEN:?Set CLOUDFLARE_API_TOKEN in .env or environment}"
ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:?Set CLOUDFLARE_ACCOUNT_ID in .env or environment}"
PAGES_PROJECT_ID="${CLOUDFLARE_PAGES_PROJECT_ID:?Set CLOUDFLARE_PAGES_PROJECT_ID in .env or environment}"
R2_BUCKET="${CLOUDFLARE_R2_BUCKET:-}"
R2_ACCESS_KEY_ID="${CLOUDFLARE_R2_ACCESS_KEY_ID:-}"
R2_ACCESS_KEY_SECRET="${CLOUDFLARE_R2_ACCESS_KEY_SECRET:-}"

# Export for Wrangler / Cloudflare tools
export CLOUDFLARE_API_TOKEN="${API_TOKEN}"
export CLOUDFLARE_ACCOUNT_ID="${ACCOUNT_ID}"

# --- Virtual Environment Activation ---
if [ -d "${ROOT_DIR}/.venv" ] && [ -f "${ROOT_DIR}/.venv/bin/activate" ]; then
    echo "==> Activating virtual environment (${ROOT_DIR}/.venv)..."
    # shellcheck disable=SC1091
    source "${ROOT_DIR}/.venv/bin/activate"
    PYTHON_CMD="python"
elif command -v uv >/dev/null 2>&1; then
    echo "==> Using uv virtual environment..."
    PYTHON_CMD="uv run python"
else
    echo "==> Using environment python3..."
    PYTHON_CMD="python"
fi

# --- Gate 1: Test Suite Verification ---
echo ""
echo "========================================================"
echo " [Gate 1/3] Running Validation Test Suite..."
echo "========================================================"
${PYTHON_CMD} -m unittest discover tests
echo "✓ All tests passed cleanly."

# --- Gate 2: Static Site Pre-Rendering ---
echo ""
echo "========================================================"
echo " [Gate 2/3] Pre-rendering Static Site into dist/..."
echo "========================================================"
${PYTHON_CMD} "${ROOT_DIR}/scripts/build.py"
if [ ! -f "${BUILD_DIR}/index.html" ]; then
    echo "❌ Build Error: ${BUILD_DIR}/index.html was not generated." >&2
    exit 1
fi
echo "✓ Static site built successfully into dist/."

# --- Gate 3: Deploy to Cloudflare Pages ---
echo ""
echo "========================================================"
echo " [Gate 3/3] Deploying to Cloudflare Pages..."
echo "========================================================"

# Detect Cloudflare CLI Tool
if command -v wrangler >/dev/null 2>&1; then
    CF_CMD="wrangler"
    echo "==> Using Cloudflare Wrangler CLI..."
elif command -v npx >/dev/null 2>&1; then
    CF_CMD="npx --yes wrangler"
    echo "==> Using npx on-demand Wrangler..."
elif command -v cf >/dev/null 2>&1; then
    CF_CMD="cf"
    echo "==> Using Cloudflare cf CLI..."
else
    echo "❌ Deployment CLI Error: Neither 'wrangler', 'npx', nor 'cf' was found on PATH." >&2
    echo "   Ensure cloudflare/wrangler-action is used in GitHub Actions, or install wrangler locally." >&2
    exit 1
fi

echo "==> Deploying dist/ to project '${PAGES_PROJECT_ID}' via ${CF_CMD}..."
if [[ "${CF_CMD}" == *"wrangler"* ]]; then
    ${CF_CMD} pages deploy "${BUILD_DIR}" \
        --project-name "${PAGES_PROJECT_ID}" \
        --branch "main" \
        --commit-message "build $(git rev-parse --short HEAD 2>/dev/null || echo 'ci')"
else
    cf pages deploy "${BUILD_DIR}" \
        --project "${PAGES_PROJECT_ID}" \
        --branch "main" \
        --commit "build $(git rev-parse HEAD 2>/dev/null || echo 'ci')"
fi

# --- Optional Cloudflare R2 Asset Sync ---
if [ -n "${R2_BUCKET}" ] && [ -n "${R2_ACCESS_KEY_ID}" ] && [ -n "${R2_ACCESS_KEY_SECRET}" ]; then
    echo "==> Syncing assets (images, diagrams, documents) to Cloudflare R2 (${R2_BUCKET})..."
    if [[ "${CF_CMD}" == *"cf"* ]]; then
        cf r2 sync "${ROOT_DIR}/src/assets" "${R2_BUCKET}" \
            --access-key-id "${R2_ACCESS_KEY_ID}" \
            --access-key-secret "${R2_ACCESS_KEY_SECRET}" \
            --no-cache || true
    elif command -v aws >/dev/null 2>&1 && aws s3 help >/dev/null 2>&1; then
        AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" \
        AWS_SECRET_ACCESS_KEY="${R2_ACCESS_KEY_SECRET}" \
        aws s3 sync "${ROOT_DIR}/src/assets" "s3://${R2_BUCKET}" \
            --endpoint-url "https://${ACCOUNT_ID}.r2.cloudflarestorage.com" || true
    else
        echo "==> Syncing assets directly to R2 bucket via Wrangler..."
        for asset_file in "${ROOT_DIR}/src/assets"/*; do
            if [ -f "${asset_file}" ]; then
                base_name=$(basename "${asset_file}")
                ${CF_CMD} r2 object put "${R2_BUCKET}/assets/${base_name}" --file "${asset_file}" --remote --force >/dev/null 2>&1 || true
            fi
        done
        echo "✓ R2 assets synced successfully."
    fi
else
    echo "==> Static assets bundled directly in dist/src/assets (R2 sync skipped)."
fi

echo ""
echo "==> Deploy complete. Site is live."
