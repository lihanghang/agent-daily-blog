---
layout: page
title: "Augment"
permalink: /tags/augment/
---

<h1 class="dynamic-title pt-6 mb-4">
  <i class="fas fa-tag"></i> Augment
</h1>

<div class="post-list mt-4">
  {% for post in site.posts %}
    {% if post.tags contains "Augment" %}
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
