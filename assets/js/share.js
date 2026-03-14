// 分享功能 - 全局脚本
console.log('分享脚本加载');

// 复制分享文案
window.shareFunctions = {
  copyFullShareText: function() {
    console.log('copyFullShareText 函数被调用');

    const title = document.title || '文章标题';
    const link = window.location.href;

    // 提取摘要
    let summary = '';
    try {
      const article = document.querySelector('article');
      if (article) {
        const firstP = article.querySelector('p');
        if (firstP) {
          summary = firstP.textContent.trim();
          if (summary.length > 150) {
            summary = summary.substring(0, 150) + '...';
          }
        }
      }
    } catch (e) {
      console.error('提取摘要失败:', e);
    }

    if (!summary) {
      summary = '点击链接查看完整内容';
    }

    const shareText = `${title}\n\n${summary}\n\n${link}`;

    console.log('标题:', title);
    console.log('摘要:', summary);
    console.log('链接:', link);
    console.log('完整文本:', shareText);

    if (navigator.clipboard) {
      navigator.clipboard.writeText(shareText)
        .then(() => {
          console.log('✅ 复制成功！');
          alert('复制成功！\n\n' + shareText);
        })
        .catch(err => {
          console.error('❌ 复制失败:', err);
          alert('复制失败: ' + err);
        });
    } else {
      alert('浏览器不支持 Clipboard API');
    }
  }
};

console.log('分享脚本加载完成');
