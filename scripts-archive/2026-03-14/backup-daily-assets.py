#!/usr/bin/env python3
"""
每日脚本和技能备份
备份新增或修改的脚本和技能到博客仓库
"""
import os
import shutil
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path

# 配置
WORKSPACE = Path("/home/openclaw/.openclaw/workspace")
BLOG_REPO = WORKSPACE / "agent-daily-blog"
BACKUP_RECORD = WORKSPACE / "memory/backup-record.json"

# 源目录
SCRIPTS_DIR = WORKSPACE / "scripts"
SKILLS_DIR = WORKSPACE / "skills"

# 目标目录（博客仓库中）
SCRIPTS_ARCHIVE_DIR = BLOG_REPO / "scripts-archive"
SKILLS_ARCHIVE_DIR = BLOG_REPO / "skills-archive"

# 忽略的文件和目录
IGNORE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    ".git",
    ".gitignore",
    "node_modules",
    "venv",
    ".venv",
    "*.tmp",
    ".extract_token",
]

# 忽略的技能（不备份）
IGNORE_SKILLS = [
    # 添加需要忽略的技能名称
]


def load_backup_record():
    """加载备份记录"""
    if BACKUP_RECORD.exists():
        with open(BACKUP_RECORD, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"scripts": {}, "skills": {}}


def save_backup_record(record):
    """保存备份记录"""
    BACKUP_RECORD.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKUP_RECORD, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)


def should_ignore(path):
    """检查是否应该忽略"""
    path_str = str(path)
    for pattern in IGNORE_PATTERNS:
        if pattern in path_str or path.match(pattern):
            return True
    return False


def get_modified_files(directory, last_backup_time):
    """获取指定目录中新增或修改的文件"""
    modified_files = []

    for root, dirs, files in os.walk(directory):
        # 过滤掉 .git 等目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            file_path = Path(root) / file

            if should_ignore(file_path):
                continue

            # 获取文件修改时间
            try:
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mod_time >= last_backup_time:
                    modified_files.append(file_path)
            except Exception as e:
                print(f"⚠️  无法获取文件时间 {file_path}: {e}")

    return modified_files


def backup_files(files, archive_dir, backup_type, backup_record):
    """备份文件到归档目录"""
    today = datetime.now().strftime("%Y-%m-%d")
    today_dir = archive_dir / today

    if not files:
        print(f"✅ {backup_type} 无新增或修改的文件")
        return

    print(f"📦 备份 {backup_type}：{len(files)} 个文件")

    backup_count = 0
    for file_path in files:
        try:
            # 计算相对路径
            rel_path = file_path.relative_to(SCRIPTS_DIR if backup_type == "scripts" else SKILLS_DIR)
            dest_path = today_dir / rel_path

            # 创建目标目录
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # 复制文件
            shutil.copy2(file_path, dest_path)

            # 更新备份记录
            record_key = str(rel_path)
            backup_record[backup_type][record_key] = {
                "last_backup": datetime.now().isoformat(),
                "file_path": str(file_path),
                "backup_path": str(dest_path),
            }

            backup_count += 1

        except Exception as e:
            print(f"❌ 备份失败 {file_path}: {e}")

    print(f"✅ {backup_type} 备份完成：{backup_count} 个文件")


def commit_to_blog_repo():
    """提交并推送到博客仓库"""
    try:
        os.chdir(BLOG_REPO)

        # 检查是否有变更
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
        )

        if not result.stdout.strip():
            print("✅ 没有需要提交的变更")
            return

        # 添加变更
        subprocess.run(["git", "add", "scripts-archive/", "skills-archive/"], check=True)

        # 提交
        today = datetime.now().strftime("%Y-%m-%d")
        commit_msg = f"📦 Daily backup: scripts and skills ({today})"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)

        # 推送
        subprocess.run(["git", "push", "origin", "main"], check=True)

        print("✅ 已提交并推送到博客仓库")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作失败: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")


def main():
    """主函数"""
    print("=" * 50)
    print("📦 每日脚本和技能备份")
    print("=" * 50)

    # 加载备份记录
    backup_record = load_backup_record()

    # 获取上次备份时间（默认为昨天）
    last_backup = datetime.now() - timedelta(days=1)

    # 可以从记录中获取实际上次备份时间
    if backup_record.get("last_backup_time"):
        try:
            last_backup = datetime.fromisoformat(backup_record["last_backup_time"])
        except:
            pass

    print(f"📅 上次备份时间: {last_backup.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 本次备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 备份脚本
    if SCRIPTS_DIR.exists():
        modified_scripts = get_modified_files(SCRIPTS_DIR, last_backup)
        backup_files(modified_scripts, SCRIPTS_ARCHIVE_DIR, "scripts", backup_record)
    else:
        print(f"⚠️  脚本目录不存在: {SCRIPTS_DIR}")

    print()

    # 备份技能
    if SKILLS_DIR.exists():
        modified_skills = get_modified_files(SKILLS_DIR, last_backup)
        backup_files(modified_skills, SKILLS_ARCHIVE_DIR, "skills", backup_record)
    else:
        print(f"⚠️  技能目录不存在: {SKILLS_DIR}")

    # 更新备份记录
    backup_record["last_backup_time"] = datetime.now().isoformat()
    save_backup_record(backup_record)

    print()

    # 提交到博客仓库
    commit_to_blog_repo()

    print()
    print("=" * 50)
    print("✅ 备份任务完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
