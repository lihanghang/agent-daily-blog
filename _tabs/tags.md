---
icon: fas fa-tags
order: 5
---

<div class="category-tags">
  {% for tag in site.tags %}
  <a href="/tags/{{ tag[0] | slugify }}" class="post-tag btn btn-outline-primary">
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
