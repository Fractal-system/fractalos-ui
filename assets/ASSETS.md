# assets — что реально использует UI FractalOS

Скопировано из `C:\FractalOS\assets` **только то, что читает живой UI**
(Qt-окно). Служебные исходники, генераты и старые версии не копировались.
Подпапки сохранены как в источнике. Пути указаны от корня `C:\FractalOS`
(как в коде), размеры — в пикселях исходного файла.

Правило: в окне **нет** иконок-as-emoji и Unicode-графем в роли иконок:
глифы рисуются кодом (`app/icons.py`), картинки — только штампы/маскот/иконка окна.

---

## 1. Иконка продукта

| Файл | Размер, px | Где используется | Источник |
|---|---|---|---|
| `icon.png` | 1024×1024 | иконка окна и трея; масштабируется в `16, 22, 32, 48`; фолбэк тела мини-фрактала | `app/icons.py:14-21` (`product_icon`), `app/window.py:703-711`, `app/tray.py:18-25`, `app/fractalmini.py:107` |
| `fractal.ico` | многоразмерный ICO (113 КБ) | добавляется в `QIcon` продукта; фолбэк иконки окна и трея | `app/icons.py:15,23`, `app/window.py:707`, `app/tray.py:22` |

> Оба — **единственные** ассеты в корне `assets/`, которые читает UI. Остальные
> файлы корня (`field.png` ниже — исключение, он в корне) не используются.

## 2. Корень: фон сплеша

| Файл | Размер, px | Где используется | Источник |
|---|---|---|---|
| `field.png` | 1280×720 | фоновая картинка сплеша `Gate`: масштабируется `KeepAspectRatioByExpanding` под размер окна, рисуется с `opacity = SPLASH_FIELD (0.82)`, якорь `(0.54, 0.50)`; снизу — градиент BG | `app/chrome.py:212`, `app/chrome.py:449-468` |

## 3. Маскот (дух) — ядро

| Файл | Размер, px | Где используется | Источник |
|---|---|---|---|
| `mascot/spirit.png` | 1024×1024 | 1) тело мини-фрактала над композером (`FractalMini`), 2) первый кандидат `spirit_pixmap` для сплеша/рельса | `app/fractalmini.py:103-104`, `app/icons.py:27-37` |
| `mascot/spirit-hi.png` | 1024×1024 | второй кандидат `spirit_pixmap` (фолбэк, если нет `spirit.png`) | `app/icons.py:29-31` |
| `mascot/mini-body.png` | 1024×1024 | фолбэк тела мини-фрактала, если нет `spirit.png` | `app/fractalmini.py:104` |
| `mascot/mini-eyes.png` | 1024×1024 | глаза мини-фрактала (анимация моргания: squash к горизонту глаз) | `app/fractalmini.py:105`, `app/fractalmini.py:179-191` |
| `mascot/loop-src.png` | 1024×1024 | статичный кадр духа на рельсе, если WebP-петля недоступна | `app/rail.py:1089-1098` |
| `mascot/idle.png` | 1280×720 | статичный кадр сплеша, если WebP недоступен | `app/chrome.py:378-388` |
| `mascot/idle.webp` | анимированный WebP | живой дух сплеша (`QMovie`, размер `MASCOT_GATE = 380`) | `app/chrome.py:361-377` |
| `mascot/idle-loop.webp` | анимированный WebP | живая петля духа на рельсе (`QMovie`, `MASCOT_RAIL = 220`) | `app/rail.py:1074-1088` |

## 3a. Мини-маскот чатлога (`minimascot.py`, размеры 16…34px, по умолчанию 25)

Читается, когда `SHOW_MASCOT=True` (сейчас **выключен**, `app/chatpane.py:782-797`).

| Файл | Размер, px | Где используется | Источник |
|---|---|---|---|
| `mascot/idle-loop-f0.png` | 1024×1024 (57 КБ) | первый кадр микропетли мини-маскота (thinking / hire / ask / done) | `app/minimascot.py:39-44`, `app/minimascot.py:100-107` |
| `mascot/idle-loop-mid.png` | 1024×1024 | средний кадр микропетли | там же |
| `mascot/idle-loop-fN.png` | 1024×1024 | последний кадр микропетли | там же |
| `mascot/atom.png` | 1024×1024 | фолбэк-кадр `load_pixmap`, когда `idle-loop-*` недоступны | `app/minimascot.py:83-86` |

> **Важно:** дух в окне **выключен** флагом `theme.SHOW_MASCOT = False`
> (`app/theme.py:119`). При выключенном флаге `chrome.py` и `rail.py`
> **не читают** WebP/PNG маскота вовсе: сплеш и рельс их не грузят.
> Единственное живое использование тела/глаз — `FractalMini` над композером
> (он не зависит от флага).

## 4. Роли: штампы (44px-колонка рельса)

Каталог `mascot/roles/`. Выбор файла — `role_pixmap(kind, size)`
(`app/icons.py:121-168`): ищет `{kind}-{size}.png`, затем по убыванию
`56, 44, 40, 32, 24, 22, 18, 14, 12`; если ни одного нет — рисует глиф кодом.

| Файл | Размер, px | Роль | Источник |
|---|---|---|---|
| `mascot/roles/mouth-44.png` | 44×30 | штамп рта в рельсе (по умолчанию `RAIL_GLYPH_PX = 44`) | `app/rail.py:376-386`, `app/icons.py:134-146` |
| `mascot/roles/brain-44.png` | 44×44 | штамп мозга в рельсе | там же |
| `mascot/roles/hands-44.png` | 44×44 | штамп рук в рельсе | там же |
| `mascot/roles/mouth-256.png` | 256×177 | крупный штамп рта (кэш для больших размеров) | `app/icons.py:134` |
| `mascot/roles/brain-256.png` | 256×256 | крупный штамп мозга | там же |
| `mascot/roles/hands-256.png` | 256×256 | крупный штамп рук | там же |
| `mascot/roles/mouth-56.png` | 56×39 | промежуточный размер | там же |
| `mascot/roles/brain-56.png` | 56×56 | промежуточный размер | там же |
| `mascot/roles/hands-56.png` | 56×56 | промежуточный размер | там же |
| `mascot/roles/mouth-40.png` | 40×28 | промежуточный размер | там же |
| `mascot/roles/brain-40.png` | 40×40 | промежуточный размер | там же |
| `mascot/roles/hands-40.png` | 40×40 | промежуточный размер | там же |
| `mascot/roles/mouth-32.png` | 32×22 | промежуточный размер | там же |
| `mascot/roles/brain-32.png` | 32×32 | промежуточный размер | там же |
| `mascot/roles/hands-32.png` | 32×32 | промежуточный размер | там же |
| `mascot/roles/mouth-24.png` | 24×17 | промежуточный размер | там же |
| `mascot/roles/brain-24.png` | 24×24 | промежуточный размер | там же |
| `mascot/roles/hands-24.png` | 24×24 | промежуточный размер | там же |
| `mascot/roles/mouth-22.png` | 22×15 | промежуточный размер | там же |
| `mascot/roles/brain-22.png` | 22×22 | промежуточный размер | там же |
| `mascot/roles/hands-22.png` | 22×22 | промежуточный размер | там же |
| `mascot/roles/mouth-18.png` | 18×12 | промежуточный размер | там же |
| `mascot/roles/brain-18.png` | 18×18 | промежуточный размер | там же |
| `mascot/roles/hands-18.png` | 18×18 | промежуточный размер | там же |
| `mascot/roles/mouth-14.png` | 14×10 | промежуточный размер | там же |
| `mascot/roles/brain-14.png` | 14×14 | промежуточный размер | там же |
| `mascot/roles/hands-14.png` | 14×14 | промежуточный размер | там же |
| `mascot/roles/mouth-12.png` | 12×8 | минимальный размер | там же |
| `mascot/roles/brain-12.png` | 12×12 | минимальный размер | там же |
| `mascot/roles/hands-12.png` | 12×12 | минимальный размер | там же |
| `mascot/roles/mouth-cta-256.png` | 256×177 | **глиф кнопки отправки** в композере (`GlyphButton "send"`, заливка CYAN, вырез `DestinationOut`); масштабируется по ширине квадрата 40px | `app/icons.py:108-118` (`cta_mouth_pixmap`), `app/icons.py:227-241` |
| — `mouth-256-prev.png` | 256×177 | **не копировался:** в UI не читается (прежняя версия штампа) | — |

Итого скопировано штампов: **31** PNG (по 10 размеров × 3 роли + `mouth-cta-256`).

## 5. Партнёр / учитель

| Файл | Размер, px | Где используется | Источник |
|---|---|---|---|
| `partner/pebble.png` | 132×116 | `HEAD_FULL` бара учителя (полный портрет; API `head_asset_paths`, сейчас не рисуется — бар скрыт) | `app/teacherbar.py:34`, `app/teacherbar.py:295-296` |
| `partner/pebble-40.png` | 40×40 | `HEAD_24` бара учителя (мелкий портрет, сейчас не рисуется — бар скрыт wave130) | `app/teacherbar.py:33`, `app/teacherbar.py:295-296` |
| `mascot/partner/head.png` | 4687 Б (px 24) | партнёрская голова в мини-маскоте чатлога (`minimascot.py`, `prefer=`), когда `SHOW_MASCOT=True` | `app/minimascot.py:56`, `app/minimascot.py:74-92` |
| `mascot/partner/head-22.png` | 995 Б | мелкий вариант головы партнёра для мини-маскота | там же |

> Бар учителя (`PartnerBar`) скрыт флагом `WAVE130_CHROME_OFF`
> (`app/teacherbar.py:12`), поэтому портреты `partner/` и `mascot/partner/`
> в живом окне сейчас **не видны**; оставлены как часть поверхности роли.
> Мини-маскот чатлога тоже выключен (`SHOW_MASCOT=False`,
> `app/chatpane.py:782-797`), но его кадры читаются тем же кодом при включении.

## 6. Не копировалось (осознанно)

| Что | Почему |
|---|---|
| `field-orig.png`, `icon-pre-R03.png` | старые версии, в коде не читаются |
| `mascot/idle-pre-R03.png`, `spirit-pre-R03.png`, `spirit-hi-pre-R03.png` | версии до R03, не читаются |
| `mascot/spirit-icon-source.png`, `spirit-cyan-violet.png` | исходники/варианты |
| `mascot/imagine-f0.png`, `imagine-fN.png`, `imagine-mid.png` | кадры Imagine, в окне не читаются |
| `mascot/idle-loop.webp` источник-дубликат `loop-*` | см. выше нужные файлы |
| `mascot/roles/_gen_*.jpg`, `_ref.png`, `_sheet.jpg`, `_vot.jpg`, `_mouth_gg.png`, `_gen_mouth.jpg` | референсы и генер-исходники штампов |
| `mascot/roles/mouth-256-prev.png` | прежняя версия, не читается |
| `mascot/chatlog/active.png`, `mascot/chatlog/idle.png` | каталог `mascot/chatlog/*` в коде не читается (маска чатлога живёт в `minimascot.py` и берёт файлы из `mascot/`) |
| `partner/pebble-18/22/24/32/36.png`, `partner/pebble-active.webp`, `pebble-idle.webp`, `pebble-anim/*` | не читаются живым UI |
| `mascot/idle-loop-f0.png` дубликат `spirit-*` | см. раздел 3a — нужные кадры скопированы |
| `web/*` (`terminal.html`, `xterm.js`, `xterm.css`, `xterm-addon-fit.js`, `terminal.js`) | мёртвая ветка `FRACTALOS_TERM=1`; окно стартует без неё (`app/window.py:246-258`) |
| `fractalos.ico`, `fractal-mark.ico` | дубликаты `fractal.ico`; в коде читается только `fractal.ico` |

## 7. Итог копирования

```
assets/
├── icon.png                     1024×1024   иконка окна/трея
├── fractal.ico                  ICO         иконка окна/трея (фолбэк)
├── field.png                    1280×720    фон сплеша
├── mascot/
│   ├── spirit.png               1024×1024   тело мини-фрактала
│   ├── spirit-hi.png            1024×1024   фолбэк духа
│   ├── mini-body.png            1024×1024   фолбэк тела
│   ├── mini-eyes.png            1024×1024   глаза мини-фрактала
│   ├── loop-src.png             1024×1024   кадр духа рельса
│   ├── idle.png                 1280×720    кадр сплеша
│   ├── idle.webp                WebP        петля сплеша (движение)
│   ├── idle-loop.webp           WebP        петля рельса (движение)
│   ├── idle-loop-f0.png         1024×1024   кадр мини-маскота
│   ├── idle-loop-mid.png        1024×1024   кадр мини-маскота
│   ├── idle-loop-fN.png         1024×1024   кадр мини-маскота
│   ├── atom.png                 1024×1024   фолбэк-кадр мини-маскота
│   ├── roles/                   12…256 px   штампы ролей (31 файл)
│   └── partner/                 head, head-22
└── partner/                     pebble.png, pebble-40.png
```

Всего: **50 файлов** (3 в корне, 12 в `mascot/`, 31 в `mascot/roles/`,
2 в `mascot/partner/`, 2 в `partner/`). Плюс этот файл-опись `ASSETS.md`.
