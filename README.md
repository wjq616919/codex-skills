# Codex Skills

This repository packages four custom Codex skills:

- `ai-director-seedance`
- `continuity-director`
- `storyboard-director`
- `xiaobai-fenjing`

## Included Skills

### `ai-director-seedance`
Use when you want an AI director workflow oriented toward Seedance/Jimeng-style video prompt generation:

- script understanding
- director decisions
- pacing and timing checks
- lighting and sound design
- continuity and object-state control

### `continuity-director`
Use when you want a dedicated continuity workflow between adjacent shots, prompt segments, or reference frames:

- pose continuity and action-phase handoff
- eyeline direction repair
- camera-axis and scene-space consistency
- lighting-source and atmosphere continuity
- bridge-shot repair for broken joins

### `storyboard-director`
Use when you want a professional storyboard workflow:

- script review before shot planning
- shot-by-shot storyboard writing
- expression design
- action timing validation
- object state control
- storyboard-style prompt output

### `xiaobai-fenjing`
Use when you want to restructure a script or scene text into a professional Chinese shot list in Lao Bai's storyboard method:

- scene-level dramatic change identification
- main-shot and connector-shot planning
- transition naturalness checks
- beat-preserving rhythm restructuring
- director-style Chinese shot list output

## Install

Copy the skill folders into your local Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R ai-director-seedance ~/.codex/skills/
cp -R continuity-director ~/.codex/skills/
cp -R storyboard-director ~/.codex/skills/
cp -R xiaobai-fenjing ~/.codex/skills/
```

Then start a new Codex session and invoke:

```text
$ai-director-seedance
$continuity-director
$storyboard-director
$xiaobai-fenjing
```

## Requirements

- Codex desktop or another compatible Codex skill runtime
- Python 3 for the included validation and helper scripts

## Notes

- Keep each skill directory intact. Do not copy only `SKILL.md`; the skills also depend on `references/`, `assets/`, `scripts/`, and `agents/`.
- If you want the skills to appear as explicit workspace skills, add them to your project's `AGENTS.md`.
