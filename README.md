# Qラピカ文库

本格推理小说个人文库（GitHub Pages 静态站）。

## 结构
- `index.html` — 文库首页
- `works/<作品名>/` — 每部作品：作品页（无剧透简介+章节导航）、`ch01-*.html` 阅读页、`notes.html` 创作手记（含泄底警告）
- `assets/` — 样式与阅读页工具脚本
- `archive/<作品名>/` — 创作过程档案（真相时间线、修订记录、外审报告等，**泄底**，网页不直链）
- `scripts/build_site.py` — 建站脚本（章节页生成 + archive 同步）
- `incoming/` — 写作 agent 交付包暂存（gitignore，不入库）

维护合约（agent 职责与 git 边界）见 `AGENTS.md`。

## 新作品入库流程
1. `works/` 下新建作品目录，按既有三段式（正文 / 故事简介 / 创作手记）放页面
2. 首页追加 `.work-card`
3. 过程文件放 `archive/<作品名>/`

章节页与 archive 同步用 `scripts/build_site.py` 生成；`git add` / `commit` / `push` 一律由维护者手动执行。
