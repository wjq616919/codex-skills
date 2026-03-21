---
name: ai-director-seedance
description: Build or run an AI director workflow that reads scripts, understands dramatic intent, plans shots, critiques and corrects those choices, scores the result, and outputs Seedance 2.0-ready audiovisual prompts with cinematography, lighting, sound design, and continuity constraints.
---

# AI Director for Seedance 2.0

Turn a script, treatment, outline, or scene into shot plans and Seedance 2.0 audiovisual prompts.

Treat this as director-level work, not generic prompt polishing. Do three things:

1. Understand what the script is trying to express.
2. Decide how that meaning should appear on screen.
3. Translate those decisions into Seedance-ready audiovisual prompts.

## Source Policy

Prioritize professional and official sources over generic prompt folklore.

Use this priority order:

1. official Seedance or ByteDance product material for model behavior and prompt constraints
2. professional team or research lab open-source projects for storyboarding, shot planning, and long-video orchestration
3. community tools only for optional workflow ideas, never as the main authority
4. your own fallback reasoning only when the sources above do not answer the question

When making a substantial planning decision, prefer a rule that can be traced to [source_map.md](./references/source_map.md).
If a rule is only heuristic and not source-backed, treat it as a fallback and keep it conservative.

## Core Rule

Do not force a fixed house style.

Every job must explicitly choose one of these style modes:

- `script_inferred_style`: infer the style from genre, tone, period, subject matter, audience, and dramatic intent in the script.
- `user_locked_style`: obey a user-specified look and medium, then design shots inside that constraint.
- `hybrid_style`: keep user-locked anchors such as medium, texture, or palette, but infer scene-level pacing, shot progression, and camera strategy from the script.

Default to `script_inferred_style` when the user did not specify a style.

## Workflow

### 1. Parse the story before planning shots

Extract:

- scene boundaries
- who is present
- what changes
- what the audience must notice
- emotional turning points
- props or environmental anchors
- time, weather, geography, and period clues

Normalize FDX, Fountain, or loosely structured screenplay text first. See [screenplay_parsing.md](./references/screenplay_parsing.md).
Use `scripts/normalize_script.py` when a deterministic first pass is helpful.

### 2. Build a story bible

Before writing prompts, build a compact internal representation:

- global premise
- theme
- key relationships
- character identity anchors
- location anchors
- continuity risks
- intended audience
- runtime or platform constraints

Do not skip this step on long scripts.
Use `scripts/build_story_bible.py` to generate a reusable first-pass bible from normalized scenes.

### 3. Resolve the visual style source

Use this precedence order:

1. explicit user style lock
2. explicit style instructions inside the script
3. script-derived style inference
4. business or platform constraints
5. neutral cinematic fallback

The skill must store both:

- `style_mode`
- `style_rationale`

The rationale should explain why the chosen look supports the script, not just name a genre.

See [style_inference.md](./references/style_inference.md).

### 4. Plan shots from dramatic purpose, not from prompt templates

For each shot, decide:

- why this shot exists
- what the audience should feel or notice
- what information must be visible
- whether the scene wants restraint, spectacle, intimacy, tension, comedy, or ambiguity

Only then choose:

- shot size
- angle
- lens feel
- foreground and background strategy
- lighting
- movement
- framing density
- beat timing

See [cinematography_taxonomy.md](./references/cinematography_taxonomy.md), [lighting_design.md](./references/lighting_design.md), and [shot_planning.md](./references/shot_planning.md).

### 5. Validate action duration before approving the shot

Do not move from shot idea to final prompt without checking action readability.

For each shot, test whether the available seconds can clearly carry:

- setup
- execution
- result
- reaction

This applies even to long takes.

If a beat depends on one character trying and failing, then another character preparing and trying, the shot must explicitly budget enough readable time for both chains. Do not compress the second performer into a "suddenly already moving" state.

Record:

- the primary action chain
- any secondary action chain
- the available seconds
- the estimated seconds required for readability
- the timing pressure and adjustment

If the shot fails the timing check, simplify, extend, or split it before prompt rendering.

See [action_timing_validation.md](./references/action_timing_validation.md).

### 6. Record the director decision, not just the camera label

For each shot, explicitly record:

- why this shot exists
- what the audience must notice first
- how the subjects are staged
- what the composition is trying to achieve
- whether the visual center changes
- why the camera moves or stays still
- what tempo the shot should have

If you cannot justify these, the shot is not ready.

See [director_decision_framework.md](./references/director_decision_framework.md).

### 7. Critique, correct, and verify the first-pass shot plan

Do not trust the first pass.

Run a critique pass for each shot:

- identify the likely failure mode
- make the smallest useful correction
- verify that the revised shot better serves protagonist priority, dramatic clarity, and controllability

See [critique_correct_verify.md](./references/critique_correct_verify.md).

### 8. Design sound before rendering prompts

For each shot, decide the sound layer with the same discipline as the image layer.

Cover:

- ambience bed
- character micro-vocals
- foley
- magical or stylized effects
- music state and energy
- mix focus
- brand mnemonic if the piece is commercial

Only include sound cues that materially shape emotion, timing, or brand memory.

See [sound_design.md](./references/sound_design.md).

### 9. Render Seedance prompts

Convert each structured shot into a concise audiovisual prompt bundle. Keep the prompt production-oriented and visual, then attach separate lighting-design and sound-design output when those layers materially shape the shot.

Prefer one prompt per shot or one prompt per tightly connected continuous shot.
Prefer final output blocks over explanatory prose.
If the user provides a preferred prompt structure example, mirror that structure closely unless it conflicts with known product constraints.
Do not expose internal review layers in normal final output.
For Chinese screenplay-style outputs, keep front labels sparse, keep movement in the sentence body, and do not overload one long-take line with too many dramatic turns.

See [seedance_rules.md](./references/seedance_rules.md).
See [prompt_format.md](./references/prompt_format.md) for the preferred final-output shape.

### 10. Evaluate and score before finalizing

Score each shot before calling it final.

Use at least these categories:

- narrative fidelity
- protagonist priority
- blocking clarity
- composition logic
- camera motivation
- rhythm control
- action timing readability
- generation controllability

Revise if the overall score is weak or if any critical category fails.

See [evaluation_rubric.md](./references/evaluation_rubric.md).

### 11. Validate continuity and controllability

Check:

- character identity consistency
- wardrobe and prop continuity
- location continuity
- time-of-day continuity
- palette drift
- camera logic across adjacent shots
- sonic continuity across adjacent shots
- prompt overload or conflicting instructions

See [continuity_rules.md](./references/continuity_rules.md).

## Output Contract

The preferred output is a structured shot plan first, audiovisual prompt text second.

Use the schema in [shot_schema.json](./assets/shot_schema.json).

Each shot should capture:

- `narrative_purpose`
- `audience_focus`
- `style_mode`
- `style_rationale`
 - `director_decision`
- `action_timing_validation`
- `subject`
- `action`
- `setting`
- `mood`
- `shot_size`
- `angle`
- `lens`
- `foreground`
- `composition`
- `lighting`
- `lighting_design`
- `camera_movement`
 - `critique_pass`
- `sound_design`
 - `evaluation`
- `continuity_anchors`
- `timecoded_beats`
- `seedance_prompt`

Use three output modes:

- `storyboard_script`: default Chinese final output, shaped like a screenplay-style shot list with scene header, shot lines, and scene-level sound
- `final_prompt_only`: compact prompt-only output with no internal review lines
- `director_review`: analysis mode that may include director decision, critique-correct-verify, and scoring

## Prompt Rules

- Do not dump the whole screenplay into one giant prompt.
- Do not use style labels without translating them into visible properties.
- Do not imitate living directors by name; describe visual properties instead.
- Do not add details that are not supported by the script unless they are necessary to stage the scene and are consistent with the story bible.
- Do not repeat every attribute in every shot. Carry continuity through anchors and references.
- Do not collapse meaningful lighting decisions into one vague adjective when motivated source, edge separation, or material response matter.
- Do not use camera movement without a stated dramatic motivation.
- Do not let supporting characters steal protagonist priority unless the script explicitly shifts focus.
- Do not finalize a shot until blocking, composition goal, focus shift, and tempo are all explicit.
- Do not finalize a shot until the action timing check confirms that setup, execution, result, and reaction are readable in the available time.
- Do not show `导演决策 / 批判校正 / 评分` unless the user explicitly asks for an analysis or review mode.
- Do not stack lens, angle, movement, and multiple effects into the front label area of screenplay-style prompts.
- Do not let a single long-take line carry so many beat changes that the shot becomes hard to read or hard to generate.
- If style is inferred, make the inference explicit in the plan before rendering prompt text.
- If style is locked, keep the lock stable and vary only shot design, blocking, and emphasis.
- Do not overfill every shot with sound. Leave breathing room where silence or light ambience helps the beat land.
- If exact sound sync matters, pair the prompt with audio references rather than relying on text alone.
- If a shot scores below the rubric threshold, revise it before treating it as final output.

## Bundled Resources

- [seedance_rules.md](./references/seedance_rules.md): practical rules for Seedance-ready prompts
- [prompt_format.md](./references/prompt_format.md): preferred final prompt shape for Seedance and Jimeng-style inputs
- [source_map.md](./references/source_map.md): official and professional-team knowledge sources for this skill
- [style_inference.md](./references/style_inference.md): how to infer or lock style
- [cinematography_taxonomy.md](./references/cinematography_taxonomy.md): shot language vocabulary
- [director_decision_framework.md](./references/director_decision_framework.md): blocking-first director reasoning and shot justification
- [lighting_design.md](./references/lighting_design.md): lighting strategy for mood, ratios, materials, animation, and brand polish
- [shot_planning.md](./references/shot_planning.md): planning heuristics from dramatic intent to shot order
- [critique_correct_verify.md](./references/critique_correct_verify.md): revision workflow for stress-testing shots
- [sound_design.md](./references/sound_design.md): sound-layer planning for ambience, foley, score, and brand memory
- [evaluation_rubric.md](./references/evaluation_rubric.md): shot scoring and release thresholds
- [continuity_rules.md](./references/continuity_rules.md): continuity and consistency checks
- [screenplay_parsing.md](./references/screenplay_parsing.md): script normalization guidance
- [shot_schema.json](./assets/shot_schema.json): structured schema for the intermediate plan
- [story_bible_schema.json](./assets/story_bible_schema.json): structured schema for the story bible layer
- [example_shot_plan.json](./assets/example_shot_plan.json): compact example input
- [example_story_bible.json](./assets/example_story_bible.json): compact example story bible
- `scripts/normalize_script.py`: normalize scene-based text into structured JSON
- `scripts/build_story_bible.py`: derive a reusable story bible from normalized scenes
- `scripts/infer_style_profile.py`: derive or merge a style profile
- `scripts/render_seedance_prompt.py`: turn shot plans into audiovisual prompt bundles
- `scripts/validate_prompt.py`: basic prompt checks
- `scripts/score_shot_plan.py`: summarize evaluation scores and enforce quality gates

## Suggested Usage

1. Normalize the script.
2. Build the story bible.
3. Resolve `style_mode`.
4. Produce a shot plan JSON with sound fields.
5. Render Seedance audiovisual prompts from that JSON.
6. Validate the prompts and revise weak shots.

## Command Examples

Normalize a raw script:

```bash
python scripts/normalize_script.py \
  --input /path/to/script.txt \
  --output /tmp/normalized_script.json
```

Build a first-pass story bible:

```bash
python scripts/build_story_bible.py \
  --input /tmp/normalized_script.json \
  --output /tmp/story_bible.json
```

Infer a style profile from a script:

```bash
python scripts/infer_style_profile.py \
  --script /path/to/script.txt \
  --mode inferred \
  --output /tmp/style_profile.json
```

Render prompts from a shot plan:

```bash
python scripts/render_seedance_prompt.py \
  --input ./assets/example_shot_plan.json \
  --output /tmp/seedance_prompts.txt
```

Validate a shot plan before rendering:

```bash
python scripts/validate_prompt.py \
  --input ./assets/example_shot_plan.json
```
