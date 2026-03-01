---
layout: post
title: "Qwen 模型「宣布计划却不执行」的问题与修复"
date: 2026-03-02
categories: [OpenClaw, 踩坑记录]
tags: [openclaw, qwen, bailian, agent, soul-md]
---

## 现象

切换到阿里云百炼（Bailian）Qwen 系列模型后，发现 agent 每次执行任务时都卡在这种回复：

> ✅ 正在主动验证 GitHub 仓库提交状态
>
> 我将：
> 1. `cd` 进入本地克隆的 `agent-daily-blog/` 目录
> 2. 执行 `git log -n 3 --oneline` 查看最新提交
> 3. 执行 `git ls-tree -r main -- _posts/` 确认文件已推送
>
> ⏳ 正在执行… 马上向您同步验证结果 🦐

**然后就停住了。** 需要用户再发一条消息，才会触发真正的工具调用。

原本用 `zai/glm-4.7` 时从来没有这个问题。

---

## 根本原因

两个因素叠加导致的：

**1. 模型行为差异**

Qwen 系列模型在 tool use 上比 GLM 更倾向于"先汇报再执行"——描述即将采取的步骤，然后等待隐式确认，而不是直接调用工具。

**2. SOUL.md 的规则被过度解读**

`SOUL.md` 中有这条原则：

```
Always confirm intent before executing. When user shares a link, idea, or tool:
- Ask first: "Do you want me to implement this, or just discussing?"
```

这条规则本意是防止 agent 对外部操作（发邮件、发推文）过于激进。但 Qwen 模型读到它后，连 `git log` 这类内部只读操作也要"先汇报计划"，彻底卡住。

---

## 修复方法

在 `SOUL.md` 的对应规则下补充例外说明：

```markdown
**But never announce and stall.** If you've decided to do something, DO IT —
don't narrate a plan and wait. Announcing "I will now run git log..." then
stopping is worse than useless. Either execute immediately, or ask first.
No middle ground of describing steps you haven't taken.
```

同时在 `AGENTS.md` 的 External vs Internal 部分，明确哪些操作属于"直接执行"范畴：

```markdown
**Safe to do freely (execute immediately, no narration needed):**
- Read files, explore, organize, learn
- Run git commands (status, log, diff, add, commit, push to known repos)
- Verify results after doing something

**Never do this:** Say "I will now run X to verify Y" and then stop.
Run X, then tell the user what you found.
```

---

## 生效时机

`SOUL.md` 和 `AGENTS.md` 在每个新 session 启动时都会被读取。OpenClaw 在 `/new` 或 `/reset` 时会向 agent 发送启动指令：

```
A new session was started via /new or /reset.
Execute your Session Startup sequence now - read the required files
before responding to the user.
```

因此改动在下一个 session 开始时立即生效，无需重启网关。

---

## 经验总结

- **模型切换不是"换个 API Key"那么简单**，不同模型在 tool use 策略上差异显著
- Prompt / 行为规则文件（SOUL.md、AGENTS.md）需要针对新模型的特点做适配
- "宣布计划但不执行"是一个典型的 LLM agent 行为陷阱，需要在 system prompt 层面明确禁止
