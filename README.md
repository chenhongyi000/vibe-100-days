# Vibe 100天挑战

> 用 Vibe Coding 的方式，100 天持续产出小工具、实践文章和复盘记录。

## 系列进度

| Day | 项目 | 文章 | 配套代码 | 状态 |
|-----|------|------|----------|------|
| 1 | CleverName 智能重命名工具 | [Markdown](001-clevername-smart-renamer.md) / [HTML](001-clevername-smart-renamer.html) | [day1-clevername](day1-clevername/) | 已完成 |
| 2 | tree-gen 项目结构生成器 | [Markdown](day2/article.md) / [HTML](day2/article.html) | [day2](day2/) | 已完成 |
| 3 | wttr-cli 终端天气工具 | [Markdown](day3/article.md) / [HTML](day3/article.html) | [day3](day3/) | 已完成 |
| 4 | JSON 转 Excel 工具 | 待补充 | 待补充 | 已完成 |
| 5 | wechat-md Markdown 转公众号排版工具 | [Markdown](day5/article.md) / [HTML](day5/article.html) | [day5](day5/) | 已完成 |
| 6-100 | 后续 95 天选题规划 | [内容日历](planning/content-calendar.md) | [选题池](planning/ideas.md) | 待启动 |

## 后续规划

- Day 6-100 的后续项目清单、公众号标题和推文摘要见 `planning/content-calendar.md`。
- 轻量选题勾选清单见 `planning/ideas.md`。

## 命名建议

- 新增文章优先放在独立 Day 目录中，例如 `day4/article.md`、`day4/article.html`。
- 配套项目源码、测试和示例可以与文章同目录保存。
- 不提交 `__pycache__`、`.pytest_cache`、虚拟环境、构建产物和临时文件。
- 如果某一天只有文章、没有代码，也保留 Day 目录，便于后续补充素材。

## 发布前检查

- 文章 frontmatter 已填写 `title`、`series`、`series_index`、`status`、`date`、`tags` 和 `summary`。
- `planning/content-calendar.md` 已更新状态。
- `planning/ideas.md` 中对应选题已勾选。
- 使用 `scripts/md2wechat.py` 生成并检查 HTML。
- 封面图和正文配图已放入 `assets/` 对应目录。
