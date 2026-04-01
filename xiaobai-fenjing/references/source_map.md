# 来源映射

这份 skill 以 `/Users/will/Documents/se/老白的分镜_视频/转写文稿` 为核心语料，但这里保留的是规则映射，不是课程摘抄。

## 术语归一

转写里出现的口语和误识别，统一归到以下术语：

- `分镜`
- `景别`
- `视角`
- `轴向`
- `控制信息`
- `主镜`
- `连接镜`

## 重点章节与落地规则

### 第 1 节：`1-（先导片）分镜构思的思路.md`

提炼为：

- 分镜先解决“讲什么”，再谈“怎么拍”
- 观众会关心的是有意义变化，不是镜头数量
- 先找这场戏真正重要的变化，再决定镜头组织

对应落点：

- `references/methodology.md` 的“总原则”“先找有意义变化”
- `scripts/plan_shot_flow.py` 的 `scene_objective` 和主镜筛选

### 第 4 节：`4-完成一场戏的分镜.md`

提炼为：

- 一场戏要有主次分工
- 主镜承担主要叙事责任
- 连接镜负责补信息、顺接、强调
- 完成一场戏，关键是镜头之间能顺着讲下去

对应落点：

- `references/methodology.md` 的“主镜”“连接镜”
- `scripts/plan_shot_flow.py` 的主镜 / 连接镜策略
- `scripts/audit_transitions.py` 的修顺优先级

### 第 10 节：`10-景别实战.md`

提炼为：

- 景别先看内容能不能说明白
- 内容成立后，景别变化才承担节奏和强调
- 相邻镜头的景别关系会直接影响顺接感

对应落点：

- `references/methodology.md` 的“景别”
- `references/transition_audit.md` 的“景别变化是否有动机”
- `scripts/plan_shot_flow.py` 的景别选择

### 第 11 节：`11-视角实战.md`

提炼为：

- 视角要服务观众跟随谁
- “看到 + 反应”是重要组合
- 主观视角能帮助聚焦，但不能破坏信息清晰

对应落点：

- `references/methodology.md` 的“视角”
- `references/transition_audit.md` 的“视线是否成立”
- `scripts/plan_shot_flow.py` 的 `viewpoint` 和 `audience_focus`

### 第 12 节：`12-控制信息在实战中的应用.md`

提炼为：

- 悬念和控制信息必须先建立观众期待
- 中间要给线索，让观众能参与
- 该揭示时要揭示，不要无意义拖延

对应落点：

- `references/methodology.md` 的“控制信息”
- `references/transition_audit.md` 的“信息揭示是否太早或太晚”
- `scripts/plan_shot_flow.py` 的 `info_control`

### 第 16 节：`16-运动规律X表演.md`

提炼为：

- 动作拆解需要考虑 setup / execution / result / reaction
- 表演变化要给观众读清，不要压成一团
- 复杂动作镜头要为可读性服务

对应落点：

- `references/methodology.md` 的“动作拆解”“表演与反应”
- `scripts/plan_shot_flow.py` 的动作链判断
- `scripts/audit_transitions.py` 的“动作是否有承接”

### 第 19 节：`19-拉片方法.md`

提炼为：

- 拉片先按单一维度拆，不要眉毛胡子一把抓
- 把单项规律抽出来，再回到原创分镜综合应用

对应落点：

- `references/methodology.md` 的“拉片方法如何反哺原创分镜”
- 整个 skill 的规则库结构拆成方法论 / 顺接 / 输出 / 来源映射四份

## 使用边界

- 这份 skill 不是课程原文复写。
- 规则是根据转写内容整理、归一和重述后的执行规范。
- 若转写里个别细节表述模糊，以“叙事清晰、顺接自然、镜头责任明确”为最高准则。
