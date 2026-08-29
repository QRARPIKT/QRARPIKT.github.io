# AGENTS.md — Qラピカ文库站点维护合约

> 任何 agent 接入本仓库，先读完本文件再动手。
> 详细规范、交付包结构要求与踩坑史见 `Qラピカ文库-交接文档.md`；两者冲突时以本文件为准。

## 站点与角色

- 本仓库 = 站点本体：GitHub Pages 仓库 `QRARPIKT/QRARPIKT.github.io` 的本地工作副本，线上地址 <https://qrabica.com>。
- **写作 agent**：产出小说与配套档案，打成 zip 由用户放入 `incoming/`。写作 agent 永远不直接碰本仓库。
- **站点 agent（你）**：收货、校验、重建网页、同步 archive、修改仓库内文件。
- **用户**：审阅确认、执行全部 git 提交操作、拍板所有文案。

**铁律：站点 agent 永远不改正文内容。** 交付物与站内文案/设定冲突时（如 intro 回归废弃设定、简介与正文打架），拦下来报告用户，由用户裁决。

## git 边界（最高优先级规则）

- 你只做文件修改。只读 git 命令（`status` / `diff` / `log`）允许。
- **`git add` / `git commit` / `git push` 及一切改动仓库状态的操作，一律由用户本人在终端执行，你永远不执行。** 你只负责在收尾时给出建议的 commit message。
- 每轮收尾输出：校验结果 + 变更文件清单 + 建议的 commit message，交给用户执行。
- 用户 push 后：提醒查看 Actions 构建结果，等 1–2 分钟生效；`style.css` 有缓存，样式类改动后提醒强刷（Ctrl+Shift+R）。
- 如用户要求核验线上：抓取 qrabica.com 全部页面（首页 + 作品页 + 手记 + 全部章节页）与本地去空白后比对，差异必须为 0（偶发 504/超时重试即可）。此为只读操作，可直接做。

## 收稿 → 上站流水线

**第 0 步：暂存与防串书**

- 用户把交付 zip 放进 `incoming/`（已 gitignore，不入库）。解压为 `incoming/{book-id}/`，按 `清单.md` 核对文件数。
- 跨书同名文件（ch01.md 等）历史上真实串过：按当批清单逐名取件 + 内容指纹校验（过拟合必含"松枝"；落语心中必含"八云/晶太/助六"）。

**第 1 步：一致性校验（不过就停）**

- chapters/ 逐章与 final.md diff（忽略 final 的章题切分行与 `---` 分隔线、行尾空白）。全部一致才继续。
- 章题比对：chapters 首行标题 == final 对应章标题（逐字）。
- 探针：「」计数相等、“”计数相等；该书废设定词表零命中（词表在该书 truth/手册里）。
- notes.md 查「【」占位符（含带文字的变体，查「【」而非「【】」）。

**第 2 步：重建网页**（仓库根目录执行）

```bash
python3 scripts/build_site.py --book-dir incoming/{book-id} --site-dir . \
  --book-id {book-id} --title {书名}
```

- 章节页永远全量重生成；脚本同时把 documents/reviews/chapters/final 全量复制到 `archive/{book-id}/`。
- 重建后检查：章题 h1 正确、特殊块渲染（过拟合 ch10 的 `table class="comp"`、顾问记录 worklog 块、落语 epigraph 块、烧却告白 `## 一` 小节号）。

**第 3 步：人工页手工处理（脚本 skip-if-exists，永不覆盖）**

- `works/{book-id}/index.html`：章题或序号体系一变，手动重写 `<ul class="chapter-list">` 目录。
- `works/{book-id}/notes.html`：保留页首 warn 泄底警告块，正文由 notes.md 重新注入（`## ` → h2）。
- `works/overfitting/handbook.html`（仅过拟合）：由 documents/二读手册.md 重新生成前，先清掉页首残留的 blockquote 警告块，只保留一条。
- 首页 `index.html` 书卡、`assets/style.css` / `reader.js`：人工领地，脚本不会动；style.css 若有手工改动，顺手同步 `scripts/build_site.py` 里的 STYLE 常量（两者已验证字节级一致）。

**第 4 步：archive 抽验**

- truth.md 与 final_manuscript.md 的 md5 与交付包一致。

**第 5 步：收尾交用户**

- 输出校验表 + `git status` 变更清单 + 建议 commit message。git add/commit/push 由用户执行。

## 人工领地（文案）

- 首页书卡（短版）与作品页简介（长版）是两个独立文案，用户给哪段贴哪段，不要互相推导。
- 交付包里的 intro.md 只进 archive 存档，**不自动上页**（有过 intro 回归废弃设定的前科）。
- 字数 meta（如"约12.2万字"）不会自动更新；正文大改后提醒用户是否改 meta。

## 坑表

1. **同名跨书冲突**：按批清单取件 + 内容指纹，绝不按文件名猜归属。
2. **清单少报**：不信"改了 N 章"，全量 diff final.md 说了算。
3. **intro 回归**：上页前与正文设定核对，不符就拦。
4. **【】占位符**：永不写跨书对照，见到即删（带文字的变体也要查）。
5. **手册警告叠加**：重生成 handbook 前先清页首 blockquote。
6. **TOC 不自动更新**：章题/序号体系一变，作品页目录必须手工同步。

## 现有书籍（book-id）

| book-id | 书名 | 章数 | 序号体系与格式注意 |
|---|---|---|---|
| proof-read | 校样 | 13 | 第一章～第十三章；无 reviews 目录 |
| murder-ballad | 谋杀歌谣 | 13 | 第一章～第十三章；章首歌词块（缩进格式敏感） |
| overfitting | 过拟合 | 26 | 第一章～第二十六章；章末顾问记录（〔〕引用块 → worklog）；ch10 有白板 + `table.comp` 表格 |
| rakugo-shinju | 落语心中 | 25 | 序章 + 第一章～二十三章 + 终章；章首俳句 epigraph（`> ` 引用块） |
| burning-confession | 烧却告白 | 13+附録 | 第一章～第十三章+附録；章内 `## 一` 小节号；章题为中文 |
