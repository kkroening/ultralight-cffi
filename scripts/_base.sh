#!/usr/bin/env bash
set -euo pipefail

base::abspath() {
  # Cross-platform(-ish) abspath for hideous systems that lack GNU readlink.
  arg1="$1" python -c "import os; print(os.path.realpath(os.environ['arg1']))"
}

BASE__ROOT_DIR="$(base::abspath "$(dirname "${BASH_SOURCE}")/..")"

_BASE__COLOR_LIGHT_GREEN='\033[1;32m'
_BASE__COLOR_OFF='\033[0m'

base::show_banner() {
  printf "\n===> ${_BASE__COLOR_LIGHT_GREEN}${@}${_BASE__COLOR_OFF}\n" >&2
}

base::_log() {
  if (($# < 1)); then
    base::abort "Usage: ${FUNCNAME[1]} <fmt> [printf args...]"
  fi
  local args fmt
  args=("${@:2}")
  fmt="$1"
  printf \
    "${prefix}${fmt}\n" \
    "${args[@]:-}" \
    >&2
}

base::log_info() {
  prefix='' base::_log "$@"
}

base::log_warning() {
  prefix='[WARNING] ' base::_log "$@"
}

base::log_error() {
  prefix='[ERROR] ' base::_log "$@"
}

base::abort() {
  base::log_error "${@:-Aborting.}"
  exit 1
}

base::ensure_which() {
  if ! which "$1" > /dev/null; then
    base::abort "$1 not found; aborting."
  fi
}
