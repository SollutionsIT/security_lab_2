#!/usr/bin/env sh
set -eu
command -v syft >/dev/null 2>&1 || {
  echo "ERROR: syft is required (see docs/11-supply-chain-security.md)" >&2
  exit 2
}
mkdir -p sbom
syft dir:lab-api -o cyclonedx-json=sbom/lab-api.cdx.json
echo "PASS: wrote sbom/lab-api.cdx.json"
