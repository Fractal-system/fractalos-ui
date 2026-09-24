# ANSWERS-R0 — ответы облачной дизайн-сессии (раунд 0)

Источник — только чтение кода продукта. Всё, чего в коде нет, помечено явно.
Ссылки — вид `app/<файл>.py:<строка>`.

---

## 1. Рельс, строка «Руки:» — сегмент Flash | Grok

### Короткий ответ

Сегмент выбирает **не исполнителя, а только флаг «руки включены»**. И `Flash`, и `Grok` ведут в один и тот же путь: `hire.py` (DSH-headless), на одной и той же модели `deepseek-v4.1-flash:cloud`. Переключатель `hands_on` (галочка роли) — вот что реально гасит найм. Значение `grok` в этом сегменте **не доходит до воркера** ни одной строкой кода.

### Детали

**Что хранится в состоянии.** Две отдельные вещи: провайдер и питание.

- `app/slot_matrix.py:14-15` — контракт ключей: `hands_on bool` («role power; provider only meaningful when True») и `hands flash|grok`.
- `app/slot_matrix.py:108-116` — `hands_on()`: если ключ `hands_on` есть, читается он; иначе легаси-значение `hands == "off"` даёт `False`, всё прочее — `True`.
- `app/slot_matrix.py:127-131` — `hands_provider()`: `off` → `flash`; иначе нормализация до `flash|grok`.
- `app/slot_matrix.py:44-53` — `normalize_provider()` жёстко зажимает в `{flash, grok}`; легаси `partner`, `off`, `none`, `0`, `false` и любой мусор → `flash` (`DEFAULT_PROVIDER`, строка 33).
- `app/roles.py:30` — дефолт `DEFAULTS = {"mouth": "grok", "brain": "grok", "hands": "flash"}`; `app/roles.py:177` — допустимые значения для `hands` ровно `("flash", "grok")`.

**Куда провайдер рук доходит (и куда нет).**

- `app/slot_matrix.py:277-281` — `hands_uses_hire()`: найм разрешён, если `hands_on` и провайдер в `("flash","grok")`. **Оба** проходят одинаково; различие не проверяется.
- `app/window.py:4789-4795` — обработчик найма: `use_hire = slot_matrix_mod.hands_uses_hire(...)`. Провайдер здесь не разветвляется.
- `app/dispatch.py:641-645` — argv найма собирается из `hire.py`, `--cwd`, `--prompt-file`; **флага провайдера/модели в argv нет**. Self-test подтверждает ровно этот набор.
- `app/slot_matrix.py:294-296` — `guide_slot()`: **схлопывает** провайдер до `"off" | "flash"`. То есть даже CPU-наводка (`guide.py`) не различает Flash и Grok у рук.
- `app/window.py:4615`, `app/window.py:4715` — оба вызова `guide_slot` ещё раз затирают `grok` → `flash` (`"slot": "off" if slot_raw == "off" else "flash"`, строки 4627 и 4725).
- `app/guide.py:119-149` — `_CTX_DEFAULTS["slot"] = "flash"`, а `_ctx()` (строка 137) принудительно: `if out["slot"] not in ("flash","off"): out["slot"] = "flash"`. Второй барьер против `grok`.

**Модель и профиль воркера DSH.**

- `runtime/dsh/profiles/hire/cordis.patch.yml:2-5` — `agent-default-model`: `provider: fractal-ollama`, `model: "deepseek-v4.1-flash:cloud"`. Одна константа, без ветки по провайдеру.
- `runtime/dsh/profiles/hire/cordis.patch.yml:1` — комментарий: «Warm hire worker: same tree as headless, no one-shot exit, no web UI».
- `runtime/dsh/profiles/headless/lean.patch.yml:1` — каталог найма по умолчанию (леан): fs + search + pwsh + skill; отключены ralph/workflow/subagent/goal/todo/web/plan-mode.
- `app/dshd.py:37-38` — `CATALOGS = ("slim","lean","full")`, `WORKER_OFFSET = {"slim":1,"lean":2,"full":3}`; `app/dshd.py:63-66` — URL воркера = порт mux + offset. Каталог — **отдельная** ось, не связана с Flash|Grok.

**Выключатель `hands_on` (галочка у «Руки:»).**

- `app/rail.py:635-647` — сегмент `_ProviderSeg("hands", ...)` и переключатель питания `hands_power` в одной строке `_RoleRow`; `app/rail.py:1312-1314` — при `hands_on=False` сегмент провайдера **дизейблится** (`setEnabled(False)`) — визуальная подсказка, что выбор провайдера при выключенных руках ничего не значит.
- `app/window.py:8081-8089` — обработчик питания: `self.state["hands_on"] = bool(on)`, при выключении идёт отдельная ветка.
- `app/window.py:8173-8188` — обработчик провайдера: `hands = normalize_provider(value)`, и **безусловно** `hands_on = True` (строка 8184). То есть клик по сегменту всегда включает руки, даже если они были выключены.
- `app/window.py:8611-8615` — при выключенных руках рельс пишет `«Руки: выкл»`, подпись `«нет POST /job · DSH тёплый · ledger в spend/»` и **выходит** — счётчик вызовов не читается.
- `app/window.py:8621-8627` — при включённых руках: `snap = spend.snapshot(...)`, tip `f"слот Flash · вызовов {snap.get('calls',0)} · ledger spend/ (не на рельсе)"` — **жёстко написано «слот Flash»**, независимо от того, что выбрано в сегменте.
- `app/window.py:1818`, `app/window.py:2107` — в дочерний DSH-процесс уезжает `FRACTALOS_HANDS = str(self.state.get("hands") or "flash")`; `app/mouth.py:180` — то же для рта.
- `app/dshd.py:69-84` — `slot_open()`: читает `FRACTALOS_HANDS`; `off/0/false/no` → закрыто, `flash/on/1/true/yes` → открыто, прочее → смотрит `state.json` на `hands != "off"`. `grok` попадает в «прочее» и трактуется как «открыто», не как отдельный режим.
- `app/dshd.py:504`, `app/dshd.py:984` — в статусе мux наружу торчит `"slot": "flash" if slot_open() else "off"` — **третье место, где grok схлопывается в flash**.
- `app/dshd.py:1214-1222` — self-test ровно этого поведения: `FRACTALOS_HANDS=off → slot_open() is False`, `=flash → True`, `=off + force=True → True`.

### Что это значит для дизайна

1. Сегмент **врёт дважды**: он выглядит как выбор исполнителя, но исполнитель один; и подпись «слот Flash» появляется даже при выбранном Grok. Либо убрать сегмент, либо честно переименовать его в «руки вкл/выкл» (а питание уже есть рядом галочкой — то есть дубль).
2. `hands_on` — единственный рычаг, который что-то меняет. Ему и нужен главный вид (крупно: «руки выключены — найм не запустится»), а провайдеру — второстепенный или никакой.
3. Если в будущем Grok у рук должен значить другую модель/профиль — это сначала надо завести в коде (`slot_matrix`, `dispatch_argv`, `cordis.patch.yml`), а потом уже рисовать в UI. Сейчас рисовать нечего.

---

## 2. Грант: «разово» (allowed-once, ~30 мин) и `/approve <минуты>`

### Короткий ответ

Внутри окна гранта руки пишут **без вопросов на каждое действие**: грант — это таймер, а не очередь подтверждений. Длительность: «разово» — 30 мин, «на сессию» — 8 ч (480 мин, максимум), `/approve <минуты>` — сколько сказано, клампится 1…480. «нет» — снимает грант. В конфиге продукта сейчас `policy = grant` — так и работает. Есть ещё режим `policy = allow` (Soft FS ACL), при котором кнопок гранта нет и запись разрешена сразу; в него код падает, если ключа политики нет или в нём опечатка (см. «Расхождения», п. 5).

### Детали

**Файл гранта и таймер.**

- `app/approve.py:21` — `GRANT = paths.state_dir() / "approve.grant"`.
- `app/approve.py:22-25` — `LEGACY_GRANT` (`runtime/dsh/approve.grant`) закрыт в 131.1: «never read, never deleted»; закомментировано, почему (песочница рук пишет весь cwd, найм мог бы сам себе выписать грант).
- `app/approve.py:26-29` — `DEFAULT_MINUTES = 30`, `MAX_MINUTES = 480`, `ALWAYS_MINUTES = MAX_MINUTES` («на сессию»).
- `app/approve.py:56-66` — `until()` / `active()`: грант = `until > now`; нет файла — нет гранта; мусор в файле грантом не читается.
- `app/approve.py:69-85` — `grant(minutes, note)`: кламп `max(1, min(minutes, 480))`, пишет `{until, minutes, note, at}`. Важно: **повторный вызов переназначает срок от «сейчас», а не складывает** (docstring строки 72-74, self-test строка 187).
- `app/approve.py:88-94` — `revoke()`: удаляет файл; повторный вызов → `False`, не ошибка.

**Что делает каждый ответ (кнопка → тот же API, что слэш).**

- `app/window.py:2517-2550` — `_on_approve_choice(choice)`: `once/yes/разово` → `_owner_approve(str(DEFAULT_MINUTES))`; `always/session/на сессию` → `_owner_approve("always")`; всё прочее → `_owner_approve("off")`. Дальше `rail.set_note(msg)` (строка 2539 — **на экран не выводится, см. §5**), `pane.hide_approve()`, `composer.show_approve(False)` и `pane.append_process(msg, phase="after", tone=...)`.
- `app/window.py:2459-2513` — `_owner_approve(arg)`: `off/no/нет/0/reject/deny` → `revoke()`; `always/yolo/session/навсегда/сессия` → **диалог подтверждения** `_confirm_always_approve()` (иначе строка 2491 `«always-approve: отменено — грант не выдан»`), затем `grant(ALWAYS_MINUTES, note="window /always-approve")`; число → `minutes = int(word)`, иначе `DEFAULT_MINUTES`; `grant(minutes, note="window /approve")`. Возврат всегда — `approvemod.status()`.
- `app/window.py:2438-2439` — `_confirm_always_approve()`: «Owner says yes to an 8h write grant. No/Cancel → do not grant».

**Текст статуса (единственная честная строка про длительность).**

- `app/approve.py:133-145` — `status()`: при активном Soft ACL (и живом пути гранта) → `«Soft FS ACL: запись в продукт разрешена (policy allow) — без кнопок гранта»`; без гранта → `«запись вне песочницы: одобрения нет — кнопки разово / на сессию / нет · грант: <путь>»`; с грантом → `«запись вне песочницы: одобрено ещё ~N мин — /approve off снимает · грант: <путь>»`.

**Как одобряется каждая эскалация — плагин approve в DSH.**

- `runtime/dsh/profiles/hire/node_modules/@fractalos/approve/index.js:31-40` — `ownerGranted()`: читает файл по `FRACTALOS_APPROVE_GRANT`, `Number(data.until) > Date.now()/1000`; «absent, unreadable or malformed: a closed door, never an open one».
- Там же `:42-51` — `decide()`: `allow` → `{outcome:"allowed-once", because:"policy allow"}`; `deny` → `{outcome:"rejected"}`; `ask` → `null` (не заявляет ничего, DSH падает в свой fail-closed); иначе — грант есть → `allowed-once`/`owner grant`, гранта нет → `rejected`/`no owner grant`.
- Там же `:53-61` — на `approval/request` пишет в stderr `dsh: approve <outcome> <tool> (<because>) <reason≤120>` и возвращает исход.
- Там же `:22-24` — ключевое: «`'allowed-once'` is one-shot by construction: a grant covers the single action that asked, nothing after it» — то есть это **вердикт на один запрос**, но запрос приходит от DSH на каждое действие, а плагин отвечает «да» всё время, пока жив таймер.
- `app/dshd.py:165-174` — `approve_env()` ставит оба ключа: `FRACTALOS_APPROVE = approve_policy(cfg)` и `FRACTALOS_APPROVE_GRANT = str(approve.GRANT)`. Комментарий 168-169: «plugin reads the grant file per request, so a grant taken after the worker started still counts — the worker is not restarted for it».

**Политика `[approve].policy`.**

- `app/approve.py:98-121` — `load_policy()`: `allow|grant|deny|ask` из `config.toml`; отсутствие/ошибка → `"allow"`.
- `app/approve.py:124-131` — `soft_acl_on() = (policy == "allow")`, `needs_owner_chrome() = (policy == "grant")`. То есть кнопки разово/на сессию/нет существуют **только** в режиме `grant`.
- `app/dshd.py:160-162` — `approve_policy()`: пусто → `"allow"` («Soft FS ACL staff default (was grant → button UX)»), неизвестное → `"ask"`.
- `app/window.py:2410-2415` — обработчик эскалации: `if not approvemod.needs_owner_chrome(): return` — вне режима `grant` chrome не показывается вообще. Если текст не «стоит одобрения» (`worth_approving` ложно) — подменяется на `«запись вне песочницы: нужен грант — разово / на сессию / нет»` (строка 2414).
- `app/approve.py:32-45` — `_WORTH_KEYS`: `diff, plan, patch, write, sandbox, песочниц, вне песочницы, danger-full, no owner grant, approve rejected, запись вне, allowed-once`. `app/approve.py:148-157` — `worth_approving()`: пусто/шум → `False`.
- `app/approve.py:160-174` — `detect_sandbox_ask()`: cues `no owner grant`, `approve rejected`, `dsh: approve rejected`, `запись вне песочницы: одобрения нет`, `danger-full-access`, `outside the workspace sandbox`, `вне песочницы`. Вызовы: `app/window.py:5218-5220`, `app/window.py:6006`.

**Кто реально рисует chrome.** Кнопки в композере — **мёртвая ветка**:

- `app/chatpane.py:1262-1325` — `ChatPane.show_approve()` строит автопопап в чатлоге: подсказка + три кнопки `разово / на сессию / нет` (`:1283-1292`), стиль `border: 1px solid GOLD`, кнопки «разово/на сессию» — CYAN, «нет» — RED (`:1293-1315`).
- `app/composer.py:472-484` — `Composer.show_approve()`: docstring «Deprecated strip path… Always keep approve_row hidden so panel_height never jumps (fout)». Тело **всегда прячет** `approve_row`.
- `app/window.py:2420-2426` — сначала `pane.show_approve(...)`, композерный вызов оставлен как fail-open no-op.
- `app/composer.py:305-322` — кнопки `approve_once_btn` / `approve_always_btn` / `approve_no_btn` всё ещё создаются, но их ряд (строка 323) остаётся скрытым. Tooltips там: «выдать запись вне песочницы на ~30 мин (allowed-once)», «длинный грант на сессию (~8ч) — /always-approve», «отклонить / снять одобрение».

**CLI.**

- `tools/approve.py:1-33` — `on|grant|yes [минуты]` → `approve.grant(...)`; `off|revoke|no` → `approve.revoke()`; `status` → `approve.status()`. (В файле есть побитая кириллица в двух print — кодировка, но не поведение.)

### Что это значит для дизайна

1. Дизайн «разово = одно действие» **неверен по коду**: разово — это окно 30 минут, внутри которого каждое действие одобряется молча. Честная формулировка: «одобрено на 30 минут», а не «на один раз».
2. При дефолтном `policy = allow` весь этот UI **не существует** — кнопок нет, запись разрешена. Экран гранта нужно рисовать как редкий, «военный» режим, а не как постоянный элемент.
3. Живой chrome — автопопап в чатлоге (`chatpane.py`), а не полоса композера. Если дизайн предполагает кнопки под полем ввода — это надо согласовать с кодом, сейчас их там нет.
4. «нет» — это не «отклонить этот запрос», а `revoke()`: снятие гранта целиком. Подпись должна это отражать.

---

## 3. Строка ghost под доком («вердикт CPU»)

### Короткий ответ

Ghost показывает **предсказание роутера до нажатия Enter**: кем будет отвечено и уйдёт ли ход в найм/мозг/разведку. Текст — русский label из `preview_label()`. Показывается **только в режиме plan-mode** и **только пока поле непустое** (дебаунс 180 мс). По умолчанию, вне plan-mode, строка пустая и скрыта.

### Детали

**Кто устанавливает текст.**

- `app/composer.py:327-344` — `self.ghost = QLabel("", hud_host)`, `objectName("ghostroute")`, `NoFocus`, `WA_TransparentForMouseEvents`, стиль: фон `theme.BG`, цвет `theme.FG_DIM`, шрифт `FONT_MONO` 11px, паддинг `0 12px`; строка 344 — `self.ghost.hide()`.
- `app/composer.py:325-326` — комментарий: «Ghost line: CPU verdict. HUD sibling (not a layout slot) so showing it cannot grow the panel or yank the chat seam (fout)».
- `app/composer.py:151-154` — сигнал `ghost_requested = Signal(str)`.
- `app/composer.py:351-354` — `_ghost_timer`, single-shot, интервал `GHOST_DEBOUNCE_MS`; `app/composer.py:40` — `GHOST_DEBOUNCE_MS = 180`.
- `app/composer.py:521-530` — `_ghost_fire()`: пустой текст → `show_ghost("")`; иначе `ghost_requested.emit(text)`. `app/composer.py:532-535` — `_ghost_schedule()`: запускает таймер. Вызов — `app/composer.py:648` (на ввод текста). Гашение — `app/composer.py:829-830`, `:846-847`, `:858-859`.
- `app/composer.py:496-519` — `show_ghost(label)`: пустой текст → скрыть; иначе `setText`, `show()`, и при первом показе — `resized.emit()`. `app/composer.py:517-519` — `ghost_text()`: «Test/inspection hook; the send path ignores it».
- `app/window.py:854` — `self.composer.ghost_requested.connect(self._on_ghost)`.
- `app/window.py:4741-4769` — `_on_ghost(text)`: **`if not bool((self.state or {}).get("plan_mode")): show_ghost(""); return`** — вне plan-mode ghost всегда пуст. Затем `got = guidemod.preview(text, self._ghost_ctx(), self.cfg)` и `show_ghost(str(got.get("label") or ""))`.
- `app/window.py:4697-4737` — `_ghost_ctx()`: ctx без `two_writers` («so the ghost may show a hire the Enter then refuses. That is the honest direction»); `slot` берётся из `guide_slot` и снова затирается в `flash|off` (строка 4725).
- `app/window.py:3174` — второй вызывающий: `self.composer.show_ghost(line if on else "")` (переключение plan-mode).
- Глубина HUD: `app/window.py:6274-6334` — ghost и process dock живут **над** последними строками чата, над стабильным 1px швом (`_hud`, строка 6334).

**Откуда берётся текст.**

- `app/guide.py:675-720` — `preview(text, ctx, cfg)`: docstring «Live CPU verdict for the composer ghost line. BEFORE send, no side effects… nothing launched, nothing written and no model contacted». Внутри — те же два шага, что на Enter: `guide()` → `plan_turn()`; возвращает всегда `kind, fit, axis, label, id, needle`. `app/guide.py:691-694` — живая ось мозга поверх пожелания: свежий down-маркер деградирует мозг, даже если state говорит grok.
- `app/guide.py:652-672` — `preview_label(plan, slot)`: формирует саму строку (см. примеры ниже).

**Примеры строк (дословно, `app/guide.py:620-635`, `:660-672`).**

- `"болтовня"` — `PREVIEW_TALK_LABEL`, дефолт для `talk` и `think`.
- `"-> мозг"` — `PREVIEW_BRAIN_LABEL`, для `brain` и `brain_then_hire`.
- `"-> разведка"` — `PREVIEW_RESEARCH_LABEL`, для `research` и `research_then_hire`.
- `"-> отказ"` — `PREVIEW_REFUSE_LABEL`, для `refuse`.
- `"-> руки выкл"` — `PREVIEW_HANDS_OFF_LABEL`, приоритетно, когда ход умирает именно из-за выключенных рук (строки 638-649: слот `off` + kind `hire`/`brain_then_hire`, либо `refuse` с id `slot_off_volume`).
- `f"-> найм (fit {fit:.2f})"` — для `hire`/`brain_then_hire` (строка 667). Это **единственная** метка с числом; комментарий 624-625: «Only the hire label carries a fit; the rest are decisions, not scores, and a number next to them would invent certainty».

**Когда показывается / прячется.**

- Показывается: plan-mode включён **и** текст непустой **и** метка непустая.
- Прячется: plan-mode выключен (`window.py:4748-4752`); поле очищено (`composer.py:525-528`); ход завершён/сброшен (`composer.py:829`, `:846`, `:858`).

### Что это значит для дизайна

1. Это **самый недооценённый элемент** окна: честное предсказание поведения на Enter, до траты токенов. Сейчас он спрятан за plan-mode и живёт мелким моношрифтом 11px в углу.
2. Формат `-> найм (fit 0.72)` — машинный. Дизайн может дать человеческое: «пойдёт в найм · уверенность 0.72 — 30 мин работы рук».
3. Метки — уже готовый словарь из 6 состояний. Это основа для цветовой семантики (спокойно / уйдёт в работу / отказ), и менять словарь нужно синхронно с `guide.py`.

---

## 4. Память: метрика «сколько fractalmem помнит по проекту»

### Короткий ответ

Есть **две разные честные метрики**, и их легко перепутать. (а) `offer_count` — **сколько подсказок слой предложил на этот ход** (0…3, `k=3`), показывается строкой в чатлоге. (б) `atoms_total` — **сколько атомов запинено по проекту**; он приходит из Bridge, но на экран **не выводится** (только хранится в снапшоте). Метрики «сколько всего помнит» в коде нет.

### Детали

**Метрика (а): подсказки на ход — то, что реально видно.**

- `app/memory.py:387-422` — `offer_count(cfg, cwd, text)`: docstring «How many rules the layer would offer for this turn's text. 0 on any failure… Same `offer(..., point="prompt")` call memamp.brief_prefix makes, so the chip and the brief cannot disagree». Внутри: `project_slug` → `tags_from_prompt` → `situation` → `offer(store, sit, project, point="prompt", k=3)` → `len(rows)`. Значит **максимум 3**, и это потолок, а не объём памяти.
- `app/window.py:3688-3719` — `_start_mem_chip(text)`: считает на **отдельном потоке** (`name="memchip"`), с монотонным `_mem_chip_seq` против гонки; emit только при `n > 0`. Комментарий 3692-3693: «0 offers (layer off, DB locked, sandbox) draws nothing at all».
- `app/window.py:3721-3733` — `_on_mem_chip(n)`: `word = mem_offer_word(count)`, затем `pane.append_note(f"память: {count} {word} — /why покажет причины")`. Docstring: «One dim line next to the turn… Never a turn».
- `app/window.py:500-516` — `mem_offer_word(n)`: русская плюрализация (1 подсказка / 2 подсказки / 5 подсказок), с отдельной обработкой тинейджеров (комментарий 502-503: «the teens are the trap»).
- `app/window.py:3636` — вызов `_start_mem_chip(text)` на ход.

**Метрика (б): атомы по проекту — в снапшоте есть, на экран не идёт.**

- `app/memory.py:196-213` — `raw_snap`: `"atoms": format_atoms(atoms_raw)[:ATOMS_KEEP]` и `"atoms_total": int((overview.get("atoms") or {}).get("pinned") or len(atoms_raw))`. То есть `atoms_total` — число запиненных атомов, с фолбэком на длину списка.
- `app/memory.py:170-176` — источники: `bridge.atoms("pinned", ATOMS_KEEP)` и `bridge.overview()`.
- `app/memory.py:21-22` — `ATOMS_N = 4` («visible floor for the atom panel»), `ATOMS_KEEP = 40` (строки скролла).
- `app/memory.py:19-20` — `JOURNAL_N = 8`, `JOURNAL_KEEP = 48`.
- `app/memory.py:165-167` — `snapshot_now()`: «The slow Bridge read. Only the worker thread calls this».
- `app/memory.py:236-253` — `snapshot()`: last-good снапшот, обновление вне GUI-потока; при пустом кэше и без локальных пожеланий → `{"ok": False, "error": "слой: ещё пуст"}`.
- **`atoms_total` не читается нигде в UI** (grep по `atoms_total` даёт только `memory.py:210`, `:293`, `:341` — три места внутри самого модуля). То есть метрика «сколько помнит по проекту» собирается, но владельцу не показывается.

**Статус слоя — то, что показывается вместо неё.**

- `app/memory.py:12-17` — `TITLES = {"layer": "Слой", "serving": "Подача", "learning": "Обучение", "hot": "Горячая"}`.
- `app/memory.py:199-206` — снапшот отдаёт `switches` ровно по этим четырём именам с `on: bool`.
- `app/memory.py:41-53` — `verdict_of(states)`: `layer off` → `"asleep"`; ни подачи, ни обучения → `"asleep"`; нет подачи → `"learning"`; нет обучения → `"watching"`; иначе → `"idle"`.
- `app/rail.py:1396-1404` — `refresh()`: по `snap["switches"]` дёргает `w.show_state(row["on"])` и `set_mood(snap["mood"])`. При `snap["ok"] == False` — просто `return` (нет слоя — нет строк).
- `app/memory.py:256-318` — `set_switch()`: пишет в Bridge; если Bridge мёртв — держит локальное пожелание `_LOCAL_SWITCHES`, патчит кэш, чтобы тумблеры в рельсе не отскакивали. `app/memory.py:321-357` — `_merge_local()` накладывает эти пожелания.
- `app/memory.py:361-378` — `set_atom(cfg, atom_id, accept=)` → `bridge.accept/retire`; «The write goes to the same layer the hook path writes; no second truth is created».

**`/why`.**

- `app/window.py:3735-3760` — `_slash_why()`: берёт текст последнего хода (`_turn_mem_text`); нет хода → rail-note `«/why: нет хода — команда объясняет причины подсказок памяти»`; нет модуля → `«/why: память недоступна (модуль не поднят)»`; пусто → `pane.append_note("память: why пусто — слой молчит или недоступен")` и rail-note `«память: why пусто»`; иначе — `«память · why:»` и до **40** строк по 200 символов.
- `app/memory.py:425-461` — `why_text(cfg, cwd, text)`: запускает `fractalmem.py why <text> --cwd <cwd>`, timeout 30 с. Fail-open: пустая строка, и главное — `if got.returncode != 0 or "Traceback (most recent call last)" in out: return ""`. Комментарий 430-431: «A traceback is NOT output… the owner must not get a stack trace in the chatlog for asking why».
- `app/window.py:3912` — ещё один rail-note: `"mem · " + " · ".join(notes[:2])`.

### Что это значит для дизайна

1. Честная метрика для «сколько помнит по проекту» **уже собирается** — `atoms_total` (запиненные атомы) + `atoms` (список). Показать её можно без нового кода на стороне памяти; сейчас это работа только для UI.
2. `offer_count` нельзя выдавать за «объём памяти»: это 0…3 подсказки на один ход, потолок жёсткий (`k=3`). Подпись должна говорить «подсказок на этот ход», а не «правил в памяти».
3. Статус слоя — четыре тумблера (`Слой/Подача/Обучение/Горячая`) плюс вердикт-настроение (`asleep/learning/watching/idle`). Это готовый, но «внутренний» язык. Для хозяина по PRODUCT «работает / нет / сколько помнит» он переводится в одно слово + одно число.
4. `/why` — единственное место, где видно *причины*. Это тяжёлый, до 40 строк, вывод; в дизайне ему место в разворачиваемой панели, не в ленте подряд.

---

## 5. `Rail.set_note` — 20–30 типичных текстов и пометка тона

### Короткий ответ

`set_note` **ничего не выводит на экран**. Он сохраняет строку в поле `self._note` и всё. Никакой виджет её не рисует. То есть **~118 вызовов статуса по всему `window.py` пропадают молча** — это самый большой разрыв «код ↔ экран» в окне.

### Детали

- `app/rail.py:1378-1380` — единственная реализация:
  `def set_note(self, text: str) -> None:` → `"""Status note API for window. No journal list on rail anymore."""` → `self._note = text or ""`.
- `app/rail.py:597` — инициализация `self._note = ""`.
- Проверено grep’ом по `rail.py`: `_note` встречается ровно в этих трёх местах (`:597`, `:1378`, `:1380`). **Ни одного чтения** `self._note` для `setText`, paint или tooltip нет. Все `QLabel` рельса (`spirit`, `session_now`, `nav_path`, `hint`, ячейки `_cell`, строки `_head`/`_line`) заполняются независимо от `_note`.
- Значит каждый вызов ниже — запись в никуда. Строки-дубликаты уходят в `pane.append_note`/`append_process` в части мест, но далеко не во всех.

Ниже — 28 типичных текстов, `инфо / предупреждение / сбой` (по смыслу текста, не по коду — в коде тона нет вообще).

**Сбой / явная ошибка**
1. `app/window.py:1806` — `f"дом окна {kind} не поднялся — агент стартует без настроек"` — запуск.
2. `app/window.py:2077` — `"TUI не поднялся: терминальная страница не собрана (FRACTALOS_TERM=1)"` — запуск TUI.
3. `app/window.py:2129` — `f"TUI не поднялся: {exc}"` — исключение при запуске TUI.
4. `app/window.py:2961` — `f"/copy: не записал {dest} — {exc}"` — слэш-команда, запись файла.
5. `app/window.py:2978` — `f"/export: не записал — {exc}"` — экспорт ленты.
6. `app/window.py:3149` — `f"/feedback: не записал — {exc}"` — запись обратной связи.
7. `app/window.py:3779` — `f"btw не поднялся: {exc}"` — побочный вопрос.
8. `app/window.py:3832` — `"btw не поднялся"` — побочный вопрос, без деталей.
9. `app/window.py:4020` — `"Flash рот не поднялся"` — старт Flash-рта.
10. `app/window.py:4377` — `"ACP не поднялся — та же сессия, Enter ≠ /new"` — старт ACP-рта (тут же важная оговорка для хозяина).
11. `app/window.py:4506` — `"DSH рот не поднялся"` — старт DSH-рта.
12. `app/window.py:7157` — `f"pin-taken: {exc}"` — операция памяти.
13. `app/window.py:7163` — `f"pin-taken: {got.get('error') or 'fail'}"` — операция памяти.
14. `app/window.py:7273` — `f"удаление не удалось: {exc}"` — удаление сессии.
15. `app/window.py:7283` — `f"удаление: {err}"` — удаление сессии.
16. `app/window.py:8476` / `app/window.py:8507` — `"canvas: не открылась"` — открытие LabCanvas.
17. `app/window.py:3742` — `"/why: память недоступна (модуль не поднят)"` — память.

**Предупреждение / отказ в действии**
18. `app/window.py:3620`, `:4004`, `:4359`, `:4500` — `"ход ещё идёт — Stop / Esc"` — четыре разных точки входа, один текст.
19. `app/window.py:3827` — `"btw ещё отвечает — подожди"` — занятость.
20. `app/window.py:4801` — `"руки выкл"` — найм не запущен (дублируется в `pane.append_note("руки выкл — слот найма не запущен")`, строка 4802).
21. `app/window.py:4798` — `"руки=Учитель — без hire"` — легаси-ветка «руки есть, но не найм».
22. `app/window.py:3385` — `"/rewind: откатывать нечего"` — слэш-команда.
23. `app/window.py:3358` — `"ход пуст — копировать нечего"` — копирование.
24. `app/window.py:2913` — `"нечего копировать — ходов ассистента нет"` — копирование.
25. `app/window.py:3158` — `"/history: промптов нет"` — история промптов.
26. `app/window.py:3740` — `"/why: нет хода — команда объясняет причины подсказок памяти"` — память.
27. `app/window.py:3024` — `"/rename <название>"` — неверный вызов команды.
28. `app/window.py:3196` — `f"думалка: {want} не знаю — {'|'.join(EFFORTS)}"` — неверный аргумент.

**Инфо / спокойный статус**
29. `app/window.py:1748` — `"рот flash · чат :11435 · поднимаю…"` — старт.
30. `app/window.py:1867` — `f"рот {kind} · ACP · поднимаю агента…"` — старт.
31. `app/window.py:1925` — `"рот flash · DSH · поднимаю…"` — старт.
32. `app/window.py:2301` — `"рот закрыт"` — завершение.
33. `app/window.py:2433` — `"approve: разово / на сессию / нет"` — хром гранта.
34. `app/window.py:3151` — `"принято"` — отзыв записан.
35. `app/window.py:3162` — `"последний промпт в поле"` — возврат из истории.
36. `app/window.py:5671` — `"работа снята"` — остановка найма.
37. `app/window.py:4871` — `f"параллельный найм · lane {lane}"` — параллельный найм.
38. `app/window.py:5600-5606` — `"найм: слот свободен → из очереди"` (+ возможный `qleft`) — очередь найма.
39. `app/window.py:4847` / `:5582` — `qnote` из `dispatchmod.hire_queue_status()` — «найм: пул занят (max_parallel_hire=N) — в очереди».
40. `app/window.py:6786` — `"Учитель вкл"` / `"Учитель выкл"` — переключатель рамки.
41. `app/window.py:7187` — `f"pin-taken: {len(pinned)} pinned"` — память, единственная **с числом**.
42. `app/window.py:7299` — `f"сессия {sid[:8]}… удалена (archive)"` — удаление сессии.
43. `app/window.py:3395` — `"лента окна откачена · KV Grok нет — /clear новая сессия"` — rewind.
44. `app/window.py:8571-8577` — `rolesmod.axis_note(wish=..., live=..., down=...)` — деградация оси мозга (текст собирается в `app/roles.py:58`).
45. `app/window.py:8160` — `"рот Grok ⇒ мозг Grok, одна сессия"` — зависимость слотов.
46. `app/window.py:3437` — `"ctx7 · руки, не рот"` — подсказка.
47. `app/window.py:3912` — `"mem · " + " · ".join(notes[:2])` — память, до двух заметок.
48. `app/window.py:6119` — `note or "ход… · Stop / Esc"` — ход пошёл.
49. `app/window.py:7352` / `:7356` — `live` / `line` — состояние оси.
50. `app/window.py:8067` — `str(claim.get("rail_line") or "")` — строка из `slot_matrix.enter_claim()` (см. `app/slot_matrix.py:392`).
51. `app/dshmouth.py:141` — `"DSH: воркер холодный — грею, первый ход до ~40 с"` — приходит через `on_note` (`app/window.py:1062`).
52. `app/dshmouth.py:172` — `f"DSH: первый ответ за {s:.0f} с — воркер прогревался"` — то же.
53. `app/approve.py:141` — `"Soft FS ACL: запись в продукт разрешена (policy allow) — без кнопок гранта"` — статус гранта.
54. `app/approve.py:143` — `"запись вне песочницы: одобрения нет — кнопки разово / на сессию / нет · грант: <путь>"`.
55. `app/approve.py:145` — `f"запись вне песочницы: одобрено ещё ~{left} мин — /approve off снимает · грант: <путь>"`.

Итого: **55 различных текстов** (118 вызовов), из них примерно 17 сбойных, 11 предупреждающих, остальные инфо. Тона в коде нет — классификация выше сделана по смыслу текста.

### Что это значит для дизайна

1. Строка здоровья, о которой говорит PRODUCT, **уже написана в коде** — но её никто не рисует. Это дёшево включить: один виджет, читающий `_note`. Проблема не в отсутствии данных, а в отсутствии вывода.
2. Тексты неоднородны: есть технический жаргон (`ctx7`, `lane`, `pin-taken`, `KV Grok`, `FRACTALOS_TERM=1`) и есть готовые человеческие фразы (`«руки выкл — слот найма не запущен»`). Для строки здоровья нужен слой перевода; сам словарь уже готов.
3. Тона нет вообще — это надо заводить в коде (`set_note(text, tone=...)`), иначе дизайн будет раскрашивать строки эвристикой по подстрокам.
4. `set_note` перетирается: это **одна** строка, а не журнал. Последний вызов побеждает, и предыдущее состояние теряется. Для «видеть, что всё работает» одной строки мало — нужен список или последнее-на-категорию.

---

## 6. LabCanvas («инфраструктура») — что показывает

### Короткий ответ

LabCanvas — это **архитектурная карта системы**, а не монитор здоровья. Он рисует 12 узлов в 3 колонках и 6 рядах (поверхность → слоты → исполнение → порты → память → корень) и 13 связей между ними. **Живое состояние есть только у портов** (4 узла: up/down по HTTP-пробе). Слоты, память и корень нарисованы статически, их состояние не читается.

### Детали

**Кто открывает.**

- `app/window.py:8468-8509` — `_on_lab_canvas(name)`: импорт `LabCanvas`, резолв пути через `projectsmod.lab_registry(cfg)`, отказ для `metrprod` (строка 8494-8496: `"metrprod — объект разработки, не lab-среда"`), затем `dlg.exec()` (модальный диалог).
- `app/window.py:8463-8465` — `_on_infra_popup()`: «Unified: infra lives on Lab Canvas (no separate hop)» → просто вызывает `_on_lab_popup()`.
- `app/window.py:8511-8513` — `_on_lab_popup()`: канвас для текущего lab-продукта.
- `app/rail.py:586-587` — сигналы рельса `project_chosen` и `canvas_requested(str)` — рельс открывает канвас на конкретный продукт.
- `app/labcanvas.py:652-659` — сам `LabCanvas(QDialog)` с параметрами `cfg`, `project_name`, `project_path`.

**Узлы (12), `app/labcanvas.py:172-249`.**

| id | имя | kind | lane | источник состояния |
|---|---|---|---|---|
| `window` | поверхность | hub | 0 | нет |
| `mouth` | рот | slot | 1 | нет (sub — константа «всегда on · Flash\|Grok») |
| `brain` | мозг | slot | 1 | нет |
| `hands` | руки | slot | 1 | нет |
| `partner` | Учитель | ext | 2 | нет (`partner_on = "сессия"`, строка 167 — литерал) |
| `flash` | flash closer | port | 2 | **да** — `_probe(flash)` |
| `hire` | hire | flow | 2 | нет (sub — константа «slim\|lean\|full · EXPECT») |
| `dsh` | dsh mux | port | 3 | **да** — `_probe(dsh)` |
| `ollama` | ollama | port | 3 | **да** — `_probe(ollama)` |
| `jobport` | POST /job | port | 3 | **да** — `_probe(dsh)` (тот же проб, что у `dsh`) |
| `mem` | fractalmem | mem | 4 | нет |
| `root` | корень | hub | 5 | нет (`root_path` — путь, строка 168) |

- `app/labcanvas.py:161-168` — `_arch_fractalos(cfg, path)`: порты берутся из `cfg["ports"]` с дефолтами `ollama 127.0.0.1:11434`, `flash :11435`, `dsh :11436`.
- `app/labcanvas.py:207`, `:220`, `:227`, `:234` — у портов есть поле `"up": _probe(...) == "up"`.
- `app/labcanvas.py:170-171` — комментарий-легенда: «Columns: 0 рот-ветка · 1 мозг-ветка · 2 руки-ветка. Lanes: 0 поверхность · 1 слоты · 2 исполнение · 3 порты · 4 память · 5 корень».
- `app/labcanvas.py:87` — текст-справка по `hands`: «Зачем: вынести изменения в мир (файлы, команды) отдельно от речи рта… По сути: Flash/Grok → hire.py. Объём всегда найм».
- `app/labcanvas.py:125` — справка по связи `(hands, hire)`: «Зачем: наём с EXPECT даёт приёмку, а не «модель что-то написала». По сути: руки → hire.py».

**Связи (13), дерево, `app/labcanvas.py:251-266`** — «TREE edges only (drawn). One clear parent per child where possible»:

`window→mouth` «ход», `window→brain` «пак», `window→hands` «дело», `mouth→partner` «chrome», `brain→flash` «closer», `hands→hire` «job», `partner→dsh` «рамка», `flash→ollama` «модель», `hire→jobport` «hire/v1», `dsh→mem` «след», `ollama→mem` «atoms», `jobport→mem` «tape», `mem→root` «полка».

- Подписи-объяснения к связям: `app/labcanvas.py:268-279` (словарь `how` по метке связи).
- В словаре есть объяснения и для меток, которых в дереве **нет**: `"гейт"`, `"native"`, `"Flash-путь"` (строки 272, 273, 276) — мёртвые записи, след прежних вариантов графа.

**Цвета и состояния, `app/labcanvas.py:587-625`.**

- `kind == "hub"` → рамка `theme.GOLD`, заливка `rgba(226,168,74,55)` (строка 592).
- `kind in {"mem","layer"}` → рамка `theme.CYAN`, заливка `rgba(9,245,229,28)` (строка 594).
- `kind == "port"` → рамка `theme.GREEN` если `up`, иначе `theme.FG_DIM` (мятный/зелёный = живо, тусклый = лежит); заливка `rgb(36,36,40)` (строки 596-598). **Единственный реально динамический цвет.**
- `kind == "slot"` → рамка `theme.GOLD`, заливка `rgb(40,36,28)` (строка 600).
- `kind == "gate"` → рамка `theme.FG_DIM`, заливка `rgb(32,32,36)` (строка 602). В текущей архитектуре узлов `gate` нет — мёртвая ветка.
- `else` (в т.ч. `ext`, `flow`) → рамка `theme.CYAN_DIM`, заливка `rgb(36,36,40)` (строка 604).
- Наведение: `border = theme.CYAN`, толщина пера `2.1` против `1.4` (строки 605-607).
- Текст узла: имя — `theme.GOLD` для hub/slot, иначе `theme.FG` (строка 610); подпись `sub` — `theme.FG_DIM`, обрезается до 40 символов (строки 613-618); тизер `how` — мелким 8pt, `theme.CYAN_DIM` при наведении, иначе `FG_FAINT`, обрезается до 48 (строки 619-625).
- Нижняя полоса-подсказка: `rgb(20,20,22,235)`, высота 30px, текст `theme.FG_DIM`, обрезка до 140 (строки 627-631).
- Шрифты: `Segoe UI` 10 / 11 bold / 8, с фолбэком на `theme.FONT_UI` (строки 581-586).
- `app/labcanvas.py:87`, `:125`, `:194`, `:275` — тексты `how`/справок; отрисовка их — строки 619-625.

**Пробы портов.**

- `app/dshd.py:177-187` — `_probe(url, timeout=0.4)`: URL → `/ready` (или `/status`), таймаут 0.4 с, при любой сетевой/JSON-ошибке → `None`. То есть «down» может значить и «медленно», и «нет JSON».

### Что это значит для дизайна

1. LabCanvas — **не** экран здоровья, а карта состава с четырьмя живыми лампочками. Хозяину по PRODUCT нужно «видеть, что всё работает»: сейчас 8 из 12 узлов нарисованы без состояния, включая три слота (рот/мозг/руки) — самое важное для него.
2. Готовый визуальный язык уже есть и его стоит переиспользовать: `GOLD`+прозрачная заливка = hub, `CYAN` = память, зелёный/тусклый = порт жив/лежит, `GOLD` = слот. Мёртвые цвета (`gate`) и мёртвые подписи связей можно не переносить.
3. Узлы несут полезную нагрузку в трёх слоях текста: имя → `sub` → `how` (тизер при наведении). Это готовый паттерн, но `sub` у слотов сейчас — статичные константы, а не факты. Их надо оживить данными (`slot_matrix.hands_on/hands_provider`), а не рисовать заново.
4. `_probe` с таймаутом 0.4 с — источник нестабильных «down». В дизайне деградации нужно третье состояние («не ответил вовремя»), иначе владелец будет видеть ложные падения.

---

## Что это значит для дизайна (сводно)

1. **Три места, где UI обещает выбор, которого нет:** сегмент «Руки: Flash|Grok» (§1), подпись «слот Flash» при выбранном Grok (§1), и «разово = один раз» вместо «30 минут» (§2).
2. **Два готовых, но не выведенных источника правды:** `set_note` (55 текстов, ~118 вызовов, ноль пикселей — §5) и `atoms_total` (число запиненных атомов — §4). Оба дают хозяину пункты 1 и 2 его приоритетов почти без нового кода.
3. **Ghost — недооценённый актив** (§3): единственное место в окне, где поведение предсказано до траты токенов. Спрятан за plan-mode и мелким шрифтом.
4. **LabCanvas нужно доводить до карты здоровья** (§6): язык цветов есть, состояния есть только у 4 портов из 12 узлов.

## Расхождения код ↔ экран/доки

1. **«Руки: Flash | Grok» — выбор без последствий.** `hands_provider()` возвращает `flash|grok` (`app/slot_matrix.py:127`), но `guide_slot()` схлопывает до `flash|off` (`app/slot_matrix.py:294`), `window.py` затирает ещё раз (`app/window.py:4627`, `:4725`), статус mux — `"flash" if slot_open()` (`app/dshd.py:504`, `:984`), tip рельса — литерал «слот Flash» (`app/window.py:8623`), а argv найма вообще не несёт провайдера (`app/dispatch.py:641-645`). Модель зашита константой `deepseek-v4.1-flash:cloud` (`runtime/dsh/profiles/hire/cordis.patch.yml:5`). **Экран обещает выбор исполнителя, код его не имеет.**
2. **«разово» ≠ разовое действие.** Tooltip «на ~30 мин (allowed-once)» (`app/composer.py:307`) и слово `allowed-once` в плагине (`approve/index.js:45`) читаются как «один раз», но грант — таймер 30 минут (`app/approve.py:26`, `:69-85`), внутри которого ответчик одобряет каждое обращение, пока `until > now` (`approve/index.js:48-50`).
3. **Кнопки гранта в композере — мёртвая ветка.** `Composer.show_approve()` всегда прячет ряд (`app/composer.py:472-484`), а `window.py:2424` помечает вызов как «no-op strip; kept fail-open». Живой chrome — автопопап в чатлоге (`app/chatpane.py:1262-1325`). Если доки/CURRENT-UI описывают кнопки под композером — они описывают несуществующее.
4. **`Rail.set_note` не выводит ничего.** `app/rail.py:1378-1380` пишет `self._note`, и это поле не читает ни один виджет (все три вхождения `_note` в `rail.py` — запись). Все ~118 вызовов статуса, включая сообщения об отказах старта рта и найма, на экран не попадают.
5. **Политика гранта: работает `grant`, но код падает в `allow` при сбое конфига.** В конфиге продукта стоит `[approve] policy = "grant"` — так система работает сейчас: без гранта хозяина запись вне песочницы отклоняется, с грантом — одобряется (проверено пробой 2026-09-24). Но если ключа нет или в нём опечатка, `load_policy()` возвращает `allow` (`app/approve.py:107`, `:121`), `dshd.approve_policy()` — тоже `allow` (`app/dshd.py:161`), а `window.py:2411` в этом режиме выходит до показа chrome: запись разрешена, кнопок нет. Для дизайна: грант — нормальный шаг; при этом экран должен честно показывать действующую политику (grant / allow / deny), а не угадывать.
6. **Ghost виден только в plan-mode.** `app/window.py:4748-4753` гасит строку при `not state["plan_mode"]`. Комментарий `app/composer.py:325` описывает ghost как постоянный HUD-элемент; фактически это атрибут plan-mode.
7. **`atoms_total` собирается, но не показывается.** `app/memory.py:210` его вычисляет; grep даёт только три вхождения, все внутри `memory.py`. Ни рельс, ни чип памяти его не читают.
8. **LabCanvas: 8 из 12 узлов без состояния.** Живые пробы есть только у `flash`, `dsh`, `ollama`, `jobport` (`app/labcanvas.py:207`, `:220`, `:227`, `:234`); слоты рот/мозг/руки, память, корень и `hire` нарисованы константами. Плюс мёртвые ветки: цвет `gate` (`:601-602`) и объяснения связей `гейт`/`native`/`Flash-путь` (`:272-276`) для рёбер, которых в графе нет.
9. **`hands_on` — единственный рычаг, но он дублируется.** Питание роли есть и галочкой (`app/rail.py:635-647`, `hands_power`), и побочно — кликом по сегменту провайдера, который всегда ставит `hands_on = True` (`app/window.py:8184`). Экран показывает два способа включить одно и то же.

---

PIN: hands_provider(flash, grok): сегмент «Руки» выбирает только вкл/выкл — оба провайдера ведут в один hire.py на одной модели, grok схлопывается в flash.
PIN: rail.set_note(silent, 118): строка статуса пишется в поле, которое не читает ни один виджет — 55 текстов здоровья готовы, но невидимы.
PIN: atoms_total(hidden, honest): число запиненных атомов уже считается в memory.py, но на экран не выведено — это готовая метрика «сколько помнит по проекту».
