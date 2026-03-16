#!/bin/bash
# code-forge session hook
# Usage: session.sh start | session.sh end

set -euo pipefail

ACTION="${1:-}"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

AGENTS_DIR="$PLUGIN_ROOT/agents"
RULES_DIR="$PLUGIN_ROOT/rules"
DEFAULT_AGENTS_DIR="$PLUGIN_ROOT/agents-default"
VAS_AGENTS_DIR="$PLUGIN_ROOT/plugins/vas/agents/_agents"
VAS_RULES_DIR="$PLUGIN_ROOT/plugins/vas/rules"

# --- config helpers ---

# Read vas.enabled from a local.md file (YAML frontmatter)
# Returns: "true", "false", or "" (not set)
read_vas_config() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  sed -n '/^---$/,/^---$/p' "$file" 2>/dev/null \
    | grep -E '^\s*enabled:' \
    | head -1 \
    | sed 's/.*enabled:\s*//' \
    | tr -d '[:space:]'
}

# Resolve VAS enabled status
# Priority: project > global > unset
resolve_vas_enabled() {
  local project_config=".claude/code-forge.local.md"
  local global_config="$HOME/.claude/code-forge.local.md"

  local val
  val=$(read_vas_config "$project_config")
  if [[ -n "$val" ]]; then
    echo "$val"
    return
  fi

  val=$(read_vas_config "$global_config")
  if [[ -n "$val" ]]; then
    echo "$val"
    return
  fi

  echo ""
}

# --- agent switching ---

switch_agents() {
  local source_dir="$1"

  # Clear current symlinks in agents/
  rm -f "$AGENTS_DIR"/*.md 2>/dev/null || true

  # Create new symlinks
  for f in "$source_dir"/*.md; do
    [[ -f "$f" ]] || continue
    ln -sf "$f" "$AGENTS_DIR/$(basename "$f")"
  done
}

# --- VAS rules switching ---

vas_rules_on() {
  # Symlink VAS rules into plugin rules/
  for f in "$VAS_RULES_DIR"/*.md; do
    [[ -f "$f" ]] || continue
    ln -sf "$f" "$RULES_DIR/$(basename "$f")"
  done
}

vas_rules_off() {
  # Remove VAS rule symlinks from plugin rules/
  for link in "$RULES_DIR"/*.md; do
    [[ -L "$link" ]] || continue
    local target
    target=$(readlink "$link" 2>/dev/null || true)
    if [[ "$target" == *"plugins/vas/rules/"* ]]; then
      rm -f "$link"
    fi
  done
}

# --- actions ---

on_start() {
  local vas_enabled
  vas_enabled=$(resolve_vas_enabled)

  case "$vas_enabled" in
    true)
      switch_agents "$VAS_AGENTS_DIR"
      vas_rules_on
      echo "VAS_STATUS=enabled"
      ;;
    false)
      switch_agents "$DEFAULT_AGENTS_DIR"
      vas_rules_off
      echo "VAS_STATUS=disabled"
      ;;
    *)
      # Default agents until user decides
      switch_agents "$DEFAULT_AGENTS_DIR"
      vas_rules_off
      echo "VAS_STATUS=ask"
      ;;
  esac
}

on_end() {
  :
}

case "$ACTION" in
  start) on_start ;;
  end)   on_end ;;
  *)     echo "Usage: session.sh start|end" >&2; exit 1 ;;
esac
