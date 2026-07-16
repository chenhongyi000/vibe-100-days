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
| 6 | img-slim 批量图片压缩器 | [Markdown](day6/article.md) / [HTML](day6/article.html) | [day6](day6/) | 已完成 |
| 7 | dupe-scout 文件夹重复文件扫描器 | [Markdown](day7/article.md) / [HTML](day7/article.html) | [day7](day7/) | 已完成 |
| 8 | pdf-kit-lite PDF 拆分合并工具 | [Markdown](day8/article.md) / [HTML](day8/article.html) | [day8](day8/) | 已完成 |
| 9 | excel-cleaner Excel 自动清洗器 | [Markdown](day9/article.md) / [HTML](day9/article.html) | [day9](day9/) | 已完成 |
| 10 | csv-encoding-fixer CSV 编码修复工具 | [Markdown](day10/article.md) / [HTML](day10/article.html) | [day10](day10/) | 已完成 |
| 11 | file-archiver 批量文件归档器 | [Markdown](day11/article.md) / [HTML](day11/article.html) | [day11](day11/) | 已完成 |
| 12 | meeting-minutes-organizer 会议纪要整理器 | [Markdown](day12/article.md) / [HTML](day12/article.html) | [day12](day12/) | 已完成 |
| 13 | todo-text-extractor TODO 文本提取器 | [Markdown](day13/article.md) / [HTML](day13/article.html) | [day13](day13/) | 已完成 |
| 14 | screenshot-renamer 批量截图重命名器 | [Markdown](day14/article.md) / [HTML](day14/article.html) | [day14](day14/) | 已完成 |
| 15 | invoice-info-extractor 发票信息提取器 | [Markdown](day15/article.md) / [HTML](day15/article.html) | [day15](day15/) | 已完成 |
| 16 | contract-keyword-checker 合同关键词检查器 | [Markdown](day16/article.md) / [HTML](day16/article.html) | [day16](day16/) | 已完成 |
| 17 | weekly-reporter 周报生成器 | [Markdown](day17/article.md) / [HTML](day17/article.html) | [day17](day17/) | 已完成 |
| 18 | word-image-exporter Word 图片导出器 | [Markdown](day18/article.md) / [HTML](day18/article.html) | [day18](day18/) | 已完成 |
| 19 | excel-diff 表格差异对比器 | [Markdown](day19/article.md) / [HTML](day19/article.html) | [day19](day19/) | 已完成 |
| 20 | filename-normalizer 文件名批量规范器 | [Markdown](day20/article.md) / [HTML](day20/article.html) | [day20](day20/) | 已完成 |
| 21 | wechat-article-pusher 公众号文章自动推送工具 | [Markdown](day21/article.md) / [HTML](day21/article.html) | [day21](day21/) | 已完成 |
| 22-100 | 后续 79 天选题规划 | [内容日历](planning/content-calendar.md) | [选题池](planning/ideas.md) | 待启动 |

## 后续规划

- Day 22-100 的后续项目清单、公众号标题和推文摘要见 `planning/content-calendar.md`。
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
