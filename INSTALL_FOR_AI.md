# Install This Skill With an AI Assistant

[Chinese document](INSTALL_FOR_AI.zh-CN.md)

Copy this one-sentence prompt to your AI assistant:

```text
Install the Codex skill at https://github.com/XinShuichen/auto-crash-skills by cloning the repository, running ./install.sh for the default English skill unless I ask for Chinese, running ./install.sh --lang zh-CN when I ask for Chinese, using ./install.sh --current-dir when I ask to install into the current workspace, verifying that kernel-crash-debugger exists under the selected skills directory, and telling me to start a new Codex session when installing globally.
```

## Instructions For The AI Assistant

You are installing a Codex skill, not a runtime dependency for another AI
product. Do not install third-party agent wrappers.

1. Clone or update the repository.

```bash
git clone https://github.com/XinShuichen/auto-crash-skills.git
cd auto-crash-skills
```

If the directory already exists, update it instead:

```bash
cd auto-crash-skills
git pull --ff-only
```

2. Run the installer.

```bash
./install.sh
```

For Chinese skill text:

```bash
./install.sh --lang zh-CN
```

3. Respect a custom skills directory when the user provides one.

```bash
CODEX_SKILLS_DIR=/path/to/codex/skills ./install.sh
CRASH_SKILL_LANG=zh-CN ./install.sh
```

4. If the user asks to install into the current workspace, run the installer
   from that workspace with `--current-dir`.

```bash
/path/to/auto-crash-skills/install.sh --current-dir
test -f ./.agents/skills/kernel-crash-debugger/SKILL.md
```

5. Verify the installed skill.

```bash
test -f "${CODEX_SKILLS_DIR:-$HOME/.agents/skills}/kernel-crash-debugger/SKILL.md"
```

6. Tell the user to start a new Codex session so skill metadata is reloaded
   after global installation.
