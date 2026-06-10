# 让 AI 助手安装这个 Skill

[English document](INSTALL_FOR_AI.md)

把下面这一句话复制给你的 AI 助手：

```text
请从 https://github.com/XinShuichen/auto-crash-skills 安装 Codex skill：克隆仓库，默认运行 ./install.sh 安装英文版；如果我要求中文，就运行 ./install.sh --lang zh-CN；如果我要求安装到当前 workspace，就在该 workspace 运行 ./install.sh --current-dir；确认 kernel-crash-debugger 已出现在选择的 skills 目录下；全局安装后提醒我重新打开一个 Codex session。
```

## 给 AI 助手的安装说明

你要安装的是 Codex skill，不是其他 AI 产品的运行依赖。不要安装第三方 agent
wrapper。

1. 克隆或更新仓库。

```bash
git clone https://github.com/XinShuichen/auto-crash-skills.git
cd auto-crash-skills
```

如果目录已经存在，就更新它：

```bash
cd auto-crash-skills
git pull --ff-only
```

2. 执行安装脚本。

```bash
./install.sh
```

如果要安装中文 skill 文本：

```bash
./install.sh --lang zh-CN
```

3. 如果用户提供了自定义 Codex 目录，需要尊重这些路径。

```bash
CODEX_HOME=/path/to/codex/home ./install.sh
CODEX_SKILLS_DIR=/path/to/codex/skills ./install.sh
CRASH_SKILL_LANG=zh-CN ./install.sh
```

4. 如果用户要求安装到当前 workspace，在该 workspace 中运行 `--current-dir`。

```bash
/path/to/auto-crash-skills/install.sh --current-dir
test -f ./.codex/skills/kernel-crash-debugger/SKILL.md
test -f ./.agent/skills/kernel-crash-debugger/SKILL.md
```

5. 验证全局 skill 已安装。

```bash
test -f "${CODEX_SKILLS_DIR:-${CODEX_HOME:-$HOME/.codex}/skills}/kernel-crash-debugger/SKILL.md"
```

6. 全局安装后，提醒用户重新打开一个 Codex session，让 skill metadata 重新加载。
