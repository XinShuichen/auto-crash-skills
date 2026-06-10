#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
base_skill_src="${repo_dir}/skills/kernel-crash-debugger"
zh_skill_src="${repo_dir}/skills/kernel-crash-debugger-zh-CN"

skills_dir="${CODEX_SKILLS_DIR:-${HOME}/.agents/skills}"
target="${skills_dir}/kernel-crash-debugger"
lang="${CRASH_SKILL_LANG:-en}"
install_scope="codex"

usage() {
  cat <<'EOF'
Usage: ./install.sh [--lang en|zh-CN] [--current-dir]

Installs kernel-crash-debugger into the active Codex skills directory.
Default language: en

Options:
  --lang en|zh-CN      Install English or Chinese skill text.
  --current-dir        Install to ./.agents/skills/kernel-crash-debugger under
                       the caller's current working directory.

Environment:
  CODEX_SKILLS_DIR=/path/to/codex/skills
  CRASH_SKILL_LANG=en|zh-CN
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --lang)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --lang" >&2
        exit 1
      fi
      lang="$2"
      shift 2
      ;;
    --lang=*)
      lang="${1#--lang=}"
      shift
      ;;
    --en)
      lang="en"
      shift
      ;;
    --zh | --zh-CN | --cn)
      lang="zh-CN"
      shift
      ;;
    --current-dir | --cwd | --local)
      install_scope="current-dir"
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "${lang}" in
  en | en-US)
    lang="en"
    ;;
  zh | zh-CN | zh_CN | cn)
    lang="zh-CN"
    ;;
  *)
    echo "Unsupported language: ${lang}" >&2
    echo "Supported languages: en, zh-CN" >&2
    exit 1
    ;;
esac

if [[ "${install_scope}" == "current-dir" ]]; then
  targets=(
    "${PWD}/.agents/skills/kernel-crash-debugger"
  )
else
  targets=("${target}")
fi

if [[ ! -f "${base_skill_src}/SKILL.md" ]]; then
  echo "Missing skill source: ${base_skill_src}/SKILL.md" >&2
  exit 1
fi

source_real="$(cd "${base_skill_src}" && pwd -P)"

install_one() {
  local target="$1"
  local target_parent target_parent_real target_real skills_dir

  target_parent="$(dirname "${target}")"
  skills_dir="${target_parent}"
  mkdir -p "${target_parent}"
  target_parent_real="$(cd "${target_parent}" && pwd -P)"
  target_real="${target_parent_real}/$(basename "${target}")"

  if [[ "${target_real}" == "${source_real}" ]]; then
    echo "Refusing to install over the source skill directory: ${target_real}" >&2
    echo "Run --current-dir from the workspace that should receive .agents skills." >&2
    exit 1
  fi

  mkdir -p "${skills_dir}"
  rm -rf "${target}"
  cp -a "${base_skill_src}" "${target}"

  if [[ "${lang}" == "zh-CN" ]]; then
    if [[ ! -f "${zh_skill_src}/SKILL.md" ]]; then
      echo "Missing Chinese skill source: ${zh_skill_src}/SKILL.md" >&2
      exit 1
    fi
    cp -a "${zh_skill_src}/SKILL.md" "${target}/SKILL.md"
    cp -a "${zh_skill_src}/agents/." "${target}/agents/"
    cp -a "${zh_skill_src}/references/." "${target}/references/"
  fi

  echo "Installed kernel-crash-debugger skill (${lang}) to: ${target}"
}

for target in "${targets[@]}"; do
  install_one "${target}"
done

if [[ "${install_scope}" == "codex" ]]; then
  echo "Restart Codex or start a new session so the skill metadata is reloaded."
fi
