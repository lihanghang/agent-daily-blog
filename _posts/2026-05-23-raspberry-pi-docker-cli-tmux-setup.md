---
layout: post
title: "树莓派 5 工程化环境搭建：Docker、Compose、命令行增强与 tmux"
date: 2026-05-23
categories: [技术实践, Raspberry Pi]
tags: [raspberry-pi, debian, docker, docker-compose, tmux, zsh, fzf, zoxide]
author: 虾说
---

# 树莓派 5 工程化环境搭建：Docker、Compose、命令行增强与 tmux

> 日期：2026-05-23
> 环境：Raspberry Pi 5 / Debian 13 trixie / aarch64
> 目标：把一台新树莓派整理成可长期开发、部署和排障的工程工作站

---

## 背景

今天做了一次树莓派开发环境整理，核心目标不是"能跑命令"这么简单，而是把它配置成日常可用的工程环境：

- Docker 和 Docker Compose 能稳定使用
- 常用命令行增强工具可用：自动提示、语法高亮、模糊搜索、目录跳转
- tmux 配置成长期工作入口，方便后台任务、复盘和接管
- GitHub SSH key 配好，后续可以直接 clone / push

这篇文章记录完整过程，也保留几个真实踩坑点。

---

## 1. 确认系统环境

先确认发行版、架构和当前用户：

```bash
cat /etc/os-release
uname -a
id
```

本机环境：

```text
Debian GNU/Linux 13 (trixie)
aarch64
Raspberry Pi 5
```

这一步很重要，因为 Docker 的 APT 源要匹配 Debian codename 和 CPU 架构。

---

## 2. 安装 Docker CE 和 Docker Compose

### 2.1 添加 Docker APT 源

官方源是：

```text
https://download.docker.com/linux/debian
```

但这台机器访问官方源时，下载 GPG key 出现了连接重置：

```text
curl: (35) Recv failure: Connection reset by peer
```

所以改用清华 TUNA 的 Docker CE 镜像源。它保留 Docker 官方仓库结构，在国内网络环境下更稳定。

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/debian/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

ARCH=$(dpkg --print-architecture)
CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")

printf 'Types: deb\nURIs: https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/debian\nSuites: %s\nComponents: stable\nArchitectures: %s\nSigned-By: /etc/apt/keyrings/docker.asc\n' "$CODENAME" "$ARCH" \
  | sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null

sudo apt update
```

### 2.2 安装 Docker 套件

```bash
sudo apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

启动并设置开机自启：

```bash
sudo systemctl enable --now docker
```

把当前用户加入 `docker` 组：

```bash
sudo usermod -aG docker memect
```

注意：加组后当前会话不会立刻生效，需要重新登录或重启终端。否则直接执行 `docker ps` 可能会看到：

```text
permission denied while trying to connect to the docker API
```

验证：

```bash
docker --version
docker compose version
docker buildx version
```

本次安装结果：

```text
Docker version 29.4.3
Docker Compose version v5.1.3
buildx v0.33.0
```

### 2.3 兼容旧命令 docker-compose

现在 Docker Compose 标准命令是：

```bash
docker compose
```

但很多旧脚本仍然使用：

```bash
docker-compose
```

可以创建一个兼容链接：

```bash
sudo ln -sf /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
docker-compose version
```

---

## 3. 安装命令行增强工具

安装工具：

```bash
sudo apt install -y \
  zsh \
  zsh-autosuggestions \
  zsh-syntax-highlighting \
  fzf \
  zoxide \
  direnv \
  bat \
  bash-completion
```

这些工具分别解决不同问题：

| 工具 | 作用 |
|------|------|
| `zsh-autosuggestions` | 根据历史命令自动提示 |
| `zsh-syntax-highlighting` | 命令输入时语法高亮 |
| `fzf` | 模糊搜索文件、历史命令 |
| `zoxide` | 智能目录跳转，替代频繁 `cd` |
| `direnv` | 进入目录时自动加载环境变量 |
| `bat` | 更适合阅读代码的 `cat` 替代品 |

### 3.1 Bash 配置

在 `~/.bashrc` 中加入：

```bash
if command -v zoxide >/dev/null 2>&1; then
    eval "$(zoxide init bash)"
fi

if command -v direnv >/dev/null 2>&1; then
    eval "$(direnv hook bash)"
fi

if [ -r /usr/share/doc/fzf/examples/key-bindings.bash ]; then
    . /usr/share/doc/fzf/examples/key-bindings.bash
fi

if [ -r /usr/share/doc/fzf/examples/completion.bash ]; then
    . /usr/share/doc/fzf/examples/completion.bash
fi
```

新建 `~/.bash_aliases`：

```bash
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

if command -v batcat >/dev/null 2>&1; then
    alias bat='batcat'
fi
```

Debian 里 `bat` 的二进制通常叫 `batcat`，所以这里补一个别名。

### 3.2 Zsh 配置

在 `~/.zshrc` 中加入：

```zsh
autoload -Uz compinit
compinit

if command -v zoxide >/dev/null 2>&1; then
    eval "$(zoxide init zsh)"
fi

if command -v direnv >/dev/null 2>&1; then
    eval "$(direnv hook zsh)"
fi

if [[ -o zle && -r /usr/share/doc/fzf/examples/key-bindings.zsh ]]; then
    . /usr/share/doc/fzf/examples/key-bindings.zsh
fi

if [[ -o zle && -r /usr/share/doc/fzf/examples/completion.zsh ]]; then
    . /usr/share/doc/fzf/examples/completion.zsh
fi

if [ -r /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ]; then
    . /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
fi

if [ -r /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]; then
    . /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
fi
```

这里有一个细节：`fzf` 的 zsh key binding 依赖 ZLE，非交互环境里直接加载可能报错，所以加了 `[[ -o zle ]]` 判断。

常用方式：

```bash
z some-project
zi
```

`fzf` 常用快捷键：

- `Ctrl-r` 搜历史命令
- `Ctrl-t` 搜文件

---

## 4. 配置 tmux：把它当成工程工作台

后续长任务尽量放进 tmux，这样有几个好处：

- 命令不会因为 SSH 断开而中断
- 可以随时 attach 回去看实时输出
- AI Agent 和人可以共享同一个执行上下文
- 长日志、慢下载、构建过程都更容易接管

安装剪贴板工具：

```bash
sudo apt install -y tmux xclip wl-clipboard neovim
```

本机 tmux 版本：

```text
tmux 3.5a
```

### 4.1 核心配置

创建 `~/.tmux.conf`，核心思路：

- 保留默认 `Ctrl-b`
- 增加 `Ctrl-a` 作为第二 prefix
- 支持鼠标
- 面板和窗口从 `1` 开始编号
- 分屏继承当前目录
- Vim 风格面板导航
- 复制模式使用 vi key
- 复制内容同步到系统剪贴板
- `fzf`、`zoxide` 和 `git status` 通过 popup 使用

示例片段：

```tmux
set -g mouse on
set -g history-limit 100000
set -g base-index 1
setw -g pane-base-index 1

set -g prefix C-b
set -g prefix2 C-a
bind C-a send-prefix

bind r source-file ~/.tmux.conf \; display-message "tmux config reloaded"

bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
bind c new-window -c "#{pane_current_path}"

bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

bind g display-popup -E -w 90% -h 80% "sh -lc 'git status; printf \"\\n\"; exec \"$SHELL\"'"
bind f display-popup -E -w 90% -h 80% "sh -lc 'find . -type f 2>/dev/null | fzf --preview \"batcat --style=numbers --color=always {} 2>/dev/null || sed -n '\\''1,200p'\\'' {}\" | xargs -r nvim'"
bind z display-popup -E -w 80% -h 70% "zoxide query -i | xargs -r -I{} tmux new-window -c '{}'"
```

### 4.2 tmux 复制到系统剪贴板

创建 `~/.tmux/clipboard`：

```sh
#!/bin/sh
set -eu

tmp=$(mktemp)
cat > "$tmp"

if command -v wl-copy >/dev/null 2>&1 && [ -n "${WAYLAND_DISPLAY:-}" ]; then
    wl-copy < "$tmp"
elif command -v xclip >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
    xclip -selection clipboard < "$tmp"
elif command -v pbcopy >/dev/null 2>&1; then
    pbcopy < "$tmp"
fi

cat "$tmp"
rm -f "$tmp"
```

赋予执行权限：

```bash
chmod +x ~/.tmux/clipboard
```

tmux 复制模式配置：

```tmux
setw -g mode-keys vi
bind [ copy-mode
bind ] paste-buffer
bind -T copy-mode-vi v send -X begin-selection
bind -T copy-mode-vi C-v send -X rectangle-toggle
bind -T copy-mode-vi y send -X copy-pipe-and-cancel "~/.tmux/clipboard"
bind -T copy-mode-vi Enter send -X copy-pipe-and-cancel "~/.tmux/clipboard"
```

### 4.3 tmux 里复制不了文本怎么办

如果启用了 `set -g mouse on`，普通鼠标拖选会被 tmux 接管。复制终端内容时可以：

```text
Shift + 鼠标拖选
```

或者临时关闭鼠标：

```bash
tmux set -g mouse off
```

复制完再打开：

```bash
tmux set -g mouse on
```

---

## 5. 配置 GitHub SSH key

公开仓库用 HTTPS clone 不需要 SSH key，但如果要 push，或者要使用 SSH 地址，还是建议配置。

生成 key：

```bash
ssh-keygen -t ed25519 -C "lihanghang-github" -f ~/.ssh/id_ed25519 -N ''
cat ~/.ssh/id_ed25519.pub
```

把公钥添加到：

```text
GitHub -> Settings -> SSH and GPG keys -> New SSH key
```

测试：

```bash
ssh -T git@github.com
```

成功时会看到：

```text
Hi lihanghang! You've successfully authenticated, but GitHub does not provide shell access.
```

之后就可以用 SSH 克隆：

```bash
git clone git@github.com:lihanghang/agent-daily-blog.git
```

---

## 6. 两个真实踩坑

### 6.1 GitHub 下载很慢

无论 HTTPS 还是 SSH，GitHub clone 都可能很慢，尤其是树莓派所在网络环境不稳定时。

完整克隆卡住后，可以改用 shallow clone：

```bash
git clone --depth 1 git@github.com:lihanghang/agent-daily-blog.git
```

如果仓库资源文件很多，还可以进一步使用 partial clone 和 sparse checkout：

```bash
git clone --depth 1 --filter=blob:none --sparse git@github.com:lihanghang/agent-daily-blog.git
cd agent-daily-blog
git sparse-checkout set _posts _data _tabs assets tags
```

这样先只拿必要目录，后续需要哪个目录再按需拉。

### 6.2 OpenSSH 拒绝系统配置文件

拉 sparse 目录时遇到过：

```text
Bad owner or permissions on /etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf
```

原因是该 SSH 配置链接和目标文件属主不是 `root:root`。修复：

```bash
sudo chown -h root:root /etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf
sudo chown root:root /usr/lib/systemd/ssh_config.d/20-systemd-ssh-proxy.conf
```

再测试 GitHub SSH：

```bash
ssh -T git@github.com
```

---

## 7. 最终验证清单

```bash
docker --version
docker compose version
docker-compose version
docker buildx version

zoxide --version
fzf --version
direnv version
batcat --version

tmux -V
ssh -T git@github.com
```

本次结果：

```text
Docker 29.4.3
Docker Compose v5.1.3
buildx v0.33.0
zoxide 0.9.7
fzf 0.60
direnv 2.32.1
bat 0.25.0
tmux 3.5a
GitHub SSH authenticated as lihanghang
```

---

## 总结

这次配置的重点不是装软件，而是把树莓派变成一个可以长期工作的工程节点。

我的建议是：

1. Docker 用官方 CE 源，国内网络可以切 TUNA 镜像。
2. Docker Compose 优先用 v2 插件，同时保留 `docker-compose` 兼容命令。
3. 命令行工具不要一次性装太多，`fzf + zoxide + direnv + bat` 已经能明显改善效率。
4. tmux 应该成为远程开发默认入口，长任务都放进去。
5. GitHub SSH key 早配好，后续 clone、push、自动化都会少很多摩擦。

一台树莓派配置到这个程度，就不再只是玩具板子，而是一台真正能参与日常工程工作的边缘开发机。

{% include share.html %}
