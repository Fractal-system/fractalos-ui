# Current window — screenshots (round 0)

Taken 2026-09-24 ~08:30 MSK from the running FractalOS window (Qt, Windows, 2560×1440 screen).
Captured with `PrintWindow`: window pixels only, popups drawn over the main window at their real offsets.

**Nothing was sent.** The composer was not touched: no Enter, no `···` menu, no slash menu, no grant buttons.
The rail switches (`[Слой]` … `[Горячая память]`, Рот/Мозг/Руки segments) were not clicked either, because clicking them changes state.
The chat text is from a setup-phase session (`ds`). FractalOS is not in real use yet, so do not read it as a usage example.

| file | what | size |
|---|---|---|
| `01-main.png` | default window: chatlog, rail, composer | 1509×1151 |
| `02-sessions.png` | «Сессии» popup over the window | 1509×1151 |
| `03-labcanvas-fractalos.png` | «лаборатория → fractalos [инфраструктура]», LabCanvas over the window | 1509×1151 |
| `04-labcanvas-node.png` | LabCanvas alone, node «руки» selected (detail text on the left) | 1320×860 |
| `05-labcanvas-fractalmem.png` | «лаборатория → fractalmem [инфраструктура]» | 1320×860 |
| `06-maximized-2560.png` | the same window maximized | 2560×1392 |

## What the shots show (for design)

- **Title bar** (`01`): `FractalOS · Сессии · Новая · Журнал`. «Журнал» is a gold label, and the memory strip next to it is empty in this state.
- **Rail** (`01`), from top to bottom:
  - three role rows (Рот / Мозг / Руки with Flash|Grok, the underline marks the active choice);
  - the `fractalmem` header with four bracketed switches;
  - the `hygiene apply −0.0MB` log panel: timestamped hygiene lines, cut off by `…`, plus an «обновлено …» footer;
  - «лаборатория» with two products, each with a `[инфраструктура]` link.

  There is no health line: `set_note` texts do not reach the screen, see `ANSWERS-R0.md` Q5.
- **Chatlog** (`01`): the last hire result block. It has a green «Готово — подтверждено» line, the stdout line, a ✓ receipt path and «изменённых файлов в ленте нет».
- **Composer** (`01`): `+` attach, a placeholder with the hint «Enter — Grok · «найми …» — поручить исполнителю», `···` options and the teal send glyph. The mascot sits bottom-left above it.
- **Sessions** (`02`): a small modal with the list of sessions and two buttons, «закрыть текущую» and «готово». The list has one row: time and name.
- **LabCanvas** (`03`–`05`) is a static map of layers. The left column holds reference text: layers, nodes, the tree, links not on the map, variants. On the right are node cards in lanes.
  - Live state: only the port nodes probe their address and print `· up` (`app/labcanvas.py:35`, `:205-234`).
  - The fractalmem map (`05`) has no live state at all.
  - **Stale text:** the node «Учитель» still says «OpenCode · … · не слот» and «TeacherBar + btw (модель OpenCode/OpenRouter)» (`app/labcanvas.py:199-200`). Since wave 129 the Teacher is the CPU rules (CLOSE-HIRE), and OpenCode serve is off.
- **Maximized** (`06`): the layout does not use the width. The chat column keeps its left alignment, the rail stays narrow on the far right, and about 2/3 of the screen is empty. The composer stretches across the whole width.

## Not captured

- Composer states: ghost «вердикт CPU», the grant buttons, the `···` menu and the slash menu. They need the composer, which is off-limits for now.
- Tooltips: most did not appear under automated hover. The rail role tooltips, verbatim from `app/rail.py:620-640`:
  - «Рот:» — «С кем вы говорите — всегда включён»;
  - Рот segment — «С кем вы говорите: Grok — основной, Flash — запасной и дешевле»;
  - «Мозг:» — «Планировщик сложных задач: включить или выключить»;
  - Мозг segment — «Кто планирует сложные задачи. При Grok-рте — сам Grok»;
  - «Руки:» — «Исполнитель для объёмной работы с кодом. Выкл — всё делает рот сам»;
  - Руки segment — «Кто исполняет объёмную работу (по слову «найми …»)».

  **Shadowed:** hovering «Flash» over the Руки segment showed just «Flash». `apply_availability` gives every provider button its own tooltip, the short name (`app/rail.py:354-356`), so the segment's explanatory tooltip never shows over the buttons. An unavailable provider shows its reason instead. Other tooltips are in `docs/CURRENT-UI.md`.
- A running hire or turn: there are no live runs in the setup phase.
