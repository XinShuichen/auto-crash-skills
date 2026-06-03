#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
base_skill_src="${repo_dir}/skills/kernel-crash-debugger"
zh_skill_src="${repo_dir}/skills/kernel-crash-debugger-zh-CN"

codex_home="${CODEX_HOME:-${HOME}/.codex}"
skills_dir="${CODEX_SKILLS_DIR:-${codex_home}/skills}"
target="${skills_dir}/kernel-crash-debugger"
lang="${CRASH_SKILL_LANG:-en}"

usage() {
  cat <<'EOF'
Usage: ./install.sh [--lang en|zh-CN]

Installs kernel-crash-debugger into the active Codex skills directory.
Default language: en

Environment:
  CODEX_HOME=/path/to/codex/home
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

if [[ ! -f "${base_skill_src}/SKILL.md" ]]; then
  echo "Missing skill source: ${base_skill_src}/SKILL.md" >&2
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
echo "Restart Codex or start a new session so the skill metadata is reloaded."
