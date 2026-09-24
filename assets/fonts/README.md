# fonts — шрифты для прототипов

Прототипы должны открываться двойным кликом без сети, поэтому шрифты лежат здесь.

| Файлы | Шрифт | Зачем | Лицензия | Источник |
|---|---|---|---|---|
| `cascadia-mono-{cyrillic,latin}-{400,600}-normal.woff2` | Cascadia Mono (Microsoft) | пути, код, время, трасса — тот же шрифт, что в окне FractalOS | SIL OFL 1.1, `LICENSE-cascadia-mono.txt` | npm `@fontsource/cascadia-mono@5.3.0` |
| `open-sans-{cyrillic,latin}-{400,600}-normal.woff2` | Open Sans | замена Segoe UI **только для снимков** в облаке: у Segoe UI проприетарная лицензия, класть его нельзя | SIL OFL 1.1, `LICENSE-open-sans.txt` | npm `@fontsource/open-sans@5.3.0` |

В прототипах стек такой: `"Segoe UI Variable Text", "Segoe UI", "Open Sans", …`.
На Windows хозяина сработает настоящий Segoe UI, а Open Sans подхватится только там,
где Segoe UI нет, например в облачном Chromium при съёмке.

В Qt Cascadia Mono надёжнее встроить в ресурсы приложения (`QFontDatabase::addApplicationFont`):
она ставится с Windows Terminal и есть не на каждой машине.
