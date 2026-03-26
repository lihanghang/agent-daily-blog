# YC Introduction Demo - 11 Style Showcase

> 使用 11 种不同视觉风格生成的 "什么是 Y Combinator" 主题 PPT 封面
>
> 所有图片使用 302.ai Seedream 4.0 模型生成 (1920x1080, 16:9)

---

## 风格展示

### 1. Retro Pop Art (复古波普)
**特点**: 70 年代杂志美学、厚黑边框、米色背景、几何装饰

| English | 中文 |
|---------|------|
| ![Retro Pop EN](images/01-retro-pop-en.png) | ![Retro Pop CN](images/01-retro-pop-cn.png) |

---

### 2. Minimalist Clean (极简主义)
**特点**: 白色背景、大量留白、细雅线条、企业美学

| English | 中文 |
|---------|------|
| ![Minimal EN](images/02-minimal-en.png) | ![Minimal CN](images/02-minimal-cn.png) |

---

### 3. Cyberpunk Neon (赛博朋克)
**特点**: 深色背景、霓虹发光、科技网格、未来主义

| English | 中文 |
|---------|------|
| ![Cyberpunk EN](images/03-cyberpunk-en.png) | ![Cyberpunk CN](images/03-cyberpunk-cn.png) |

---

### 4. Neo-Brutalism (新粗野主义)
**特点**: 奶油色背景、大胆原色、4px 粗黑边框、硬阴影

| English | 中文 |
|---------|------|
| ![Neo-Brutalism EN](images/04-neo-brutalism-en.png) | ![Neo-Brutalism CN](images/04-neo-brutalism-cn.png) |

---

### 5. Acid Graphics Y2K (酸性设计)
**特点**: 金属铬元素、全息点缀、液态形状、Y2K 美学

| English | 中文 |
|---------|------|
| ![Acid Graphics EN](images/05-acid-graphics-en.png) | ![Acid Graphics CN](images/05-acid-graphics-cn.png) |

---

### 6. Modern Minimal Pop (现代极简波普)
**特点**: 柔和粉彩背景、星爆图形、瑞士设计影响

| English | 中文 |
|---------|------|
| ![Modern Minimal Pop EN](images/06-modern-minimal-pop-en.png) | ![Modern Minimal Pop CN](images/06-modern-minimal-pop-cn.png) |

---

### 7. Swiss International (瑞士国际主义)
**特点**: 大胆几何色块、斜向排版、Helvetica 字体

| English | 中文 |
|---------|------|
| ![Swiss International EN](images/07-swiss-international-en.png) | ![Swiss International CN](images/07-swiss-international-cn.png) |

---

### 8. Dark Editorial (暗黑 Editorial)
**特点**: 黑色背景配白色点阵、衬线字体、报纸美学

| English | 中文 |
|---------|------|
| ![Dark Editorial EN](images/08-dark-editorial-en.png) | ![Dark Editorial CN](images/08-dark-editorial-cn.png) |

---

### 9. Design Blueprint (设计蓝图)
**特点**: Figma 文档风格、青色网格线、技术 UI 模型

| English | 中文 |
|---------|------|
| ![Design Blueprint EN](images/09-design-blueprint-en.png) | ![Design Blueprint CN](images/09-design-blueprint-cn.png) |

---

### 10. Neo-Brutalist UI (粗野主义 UI)
**特点**: 仪表板界面、柔和色板、卡片布局、SaaS 美学

| English | 中文 |
|---------|------|
| ![Neo-Brutalist UI EN](images/10-neo-brutalist-ui-en.png) | ![Neo-Brutalist UI CN](images/10-neo-brutalist-ui-cn.png) |

---

### 11. Y2K Pixel Retro (Y2K 像素复古)
**特点**: 90 年代美学、像素艺术、CRT 显示器、复古设计

| English | 中文 |
|---------|------|
| ![Y2K Pixel Retro EN](images/11-y2k-pixel-retro-en.png) | ![Y2K Pixel Retro CN](images/11-y2k-pixel-retro-cn.png) |

---

## 生成信息

- **模型**: bytedance/seedream-v4 (Seedream 4.0)
- **平台**: 302.ai
- **分辨率**: 1920x1080 (16:9)
- **数量**: 22 张图片 (11 种风格 × 2 种语言)
- **生成时间**: 2024-03-24

## 使用脚本

```bash
# 安装依赖
source .venv/bin/activate
pip install requests

# 运行生成脚本
python demos/yc-intro/generate-seedream-final.py
```

## 下载图片

所有图片位于 `demos/yc-intro/images/` 目录：

```bash
# 下载单张图片
curl -O https://raw.githubusercontent.com/AAAAAAAJ/slides/main/demos/yc-intro/images/01-retro-pop-en.png
```

## 风格 Prompt 模板

每种风格的 Prompt 都保存在 `styles/` 目录的 JSON 文件中：

- `styles/retro-pop.json` - 复古波普
- `styles/minimal.json` - 极简主义
- `styles/cyberpunk.json` - 赛博朋克
- `styles/neo-brutalism.json` - 新粗野主义
- `styles/acid-graphics.json` - 酸性设计
- `styles/modern-minimal-pop.json` - 现代极简波普
- `styles/swiss-international.json` - 瑞士国际主义
- `styles/dark-editorial.json` - 暗黑 Editorial
- `styles/design-blueprint.json` - 设计蓝图
- `styles/neo-brutalist-ui.json` - 粗野主义 UI
- `styles/y2k-pixel-retro.json` - Y2K 像素复古

---

## 下一步

1. 选择你喜欢的风格
2. 使用对应的 Prompt 模板生成自己的内容
3. 或者反推新的图片风格，添加到项目中

**项目地址**: https://github.com/AAAAAAAJ/slides
