# FractalOS UI

Static UX/UI workspace for evolving the FractalOS interface. No core or backend code lives here.

**Start here:** `READING-GUIDE.md` (how to read this repo, glossary, prototype states) and `sessions/2026-09-24.md` (what was done and concluded). For a non-Claude AI assistant, paste the prompt from `READER-PROMPT.md`. All three are in Russian.

- `CLAUDE.md` - brief for the design session (Russian).
- `docs/` - current UI inventory and product model.
- `design-system/` - tokens (current, then evolved).
- `assets/` - icons, mascot, role glyphs.
- `rounds/` - evolution rounds (prototypes, notes, screenshots).
- `PRODUCT.md` - product context for the Impeccable skill (filled from `docs/PRODUCT-MODEL.md`).
- `DECISIONS.md` - decision log: what was chosen, what was rejected, why.
- `sessions/` - session records: requests, work done, conclusions, next steps.
- `tools/shots.mjs` - Playwright screenshots of a round at 1440×900 and 1920×1080: `node tools/shots.mjs rounds/01-<name>`.
- `.claude/skills/` - design skills: Impeccable (Apache-2.0), web-design-guidelines (MIT).
