#!/usr/bin/env bash
# ============================================================
# APLICA LA PROTECCIÓN DE LA RAMA main (branch protection rules)
# ============================================================
# Con esta regla GitHub NO permite:
#   - hacer push directo a main (todo entra por Pull Request),
#   - hacer merge si algún check obligatorio del pipeline falla,
#   - hacer force push o borrar la rama.
# "enforce_admins": la regla también aplica al dueño del repositorio.
#
# Requiere un token con permiso de administración del repositorio
# (classic: scope "repo"; fine-grained: "Administration: write").
# Se ejecuta UNA vez, desde tu equipo:
#
#   GITHUB_TOKEN=<token> bash scripts/configurar-branch-protection.sh
#
# Alternativa sin token: Settings -> Branches -> Add branch protection rule.
# ============================================================
set -euo pipefail

REPO="${REPO:-SebaEscobar4/MiniBiblioteca-DevSecOps}"
RAMA="${RAMA:-main}"
: "${GITHUB_TOKEN:?Define GITHUB_TOKEN con un token de administración del repo}"

curl -fsS -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${REPO}/branches/${RAMA}/protection" \
  --data @"$(dirname "$0")/../politicas/branch-protection.json" > /dev/null

echo "Protección aplicada a ${REPO}@${RAMA}. Verifica en Settings -> Branches."
