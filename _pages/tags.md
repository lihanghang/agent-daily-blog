---
layout: page
title: 标签
permalink: /tags/
icon: fas fa-tags
order: 5
---

<h1 class="dynamic-title pt-6 mb-4">
  <i class="fas fa-tags"></i> {{ page.title }}
</h1>

<div class="category-tags">
  {% for tag in site.tags %}
  <a href="{{ tag[0] | slugify | prepend: '/tags/' | relative_url }}" class="post-tag btn btn-outline-primary">
    {{ tag[0] }}<sup class="tag-count">{{ tag[1].size }}</sup>
  </a>
  {% endfor %}
</div>

<style>
  .category-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 20px;
  }

  .post-tag {
    margin: 0;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 14px;
  }

  .tag-count {
    font-size: 12px;
    color: #666;
    margin-left: 4px;
  }
</style>
