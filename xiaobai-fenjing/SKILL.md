---
name: xiaobai-fenjing
description: 把剧本、场景文本或 beat outline 按老白分镜方法重构成叙事清晰、镜头顺接自然的专业中文分镜脚本。适用于“剧本转分镜”“补主镜/连接镜”“检查镜头衔接自然不自然”“按老白分镜方法重做”等请求。
---

# 小白分镜

把剧本、场景文本、treatment 或 beat outline，转成只输出最终结果的专业中文分镜脚本。

默认目标：

- 媒介方向：`通用影视分镜`
- 输出语言：`中文`
- 节奏策略：`适度重构节奏`
- 输出形式：`只给最终分镜，不展示分析过程`

用这个 skill 处理：

- `剧本转分镜`
- `按老白分镜方法重做`
- `检查镜头衔接自然不自然`
- `补连接镜 / 主镜`
- `把脚本做成专业分镜脚本`

## 核心承诺

- 内容优先，镜头手法服务叙事。
- 先找每场戏的“有意义变化”，再设计镜头。
- 主镜负责重要信息，连接镜只负责补信息、顺接、强调。
- 每个镜头都要检查和前后镜头的衔接是否自然。
- 允许适度重构节奏，但不改 scene 顺序，不新增原脚本没有的剧情事实。
- 默认只交付最终 shot list，不外显中间分析。

## 输出格式

每个镜头固定使用导演版格式：

```text
01A [景别｜持续时间]
机位/运动：...
画面：...
发生：...
接点：...
情绪：...
```

严格遵循 [output_contract.md](./references/output_contract.md)。

## 工作流

按下面顺序执行，不要跳步：

1. 先把用户输入整理成 `scene / beat / dialogue / action` 结构。
   - 优先运行 `scripts/normalize_script.py`
2. 为每场戏识别“有意义变化”。
   - 先回答：这一场到底要让观众读懂什么变化
3. 找出必须承担叙事责任的主镜。
   - 主镜优先承接情绪转折、关系变化、关键信息揭示、决定性动作、必须读懂的状态变化
4. 只在必要处加连接镜。
   - 连接镜只允许做三件事：补有效信息、让主镜之间更顺、扩大重点镜头篇幅
5. 对每一对相邻镜头做顺接审查。
   - 运行 `scripts/audit_transitions.py`
6. 如果 cut 不自然，优先修正镜头关系，再考虑加镜头。
   - 先改镜头顺序或景别关系
   - 再改机位/视角
   - 最后才加新镜头
7. 只输出最终 shot list。
   - 运行 `scripts/render_shotlist.py`
   - 不展示 `scene_objective / audience_focus / main_shots / connector_shots / transition_audit / continuity_risks`

## 内部工作模型

内部可以构建这些字段，但默认不要展示给用户：

- `scene_objective`
- `audience_focus`
- `main_shots`
- `connector_shots`
- `transition_audit`
- `continuity_risks`

## 决策规则

### 主镜

- 先给主镜叙事责任，再谈景别和机位。
- 情绪转折、关系变化、关键信息揭示、决定性动作，优先落在主镜上。
- 主镜必须让观众读懂“这一拍为什么重要”。

### 连接镜

- 只在以下场景加连接镜：
  - 主镜之间缺必要信息
  - 两个主镜直接相接不顺
  - 重点镜头需要展开一下才会更有力
- 不要为了“镜头多”而补空镜头。
- 如果 cut 不顺是前镜头信息量错了，先重写前镜头，不要硬补 bridging shot。

### 景别

- 先判断内容能不能说清楚，再决定景别。
- 内容允许自由度时，再利用景别变化做强调、顺接和节奏控制。
- 不要为了变化而变化。

### 视角与轴向

- 视角先服务“观众现在该跟谁走”。
- 如果角色视角能让信息更集中、情绪更强，就优先考虑“看到 + 反应”组合。
- 轴向稳定优先于花哨机位。

### 控制信息

- 先建立观众想知道答案的期待，再藏信息。
- 藏信息期间要持续给参与线索，不要空吊胃口。
- 控制信息的目标是娱乐观众，不是折磨观众。

### 节奏改编

- 可以重排同一场戏里的信息揭示顺序。
- 可以新增反应镜、插入镜、过渡镜、主观视角镜。
- 不改变 scene 顺序。
- 不新增原脚本没有的新剧情事实。

## 配套脚本

- `scripts/normalize_script.py`
  - 把输入整理成规范的 scene / beat JSON
- `scripts/plan_shot_flow.py`
  - 基于规则生成内部 shot plan，并先做一次自动修顺
- `scripts/audit_transitions.py`
  - 审查相邻镜头顺接，自带基础修正逻辑
- `scripts/render_shotlist.py`
  - 渲染最终中文分镜脚本

推荐流程：

```bash
python3 scripts/normalize_script.py --input assets/example_scene.txt --output /tmp/xiaobai-normalized.json
python3 scripts/plan_shot_flow.py --input /tmp/xiaobai-normalized.json --output /tmp/xiaobai-plan.json
python3 scripts/render_shotlist.py --input /tmp/xiaobai-plan.json --output /tmp/xiaobai-shotlist.md
```

## 参考资料

- [methodology.md](./references/methodology.md)
- [transition_audit.md](./references/transition_audit.md)
- [output_contract.md](./references/output_contract.md)
- [source_map.md](./references/source_map.md)

## 执行提醒

- 最终给用户时，默认只交付分镜结果，不复述中间分析。
- 如果用户特别要求展示思路，再把内部结构单独展开。
- 如果原脚本事实不完整，可以补镜头连接方式，但不要替用户编新剧情。
