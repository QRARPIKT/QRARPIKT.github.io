# 《谋杀歌谣》Murder Ballad — 创作计划

用户要求：5万字以内本格推理，东京银座都市背景，不强制 fancy 反转，以最适于诡计设计的思路构建。输出 md/txt。
技能：用户技能 `honkaku-mystery-writing`（独家使用，不走内置 general-writing）。

## 阶段 0+1：真相档案先行（truth-first）
- 委派「plot-architect」子代理：设计核心诡计（按阶段0预算：互锁锚点≤8、动作链≤3步、优先解释层诡计）、人物表、分钟级真实时间线 + 认知版对照、锚点推算表（代码实算复核）、物理可行性清单、CL-xx线索台账、叙述纪律。
- 产出：`truth.md` → 由 logic verifier 子代理独立复核（重推时间线、物理/医学窗口、公平性）。
- 通过后产出分章大纲 `outline.md`（每章摘要+本章埋设/回收线索编号）。

## 阶段 2：分章写作（swarm，串行 writer + 并行评审）
- 单一 fiction_writer 每批 3–4 章（约 12–14 章 / 4.5 万字内）。
- 每批完成后，下一批 writer 与上一批的双评审（逻辑/时间线审查员 + 文风/节奏审查员）同批并行派发。
- 修订顺序铁律：先改 truth.md → 再改正文 → 跑校验。
- WARNING/REVISE → 派发 fix 子代理，不内联修。

## 阶段 3：机器化校验
- 每轮修订后跑 `scripts/verify_probes.py`：陈旧字符串、锚点一致性、引号配对、禁用词/破折号预算、字数实测。
- 全部 PASS 才合订。

## 阶段 4：终稿评审 + 交付
- 终稿再做一轮双视角评审；HIGH 问题修复后合订为单一 markdown。
- 交付：`/mnt/agents/output/murder-ballad/谋杀歌谣.md`（用户明确要 md/txt，跳过 docx）。
