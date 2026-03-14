#!/usr/bin/env python3
"""
生成 Jekyll 标签页面（最终版本）

策略：
1. 文件名和 permalink 都使用小写（与 Chirpy 主题的标签链接一致）
2. 在 Liquid 模板中使用 or 条件匹配所有可能的大小写变体
3. 确保左侧的标签链接（如 /tags/augment/）能正常访问
"""

import os
import re
import glob
from collections import Counter

# 定义输出目录
TAGS_DIR = "tags"

# 确保目录存在
os.makedirs(TAGS_DIR, exist_ok=True)

# 获取所有文章中的标签（统计每个变体的出现次数）
tags_counter = {}

for post_file in glob.glob("_posts/*.md"):
    with open(post_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # 提取 tags 字段
        tags_match = re.search(r'^tags:\s*\[(.*?)\]', content, re.MULTILINE)
        if tags_match:
            tags_str = tags_match.group(1)
            # 解析标签列表
            for tag in tags_str.split(','):
                tag = tag.strip().strip('"').strip("'")
                if tag:
                    # 统计每个标签变体的出现次数
                    if tag not in tags_counter:
                        tags_counter[tag] = 0
                    tags_counter[tag] += 1

# 按 slug（小写）分组
tags_by_slug = {}
for tag, count in tags_counter.items():
    slug = tag.lower()
    if slug not in tags_by_slug:
        tags_by_slug[slug] = []
    tags_by_slug[slug].append((tag, count))

# 为每个标签创建页面
for slug, tag_list in tags_by_slug.items():
    # 选择出现次数最多的变体作为主标签（用于显示）
    tag_list.sort(key=lambda x: x[1], reverse=True)
    main_tag = tag_list[0][0]

    # 生成文件名 - 使用小写（与 permalink 一致）
    filename = f"{slug}.md"
    filepath = os.path.join(TAGS_DIR, filename)

    # 创建页面内容
    # permalink 使用小写
    content = f"""---
layout: page
title: "{main_tag}"
permalink: /tags/{slug}/
---

<h1 class="dynamic-title pt-6 mb-4">
  <i class="fas fa-tag"></i> {main_tag}
</h1>

<div class="post-list mt-4">
"""

    # 添加 Liquid 模板 - 为每个变体创建独立的匹配条件
    or_conditions = ' or '.join([f'post.tags contains "{t[0]}"' for t in tag_list])

    content += f"""  {{% for post in site.posts %}}
    {{% if {or_conditions} %}}
      <article class="card post-preview mb-4">
        <div class="card-body">
          <time datetime="{{{{ post.date | date_to_xmlschema }}}}" class="text-muted small">
            {{{{ post.date | date: "%Y-%m-%d" }}}}
          </time>
          <h2 class="h5 mt-2">
            <a href="{{{{ post.url | relative_url }}}}">{{{{ post.title }}}}</a>
          </h2>
          <p class="text-muted small mt-2">{{{{ post.excerpt | strip_html | truncate: 150 }}}}</p>
        </div>
      </article>
    {{% endif %}}
  {{% endfor %}}
</div>
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print(f"Generated {len(tags_by_slug)} tag pages in {TAGS_DIR}/:")
for slug in sorted(tags_by_slug.keys()):
    tag_list = tags_by_slug[slug]
    main_tag = tag_list[0][0]
    if len(tag_list) > 1:
        variants = ', '.join([t[0] for t in tag_list])
        print(f"  - {slug}.md -> /tags/{slug}/ (display: '{main_tag}', matches: {variants})")
    else:
        print(f"  - {slug}.md -> /tags/{slug}/ (tag: '{main_tag}')")
