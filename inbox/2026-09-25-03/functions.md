# Композер — перепись функций живого окна

Снято скриптом переписи по коду живого окна (только чтение), 2026-09-25. Всё это должно остаться в новом композере — место и вид можно менять, функцию нет.

## Сам композер (`app/composer.py`)

| вид | надпись / клавиша | куда ведёт | строка |
|---|---|---|---|
| button | `···` | `self.opt_requested.emit` | `app/composer.py:265` |
| button | `На 8 часов…` | `self.approve_choice.emit` | `app/composer.py:313` |
| button | `Разрешить на 30 минут` | `self.approve_choice.emit` | `app/composer.py:307` |
| button | `нет` | `self.approve_choice.emit` | `app/composer.py:319` |
| button | `повторить найм` | `self.retry_requested.emit` | `app/composer.py:284` |
| button | `спросить` | `self.teacher_ask_interest.emit` | `app/composer.py:233` |
| shortcut | `Down` | `event.accept` | `app/composer.py:100` |
| shortcut | `Escape` | `event.accept` | `app/composer.py:78` |
| shortcut | `Tab` | `event.accept` | `app/composer.py:82` |
| shortcut | `Up` | `event.accept` | `app/composer.py:100` |
| signal | `self.field.textChanged` | `self._on_text` | `app/composer.py:258` |
| signal | `self.menu.itemClicked` | `self._pick_item` | `app/composer.py:217` |
| timer | `180` | `self._ghost_fire` | `app/composer.py:344` |

Сигналы кнопок: `opt_requested` («···» — опции), `approve_choice` (разрешение: 30 минут / 8 часов / нет), `retry_requested` («повторить найм»), `teacher_ask_interest` («спросить»). Маршрут Enter — `ghost` (`ghostroute`, высота 20), обновляется таймером 180 мс из предпросмотра маршрута.

## Слэш-команды (35), меню открывается в композере по `/`

| команда | подсказка |
|---|---|
| `/always-approve` | ОПАСНО: запись без подтверждений до конца сессии |
| `/approve` | разрешить/запретить запись вне песочницы |
| `/btw` | вопрос в сторону — основной разговор не прерывается |
| `/compact` | контекст / уведомление |
| `/compact-mode` | плотная лента |
| `/context` | сколько контекста занято |
| `/copy` | скопировать ответ |
| `/delete` | убрать сессию в архив (с подтверждением) |
| `/diff` | дифф на проверку (Ctrl+4) |
| `/docs` | свежая документация библиотеки |
| `/drop` | убрать прикреплённые файлы (на диске останутся) |
| `/effort` | глубина размышлений: low|medium|high|xhigh |
| `/export` | сохранить разговор в markdown-файл |
| `/feedback` | оставить отзыв |
| `/history` | последний промпт в поле |
| `/how` | как устроено окно |
| `/imagine` | картинка |
| `/memory` | что помнит память |
| `/model` | сменить модель |
| `/multiline` | Enter = перенос, Shift+Enter = отправить |
| `/new` | новая сессия |
| `/pin-taken` | закрепить сработавшее правило |
| `/plan` | режим плана — по желанию, не для каждого сообщения |
| `/proof` | последний снимок метрик |
| `/remember` | записать в память |
| `/rename` | название сессии |
| `/resume` | загрузить сессию |
| `/rewind` | остановить и откатить ленту окна |
| `/routes` | куда уходит сообщение |
| `/session-info` | статус сессии |
| `/skills` | скиллы |
| `/teacher` | отвечает ли учитель памяти |
| `/timestamps` | время у сообщений |
| `/usage` | контекст и расход исполнителя |
| `/why` | почему память дала эти подсказки |
