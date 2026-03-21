# Prompt Format

## Purpose

Use this file when the user wants final prompt text, not director analysis.

The default final output should look like prompt blocks that can be copied into Jimeng or Seedance-style interfaces with minimal cleanup.

## Core rule

Do not output final prompts as long explanatory prose.

If you need generic prompt blocks instead of screenplay-style output, use this block structure:

```text
[shot_id]
画面提示词：
...

灯光设计：
...

分段动作：
...

一致性锚点：
...

声音提示：
...
```

When the user provides a preferred screenplay-like structure, mirror it. The default Chinese final output should follow this pattern:

```text
全局风格：
...

【00-15s｜第一幕：标题】
镜头1：1-4s [大特写][冷色逆光][静态] ...
镜头2：5-8s [近景][平视][慢推] ...
镜头3：9-12s [特写][平视][静态] ...
音效：...
```

This is not a guaranteed official syntax. It is a practical formatting pattern that often improves controllability because each time range is explicitly bound to its own shot description.

## Chinese visual prompt shape

Keep the main visual line compact and ordered:

```text
主体 + 场景/时间 + 关键动作 + 风格特征 + 景别/角度/焦段感受 + 前景/构图 + 光线 + 运镜
```

## Screenplay shot rules

For Chinese screenplay-style output, prefer these rules:

- front labels should be at most `1-2`
- default to `shot size` first
- add one more label only when it materially helps, usually a non-neutral angle or a special effect cue
- do not pack lens feel and camera movement into the front labels by default
- write camera movement in the shot sentence itself
- one shot should carry one primary dramatic task
- long takes are allowed, but do not cram too many story turns into one line
- keep sound at the end of the scene block, not between shot lines
- pass each shot through action timing validation before final output, but keep that validation internal unless the user asks for review mode

Good:

```text
镜头1：0-4s [近景] 绒绒轻轻扒拉棉桃，镜头缓慢推进，棉桃只轻轻晃动，没有变得蓬松。
镜头2：4-8s [近景][侧拍] 絮絮扇动棉絮翅膀，镜头轻轻横移跟住动作，粒子落在棉桃表面，但棉桃依旧没有变化。
```

Avoid:

```text
镜头1：0-8s [近景][平视][标准焦段视感][缓慢推进→横移→跟拍] ...
```

The example above overloads the front label area and makes the prompt read like internal camera notes rather than a clean shot script.

When lighting is materially important, also surface it in a separate block:

```text
灯光设计：
主光：...
辅光：...
轮廓光：...
背景光：...
色温关系：...
```

Good example:

```text
春日新疆棉田，双棉花萌宠绒绒和絮絮蹲在青涩棉桃前发愁，国风萌系奇幻动画，暖金治愈光感，棉絮粒子漂浮，中远景平视缓慢推进，前景虚化棉枝，柔和逆光。
```

Avoid this shape for final prompts:

```text
整体画面温柔、轻愁、可爱，绝对突出两只棉花萌宠主体，环境氛围前置……
```

The example above is director commentary, not a clean final prompt.

## Timecoded beats

Use timecoded beats only when they increase control.

Good shape:

```text
[0s-2s] ...
[2s-5s] ...
[5s-8s] ...
```

For screenplay-style outputs, convert those beats into shot lines instead of a separate section when that reads more naturally:

```text
镜头1：0-2s [近景] ...
镜头2：2-5s [近景][侧拍] ...
镜头3：5-8s [远景] ...
```

Do not write timecoded beats unless:

- the camera movement changes
- the action changes in phases
- sync matters

## Consistency anchors

Keep anchors outside the main prompt line when possible.

Good:

```text
一致性锚点：
绒绒白绒棉花精灵，絮絮浅粉棉絮翅膀，玉兔Q版垂耳，春日新疆棉田，暖金阳光，棉絮粒子
```

This reduces prompt clutter while preserving repeatability.

## Sound prompt shape

Do not bury sound inside the main visual line.

Prefer:

```text
声音提示：
春风拂过棉田的沙沙声，棉絮轻响，软萌叹气声，轻柔琵琶和竹笛
```

If the platform supports audio references and sync matters, add the reference separately instead of over-describing sound in text.

## Lighting output shape

Do not rely on one vague phrase like `暖光` when lighting meaningfully affects emotion, texture, or brand polish.

Prefer:

```text
灯光设计：
主光：暖金漫射夕阳从左后上方包裹角色和棉朵
辅光：棉田地面反射形成低反差自然补光
轮廓光：逆光勾亮棉絮纤维边缘
背景光：远处棉浪略亮半档，拉开空间层次
色温关系：暖主光，空气层略偏冷，画面更通透
```

If the shot plan only has a simple `lighting` field, the renderer should still expose a visible fallback such as:

```text
灯光设计：
光线锚点：暖金逆光、低反差补光、粒子边缘发光
```

## Director review shape

When the user explicitly asks for analysis, review, or internal reasoning, expose the reasoning layers explicitly:

```text
导演决策：
目的：...
观众先看：...
主体调度：...
构图目标：...
视觉重心转移：...
运镜动机：...
节奏：...

批判校正：
风险：...
修正：...
定稿依据：...

评分：
叙事... 主体... 调度... 构图... 运镜... 节奏... 可控... 总分.../5
```

These blocks are not official platform syntax. They are review and quality-control scaffolding and should stay hidden in normal final prompt output.

## Output preference

When a user says:

- “直接拆成提示词”
- “给我可复制的即梦提示词”
- “直接生成prompt”

default to `storyboard_script` or `final_prompt_only`, not narrative explanation or review layers.
If the user shows a reference image or example prompt structure, prioritize that structure for the final output.

### Output modes

- `storyboard_script`: Chinese screenplay-style output with scene header, timed shot lines, and a single scene-level `音效` line. This should be the default Chinese final format.
- `final_prompt_only`: compact prompt-only output without director review notes.
- `director_review`: internal review output that can include `导演决策 / 批判校正 / 评分`.
