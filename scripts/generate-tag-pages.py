#!/usr/bin/env python3
"""
生成 Jekyll 标签页面（直接放在根目录的 tags/ 文件夹）
"""

import os
import re
import glob

# 定义输出目录 - 直接放在根目录下的 tags 文件夹
TAGS_DIR = "tags"

# 确保目录存在
os.makedirs(TAGS_DIR, exist_ok=True)

# 获取所有文章中的标签
tags = set()

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
                    tags.add(tag)

# 为每个标签创建页面
for tag in tags:
    if tag:
        # 生成文件名（处理特殊字符）
        slug = tag.lower().replace(' ', '-')
        filename = f"{slug}.md"
        filepath = os.path.join(TAGS_DIR, filename)

        # 创建页面内容
        content = f"""---
layout: page
title: "{tag}"
tag: "{tag}"
permalink: /tags/{slug}/
---

<h1 class="dynamic-title pt-6 mb-4">
  <i class="fas fa-tag"></i> {tag}
</h1>

<div class="post-list mt-4">
"""

        # 添加 Liquid 模板（不通过 f-string）
        content += """  {% for post in site.posts %}
    {% if post.tags contains page.tag %}
      <article class="card post-preview mb-4">
        <div class="card-body">
          <time datetime="{{ post.date | date_to_xmlschema }}" class="text-muted small">
            {{ post.date | date: "%Y-%m-%d" }}
          </time>
          <h2 class="h5 mt-2">
            <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
          </h2>
          <p class="text-muted small mt-2">{{ post.excerpt | strip_html | truncate: 150 }}</p>
        </div>
      </article>
    {% endif %}
  {% endfor %}
</div>

{% assign tagged_posts = site.posts | where_exp: "post", "post.tags contains page.tag" %}
{% if tagged_posts.size == 0 %}
<div class="lead mt-5">
  <p>还没有该标签的文章。</p>
</div>
{% endif %}
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

print(f"Generated {len(tags)} tag pages in {TAGS_DIR}/:")
for tag in sorted(tags):
    slug = tag.lower().replace(' ', '-')
    print(f"  - {slug}.md -> /tags/{slug}/")
