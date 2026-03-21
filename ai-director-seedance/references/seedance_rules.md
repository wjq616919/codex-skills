# Seedance 2.0 Prompt Rules

Use these rules when converting structured shot plans into prompts.

## What matters most

- Keep prompts visual and direct.
- Prefer one main subject and one main action per shot.
- Use only details that materially affect the frame, motion, or identity.
- For complex shots, express timing as beats or time ranges.
- When continuity matters, rely on stable anchors and references instead of restating every property.

## Practical constraints

- Design per-shot prompts. Do not expect one long prompt to faithfully stage an entire screenplay.
- Official product material indicates support for text plus image, video, and audio references. Practical workflows should treat references as first-class controls.
- Public product material also indicates multi-reference workflows with up to 9 images, 3 videos, 3 audio clips, and clips up to 15 seconds. Keep shot design within those limits unless newer official docs override them.

## What to include

Usually include these in descending order of value:

1. subject identity
2. visible action
3. environment and time
4. style expressed as visible properties
5. shot size and angle
6. lens feel
7. foreground or composition cue
8. lighting
9. camera movement
10. timing beats for complex motion

## What to avoid

- conflicting styles in one shot
- camera instructions with no narrative reason
- non-visual literary analysis inside the prompt
- too many adjectives that do not change the frame
- contradictory movement such as "static handheld dolly rush"
- uncontrolled style references by director name

## Good structure

For Chinese prompts:

```text
主体 + 动作 + 场景/时间 + 可见风格特征 + 景别/角度/焦段感受 + 前景/构图 + 光线 + 运镜 + 分段动作
```

For final user-facing output, prefer a block instead of one dense paragraph:

```text
画面提示词：
主体 + 场景/时间 + 关键动作 + 可见风格特征 + 景别/角度/焦段感受 + 前景/构图 + 光线 + 运镜

分段动作：
[0s-2s] ...

一致性锚点：
...

声音提示：
...
```

For English prompts:

```text
subject + action + setting/time + visible style traits + shot size/angle/lens + foreground/composition + lighting + camera movement + timed beats
```

## Timecoded beats

Use timecoded beats when:

- a single shot contains more than one movement phase
- the camera movement changes over time
- the subject action and camera action must stay synchronized

Do not use timecoded beats on every shot. Use them where they increase control.

## References

Use image or video references when the shot depends on:

- stable character identity
- costume continuity
- product fidelity
- repeating location geometry
- a specific camera grammar already proven in a previous shot

If reference assets exist, mention their role in the shot plan even if the final prompt text stays concise.
