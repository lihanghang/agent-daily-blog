// 分享功能 - 全局脚本
console.log('分享脚本加载');

// 复制分享文案
window.shareFunctions = {
  copyFullShareText: function() {
    console.log('copyFullShareText 函数被调用');

    const title = document.title || '文章标题';
    const link = window.location.href;

    // 提取核心观点（找第一个列表或 h2 后的内容）
    let corePoints = '';
    try {
      const article = document.querySelector('article');
      if (article) {
        // 查找第一个列表（通常包含核心观点）
        const ul = article.querySelector('ul');
        if (ul) {
          const items = ul.querySelectorAll('li');
          const points = [];
          items.forEach((item, index) => {
            if (index < 3) { // 只取前3个要点
              points.push(item.textContent.trim());
            }
          });
          if (points.length > 0) {
            corePoints = '💡 核心观点：\n' + points.map(p => '• ' + p).join('\n');
          }
        }
      }
    } catch (e) {
      console.error('提取核心观点失败:', e);
    }

    // 提取摘要
    let summary = '';
    try {
      const article = document.querySelector('article');
      if (article) {
        // 查找第一个非引用的段落
        const paragraphs = article.querySelectorAll('p');
        for (const p of paragraphs) {
          const text = p.textContent.trim();
          // 跳过引用和太短的段落
          if (!text.startsWith('>') && text.length > 50) {
            summary = text;
            break;
          }
        }
      }
    } catch (e) {
      console.error('提取摘要失败:', e);
    }

    // 限制摘要长度
    if (summary.length > 200) {
      summary = summary.substring(0, 200) + '...';
    }

    if (!summary) {
      summary = '点击链接查看完整内容';
    }

    // 生成分享文案
    let shareText = title + '\n\n';
    shareText += summary + '\n\n';
    if (corePoints) {
      shareText += corePoints + '\n\n';
    }
    shareText += '📖 阅读全文：' + link;

    console.log('标题:', title);
    console.log('摘要:', summary);
    console.log('核心观点:', corePoints);
    console.log('链接:', link);
    console.log('完整文本:', shareText);

    if (navigator.clipboard) {
      navigator.clipboard.writeText(shareText)
        .then(() => {
          console.log('✅ 复制成功！');
          // 显示简单的成功提示（不弹窗）
          showSuccessToast();
        })
        .catch(err => {
          console.error('❌ 复制失败:', err);
        });
    }
  }
};

// 显示简单的成功提示
function showSuccessToast() {
  let toast = document.getElementById('copy-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'copy-toast';
    toast.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #42b983; color: white; padding: 12px 24px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 9999; animation: slideIn 0.3s ease;';
    document.body.appendChild(toast);
  }

  toast.textContent = '✅ 已复制到剪贴板';
  toast.style.display = 'block';

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => {
      toast.style.display = 'none';
    }, 300);
  }, 2000);
}

console.log('分享脚本加载完成');
