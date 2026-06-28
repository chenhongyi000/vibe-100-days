# CleverName 灵名

> 让杂乱无章的照片和文件，一秒拥有会说话的姓名

## 简介

CleverName 是一个智能批量文件重命名工具，专为摄影师、新媒体运营和资料整理爱好者设计。无需学习正则表达式，通过填空式交互即可构建命名规则。

## 功能特性

- 📁 **拖拽导入**：支持文件夹拖拽，自动递归扫描
- 📷 **智能日期提取**：优先读取 EXIF 拍摄时间，无 EXIF 则使用文件时间
- 🧩 **规则组合器**：填空式构建命名模板，支持日期、计数器、原名、AI 标签等
- 👁️ **实时预览**：执行前以表格形式展示新旧文件名对照
- ↩️ **一键回滚**：自动生成 `restore.bat`，双击即可恢复原名
- 🤖 **AI 语义标签**（可选）：自动识别图片内容，生成中文关键词

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
# 交互模式
python clevername.py

# 直接指定文件夹
python clevername.py "C:\Photos\2024"
```

### 三步完成重命名

1. **导入**：拖入文件夹，选择文件类型过滤
2. **配置**：选择命名模板（日期+计数器 / 日期+原名 / AI描述+日期 / 自定义）
3. **确认**：预览新旧对照表，确认后执行

## 命名模板

| Token | 含义 | 示例 |
|-------|------|------|
| `{date}` | EXIF/文件时间 | `2024-01-15_143022` |
| `{counter}` | 自动补零计数器 | `001`, `002`... |
| `{original}` | 原文件名 | `IMG_1234` |
| `{original:N}` | 原名前 N 个字符 | `IMG_12` (N=6) |
| `{ext}` | 扩展名 | `.jpg` |
| `{ai_desc}` | AI 语义标签 | `金毛犬_草地` |

## 使用 AI 语义标签（可选）

```bash
# 方式1：使用 OpenAI 兼容 API
set OPENAI_API_KEY=sk-xxx
set OPENAI_BASE_URL=https://api.openai.com/v1
set CLEVERNAME_AI_MODEL=gpt-4o-mini

# 方式2：使用本地 Ollama（需安装 llava 模型）
ollama pull llava
ollama serve
```

不配置 AI 时，模板 3 不可用，其他功能正常。

## 回滚

如果重命名后不满意，运行生成的脚本即可恢复：

- **Windows**：双击 `restore.bat`
- **Mac/Linux**：`python restore.py`

## 项目结构

```
day1-clevername/
├── clevername.py          # 主入口
├── src/
│   ├── scanner.py         # 文件扫描
│   ├── metadata.py        # EXIF/日期提取
│   ├── rules.py           # 规则引擎
│   ├── preview.py         # 预览面板
│   ├── executor.py        # 执行与回滚
│   ├── ai_labeler.py      # AI 标签（可选）
│   └── ui.py              # 终端 UI
├── requirements.txt
└── README.md
```

## License

MIT