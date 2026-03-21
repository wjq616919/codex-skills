# Codex Skills

This repository packages two custom Codex skills:

- `ai-director-seedance`
- `storyboard-director`

## Included Skills

### `ai-director-seedance`
Use when you want an AI director workflow oriented toward Seedance/Jimeng-style video prompt generation:

- script understanding
- director decisions
- pacing and timing checks
- lighting and sound design
- continuity and object-state control

### `storyboard-director`
Use when you want a professional storyboard workflow:

- script review before shot planning
- shot-by-shot storyboard writing
- expression design
- action timing validation
- object state control
- storyboard-style prompt output

## Install

Copy the skill folders into your local Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R ai-director-seedance ~/.codex/skills/
cp -R storyboard-director ~/.codex/skills/
```

Then start a new Codex session and invoke:

```text
$ai-director-seedance
$storyboard-director
```

## Requirements

- Codex desktop or another compatible Codex skill runtime
- Python 3 for the included validation and helper scripts

## Notes

- Keep each skill directory intact. Do not copy only `SKILL.md`; the skills also depend on `references/`, `assets/`, `scripts/`, and `agents/`.
- If you want the skills to appear as explicit workspace skills, add them to your project's `AGENTS.md`.
