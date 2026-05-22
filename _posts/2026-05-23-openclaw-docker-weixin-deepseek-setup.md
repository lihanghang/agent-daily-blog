---
layout: post
title: "树莓派上安装 OpenClaw：Docker 部署、DeepSeek 官方模型、微信接入"
date: 2026-05-23
categories: [技术实践, OpenClaw]
tags: [openclaw, docker, deepseek, wechat, raspberry-pi, ghcr]
author: 虾说
---

# 树莓派上安装 OpenClaw：Docker 部署、DeepSeek 官方模型、微信接入

> 日期：2026-05-23
> 环境：Raspberry Pi 5 / Debian 13 / Docker CE
> 目标：在树莓派上把 OpenClaw 跑起来，并接上 DeepSeek 官方模型和微信

---

## 背景

今天把 OpenClaw 在树莓派上完整落地了一遍，目标不是只把容器跑起来，而是把它变成一个真正能收微信、走官方模型、能长期维护的本地 AI 网关。

最终完成的状态是：

- OpenClaw 通过 Docker 运行
- 默认模型切到 DeepSeek 官方 `deepseek-v4-flash`
- 微信通道 `openclaw-weixin` 登录成功
- 飞书 webhook 也接上了，安装完成会通知我

这篇文章记录的是完整实操过程，包括几个真实的坑。

---

## 1. 先决条件

在开始前，这台树莓派已经完成了这些基础准备：

- Docker CE
- Docker Compose v2
- tmux
- GitHub SSH key

如果这些还没配，可以先参考前一篇树莓派工程化环境文章。

---

## 2. 官方 Docker 路线

OpenClaw 官方 Docker 文档的核心思路是：

1. 准备配置目录
2. 使用官方镜像
3. 启动 gateway
4. 通过控制台完成后续 onboarding

控制台默认地址：

```text
http://127.0.0.1:18789/
```

我最终采用的是一个最小化 Compose 方案，工作目录放在：

```text
/home/memect/work/openclaw/openclaw-docker
```

`docker-compose.yml`：

```yaml
services:
  openclaw:
    image: ${OPENCLAW_IMAGE}
    container_name: openclaw
    restart: unless-stopped
    ports:
      - "${OPENCLAW_PORT}:18789"
    environment:
      OPENCLAW_HOST: ${OPENCLAW_HOST}
      OPENCLAW_PORT: ${OPENCLAW_PORT}
      OPENCLAW_BASE_URL: ${OPENCLAW_BASE_URL}
      OPENCLAW_GATEWAY_TOKEN: ${OPENCLAW_GATEWAY_TOKEN}
      DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY}
    volumes:
      - ${OPENCLAW_HOME}:/home/node/.openclaw
    command: ["node", "openclaw.mjs", "gateway", "--allow-unconfigured"]
```

`.env`：

```bash
OPENCLAW_IMAGE=ghcr.io/openclaw/openclaw:2026.5.20-slim-arm64
OPENCLAW_HOST=0.0.0.0
OPENCLAW_PORT=18789
OPENCLAW_BASE_URL=http://127.0.0.1:18789
OPENCLAW_HOME=/home/memect/openclaw
OPENCLAW_GATEWAY_TOKEN=随机生成的token
DEEPSEEK_API_KEY=sk-...
```

启动命令：

```bash
cd /home/memect/work/openclaw/openclaw-docker
docker compose up -d
```

---

## 3. 第一个坑：GHCR 直连非常慢

理论上直接拉官方镜像就行：

```bash
docker pull ghcr.io/openclaw/openclaw:latest
```

但在树莓派这台机器上，`ghcr.io` 直连非常慢，表现是：

- `docker pull` 长时间没有完成
- 有时已经下载了一部分层，但长时间不落盘
- `latest` 镜像体积更大，等待成本更高

我做了两层优化：

### 3.1 不用 `latest`，改用 ARM64 slim 标签

直接切到：

```text
ghcr.io/openclaw/openclaw:2026.5.20-slim-arm64
```

这比 `latest` 更适合树莓派。

### 3.2 使用国内 GHCR 镜像

最终成功拉下来的路径不是 `ghcr.io`，而是：

```bash
docker pull ghcr.nju.edu.cn/openclaw/openclaw:2026.5.20-slim-arm64
```

拉下来后，再打回官方 tag：

```bash
docker tag \
  ghcr.nju.edu.cn/openclaw/openclaw:2026.5.20-slim-arm64 \
  ghcr.io/openclaw/openclaw:2026.5.20-slim-arm64
```

这样 Compose 文件仍然可以继续使用官方镜像名。

实际落地镜像：

```text
ghcr.io/openclaw/openclaw:2026.5.20-slim-arm64
```

---

## 4. 容器启动与验证

启动后先检查容器状态：

```bash
docker compose ps
```

成功时状态类似：

```text
Up (healthy)
```

再从主机内验证 HTTP：

```bash
curl -I http://127.0.0.1:18789/
```

我这里返回：

```text
HTTP/1.1 200 OK
```

说明控制台已经正常对外提供。

日志里的关键成功信息：

```text
[gateway] ready
[gateway] http server listening
```

---

## 5. 配置 DeepSeek 官方模型

这一步一开始也踩了个坑。

### 5.1 错误姿势：把模型写成 `openai/deepseek-v4-flash`

OpenClaw 里很多模型最终都走 OpenAI 兼容接口，但这不代表 provider 就应该写成 `openai`。

如果把默认模型误设成：

```text
openai/deepseek-v4-flash
```

它会被系统当成 OpenAI 家族模型，而不是 DeepSeek 官方 provider。

### 5.2 正确姿势：使用内置 `deepseek` provider

OpenClaw 自带 `deepseek` provider，插件清单里明确有：

- `deepseek-v4-flash`
- `deepseek-v4-pro`
- `deepseek-chat`
- `deepseek-reasoner`

所以最终我把默认模型改成：

```text
deepseek/deepseek-v4-flash
```

并把 API key 直接注入容器环境：

```bash
DEEPSEEK_API_KEY=sk-...
```

这样最稳，不需要额外折腾 provider auth profile。

配置文件中的核心段落：

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "deepseek/deepseek-v4-flash"
      },
      "models": {
        "deepseek/deepseek-v4-flash": {}
      }
    }
  }
}
```

### 5.3 验证模型状态

```bash
docker exec openclaw sh -lc "openclaw models status"
```

关键输出是：

```text
Default: deepseek/deepseek-v4-flash
deepseek effective=env:sk-...
```

同时 `openclaw status` 里也能看到：

```text
default deepseek-v4-flash
```

---

## 6. 安装微信插件

OpenClaw 的微信接入不是内置通道，而是外部插件：

```text
@tencent-weixin/openclaw-weixin
```

在容器里安装：

```bash
docker exec openclaw sh -lc \
  "npm config set registry https://registry.npmmirror.com && \
   openclaw plugins install '@tencent-weixin/openclaw-weixin'"
```

安装完成后会提示：

```text
Installed plugin: openclaw-weixin
Restart the gateway to load plugins.
```

重启容器：

```bash
docker compose restart
```

然后检查插件：

```bash
docker exec openclaw sh -lc "openclaw plugins list | grep -i weixin -A3 -B1"
```

看到 `enabled` 就说明插件已被加载。

---

## 7. 微信扫码登录

这一步是整个流程里最适合放 tmux 的部分。

原因很简单：二维码登录是交互式 TTY，会话断了就麻烦。

我把登录过程放进 tmux：

```bash
tmux -L weixin new-session -d -s login \
  'docker exec -it openclaw sh -lc "openclaw channels login --channel openclaw-weixin --verbose"'
```

然后 attach 进去：

```bash
tmux -L weixin attach -t login
```

终端里会出现二维码和一个备用的微信链接，扫码后插件会自动把微信账号写入配置。

日志里最关键的一段是：

```text
Weixin configured, enabled automatically.
[openclaw-weixin] starting weixin provider
[openclaw-weixin] weixin monitor started
```

### 7.1 验证微信通道状态

```bash
docker exec openclaw sh -lc "openclaw channels list"
docker exec openclaw sh -lc "openclaw channels status --deep"
```

最终我这里的结果：

```text
openclaw-weixin 81e9a3ef0c9a-im-bot: enabled, configured, running
```

这说明微信已经真正上线，不只是“插件装好了”。

---

## 8. 飞书通知

除了微信，我还顺手把飞书机器人 webhook 接进去了，安装完成和微信接通后都会主动通知。

发送方式就是普通 webhook：

```bash
curl -X POST https://open.feishu.cn/open-apis/bot/v2/hook/...
```

这样有两个好处：

- OpenClaw/系统配置完成后不用盯着终端
- 后续也可以把巡检、重启、更新结果发到飞书

---

## 9. 最终状态

最终这台树莓派上的 OpenClaw 状态是：

- OpenClaw Docker 运行正常
- 控制台：`http://127.0.0.1:18789/`
- 容器健康状态：`healthy`
- 默认模型：`deepseek/deepseek-v4-flash`
- 凭据来源：`DEEPSEEK_API_KEY`
- 微信通道：`openclaw-weixin`
- 微信状态：`enabled, configured, running`
- 飞书 webhook：可正常通知

---

## 10. 最值得记住的几个点

1. 树莓派上不要盲拉 `ghcr.io/openclaw/openclaw:latest`，优先用 `slim-arm64`。
2. 国内网络下，`ghcr.nju.edu.cn` 这种 GHCR 镜像源比直连更现实。
3. DeepSeek 官方模型要用 `deepseek/deepseek-v4-flash`，不要误设成 `openai/...`。
4. 微信登录一定放进 tmux，会省很多事。
5. 插件“已安装”不等于“已接通”，一定要看 `channels status --deep`。

这套配完之后，树莓派上的 OpenClaw 已经不是一个“能启动的容器”，而是一个真正可收消息、可走官方模型、可长期运行的本地网关。

{% include share.html %}
