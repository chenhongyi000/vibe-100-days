---
title: "Vibe Coding 100 天挑战 Day 5：Markdown 转公众号排版工具"
series: vibe-100-days
series_index: 5
status: draft
---

# Markdown 转公众号排版工具

写公众号文章时，Markdown 很适合创作，但复制到编辑器里经常会丢样式。

所以 Day 5 做了一个小工具：把 Markdown 转成带内联样式的 HTML，直接复制到公众号编辑器里继续微调。

## 它解决什么问题？

> 文章写完之后，最烦人的不是修改内容，而是标题、引用、代码块和表格全部重新排一遍。

- 标题自动变成公众号友好的样式
- 引用块自动加灰底和左边框
- 代码块保留缩进并转义特殊字符
- 表格自动生成边框和表头

## 一个代码块

```python
def hello(name: str) -> str:
    return f"Hello, {name}!"
```

## 一个表格

| 能力 | 状态 |
| --- | --- |
| 标题排版 | 已支持 |
| 代码块 | 已支持 |
| 表格 | 已支持 |

最后，把命令跑起来：

`python src/wechat_md.py examples/sample_article.md -o examples/sample_article.html`
