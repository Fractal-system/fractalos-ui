"""Docked mouth. Opaque strip is only as tall as what it holds. Field grows to FIELD_MAX. Slash menu lives in the leftover."""

from __future__ import annotations

from . import theme

from PySide6.QtCore import QMimeData, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QKeyEvent, QPainter, QTextCursor, QWheelEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import clip, slash, theme
from .icons import GlyphButton
from .tiles import ChipRow

try:
    from .teacherbar import PartnerBar
except Exception:  # pragma: no cover
    PartnerBar = None  # type: ignore[misc, assignment]

try:
    from .processdock import ProcessDock
except ImportError:  # pragma: no cover
    ProcessDock = None  # type: ignore


SLASH_ROW = 18
SLASH_MAX = 4
#: Ghost recompute delay. One timer, restarted per keystroke: typing never waits
#: on the router, and a burst of keys costs one recompute, not one per key.
GHOST_DEBOUNCE_MS = 180
#: The route line under the field (wave 149): one fixed row, never hidden.
ROUTE_H = 20


class Field(QPlainTextEdit):
    send_requested = Signal()
    stop_requested = Signal()
    nav_requested = Signal(int)
    complete_requested = Signal()
    files_pasted = Signal(list)
    #: ↑ on an EMPTY field, slash menu hidden: cycle prompt history. The window
    #: owns the list (`session_dir/prompts.jsonl`); the field only carries the
    #: keystroke, so the composer stays a widget with no session knowledge.
    history_requested = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("")
        self.setTabChangesFocus(False)
        self.setFixedHeight(theme.FIELD_MIN)
        self.setUndoRedoEnabled(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameStyle(0)
        self.document().setDocumentMargin(0)
        self.setFont(QFont(theme.FONT_UI, 13))
        # `/multiline`: when on, Enter inserts a newline and Shift+Enter sends —
        # the inverse of the default. Persisted by the window as state.chat_multiline.
        self._multiline = False

    def set_multiline(self, on: bool) -> None:
        self._multiline = bool(on)

    def multiline(self) -> bool:
        return bool(self._multiline)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            event.accept()
            self.stop_requested.emit()
            return
        if event.key() == Qt.Key_Tab:
            event.accept()
            self.complete_requested.emit()
            return
        ret = event.key() in (Qt.Key_Return, Qt.Key_Enter)
        shift = bool(event.modifiers() & Qt.ShiftModifier)
        if ret and self._multiline:
            # Inverted: Enter breaks the line, Shift+Enter is the send.
            if not shift:
                super().keyPressEvent(event)
                return
            event.accept()
            self.send_requested.emit()
            return
        if ret and not shift:
            event.accept()
            self.send_requested.emit()
            return
        if event.key() in (Qt.Key_Up, Qt.Key_Down) and self.toPlainText().strip() == "":
            # Grok Build's `↑` on an empty prompt: walk the history. `↓` past
            # the newest clears the field, so the owner can escape the walk.
            step = -1 if event.key() == Qt.Key_Up else 1
            event.accept()
            self.history_requested.emit(step)
            return
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            event.accept()
            self.nav_requested.emit(-1 if event.key() == Qt.Key_Up else 1)
            return
        super().keyPressEvent(event)

    def canInsertFromMimeData(self, source: QMimeData) -> bool:
        return clip.has_attach(source) or super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source: QMimeData) -> None:
        files = clip.paths_from_mime(source)
        if files:
            self.files_pasted.emit(files)
            return
        super().insertFromMimeData(source)

    def fit_height(self) -> bool:
        """Grow the field to its text, clamped to theme.FIELD_MAX. True if it changed.

        The field is fixed-height because the composer is hand-placed (no layout
        owns the panel): it reports the exact height it wants and nothing is
        left over. The wanted height is block count * line spacing (the document
        is laid out at the viewport width, so wrapped lines already count as
        blocks); past FIELD_MAX the text scrolls inside the field.
        """
        blocks = max(1, self.document().blockCount())
        line = self.fontMetrics().lineSpacing()
        wanted = blocks * line + 10
        h = max(theme.FIELD_MIN, min(theme.FIELD_MAX, wanted))
        if h == self.height():
            return False
        self.setFixedHeight(h)
        return True


class Composer(QWidget):
    send_requested = Signal(str)
    stop_requested = Signal()
    files_dropped = Signal(list)
    attach_clicked = Signal()
    file_removed = Signal(str)
    focused = Signal()
    wheel_requested = Signal(int)
    resized = Signal()
    retry_requested = Signal()
    #: Owner grant chrome: once / session-always / no. Window writes grant API.
    approve_choice = Signal(str)
    #: A debounced ghost recompute is due. The window answers with preview() —
    #: the composer never imports the router, so the field stays a widget.
    ghost_requested = Signal(str)
    #: ↑/↓ on an empty field with the slash menu hidden: prompt history walk.
    history_requested = Signal(int)
    #: Aside frame send (slash /btw, overflow). The composer no longer has a btw button;
    #: «спросить» above the send CTA opens the frame. Empty string means just open.
    btw_requested = Signal(str)
    #: Sticky Teacher bar (chrome only; FractalOS Teacher lane).
    teacher_ask_interest = Signal()  # спросить
    teacher_wake = Signal()  # compat; «позвать» retired
    #: Composer ··· options (effort, plan mode). Window owns the menu.
    opt_requested = Signal()
    #: Live process text for the chatlog. Dock stays hidden.
    process_live = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("composer")
        self.setAttribute(Qt.WA_StyledBackground, True)

        # WA_OpaquePaintEvent is deliberately NOT set: the panel sits over the

        # chat stack, and an opaque attribute made Qt skip the repaint of the

        # uncovered strip under it, so the panel edge and the partner bar

        # flickered against the transcript on every show/hide and re-place.

        self.setAutoFillBackground(True)
        self.setAcceptDrops(True)

        col = QVBoxLayout(self)
        col.setContentsMargins(theme.SPACE_MD, theme.SPACE_SM - 2, theme.SPACE_MD, theme.SPACE_SM)
        col.setSpacing(theme.SPACE_SM - 2)

        # Sticky Teacher presence bar (above field). Visible when Teacher ON.
        self.partner_bar = PartnerBar(self) if PartnerBar is not None else None
        if self.partner_bar is not None:
            self.partner_bar.hide()
            col.addWidget(self.partner_bar, 0)

        # Process line is a HUD sibling of this panel (parent = mouth), never a
        # layout slot: counting it in panel_height made the chat seam jump, and
        # omitting a 110px dock let it paint through the last transcript lines.
        hud_host = self.parent() or self
        self.process_dock = ProcessDock(hud_host) if ProcessDock is not None else None
        if self.process_dock is not None:
            try:
                if hasattr(self.process_dock, "retain_open_requested"):
                    self.process_dock.retain_open_requested.connect(self._on_retain_open)
                if hasattr(self.process_dock, "retain_command"):
                    self.process_dock.retain_command.connect(self._on_retain_command)
            except Exception:
                pass


        self.menu = QListWidget(self)
        self.menu.setObjectName("slashmenu")
        self.menu.setFocusPolicy(Qt.NoFocus)
        self.menu.setSelectionMode(QAbstractItemView.SingleSelection)
        self.menu.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.menu.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.menu.itemClicked.connect(self._pick_item)
        self.menu.hide()
        col.addWidget(self.menu)

        self.chips = ChipRow(self)
        self.chips.file_removed.connect(self.file_removed)
        self.chips.hide()
        col.addWidget(self.chips, 0)

        # «спросить» sits above the send CTA, same right edge — not on the field row.
        self.ask_row = QWidget(self)
        self.ask_row.setObjectName("partnerAskRow")
        ask_l = QHBoxLayout(self.ask_row)
        ask_l.setContentsMargins(0, 0, 0, 0)
        ask_l.setSpacing(0)
        ask_l.addStretch(1)
        self.ask_btn = QPushButton("спросить")
        self.ask_btn.setObjectName("partnerAsk")
        self.ask_btn.setCursor(Qt.PointingHandCursor)
        self.ask_btn.setFocusPolicy(Qt.NoFocus)
        self.ask_btn.setFixedHeight(int(getattr(theme, "ASK_H", 22)))
        self.ask_btn.setToolTip("спросить учителя (ZDR). Рот это не видит.")
        self.ask_btn.clicked.connect(self.teacher_ask_interest.emit)
        ask_l.addWidget(self.ask_btn, 0, Qt.AlignRight | Qt.AlignVCenter)
        self.ask_row.hide()
        col.addWidget(self.ask_row, 0)

        row = QHBoxLayout()
        row.setSpacing(theme.SPACE_SM)
        row.setContentsMargins(0, 0, 0, 0)

        self.add_btn = GlyphButton("plus")
        self.add_btn.setToolTip("прикрепить файл к сессии")
        self.add_btn.clicked.connect(self.attach_clicked.emit)
        row.addWidget(self.add_btn, 0, Qt.AlignVCenter)

        self.field = Field()
        self.field.send_requested.connect(self._emit_send)
        self.field.stop_requested.connect(self._on_escape)
        self.field.nav_requested.connect(self._nav_menu)
        self.field.complete_requested.connect(self._complete_menu)
        self.field.textChanged.connect(self._on_text)
        self.field.files_pasted.connect(self.files_dropped.emit)
        # `↑` on an empty field must not fight the open slash menu: the menu owns
        # the arrows while it is visible (`_nav_menu`), the window owns them after.
        self.field.history_requested.connect(self._on_history)
        row.addWidget(self.field, 1, Qt.AlignVCenter)

        self.opt_btn = QPushButton("···")
        self.opt_btn.setObjectName("optbtn")
        self.opt_btn.setToolTip("опции: думалка, режим плана")
        self.opt_btn.setCursor(Qt.PointingHandCursor)
        self.opt_btn.setFocusPolicy(Qt.NoFocus)
        self.opt_btn.setFixedHeight(theme.BTN)
        self.opt_btn.clicked.connect(self.opt_requested.emit)
        row.addWidget(self.opt_btn, 0, Qt.AlignVCenter)

        self.send_btn = GlyphButton("send", filled=True)
        self.send_btn.setToolTip("отправить в рот · Enter")
        self.send_btn.clicked.connect(self._on_send_or_stop)
        self._turn_busy = False
        self._send_is_stop = True
        self._enter_tip = "отправить в рот · Enter"
        row.addWidget(self.send_btn, 0, Qt.AlignVCenter)

        # Retry appears only when the last hire's *work* did not finish.
        # A broken closer on green Done is not retryable — hidden by default.
        self.retry_btn = QPushButton("повторить найм")
        self.retry_btn.setObjectName("retryhire")
        self.retry_btn.setToolTip("только если работа не дошла: тот же бриф, тот же hire.py")
        self.retry_btn.setCursor(Qt.PointingHandCursor)
        self.retry_btn.hide()
        self.retry_btn.clicked.connect(self.retry_requested.emit)
        row.addWidget(self.retry_btn, 0, Qt.AlignVCenter)
        col.addLayout(row)

        # Approve strip: once / session-always / no. Same chrome family as retry.
        # Hidden by default — northern path: window reveals only when a real
        # write/diff is waiting on the owner grant (not journal noise).
        self._approve_reason = ""
        self.approve_row = QWidget(self)
        self.approve_row.setObjectName("approverow")
        self.approve_row.hide()
        arow = QHBoxLayout(self.approve_row)
        arow.setContentsMargins(0, 0, 0, 0)
        arow.setSpacing(6)
        self.approve_hint = QLabel("", self.approve_row)
        self.approve_hint.setObjectName("approvehint")
        self.approve_hint.setWordWrap(False)
        arow.addWidget(self.approve_hint, 1)
        self.approve_once_btn = QPushButton("Разрешить на 30 минут")
        self.approve_once_btn.setObjectName("approveonce")
        self.approve_once_btn.setToolTip("выдать запись вне песочницы на ~30 мин (allowed-once)")
        self.approve_once_btn.setCursor(Qt.PointingHandCursor)
        self.approve_once_btn.clicked.connect(lambda: self.approve_choice.emit("once"))
        arow.addWidget(self.approve_once_btn, 0)
        self.approve_always_btn = QPushButton("На 8 часов…")
        self.approve_always_btn.setObjectName("approvealways")
        self.approve_always_btn.setToolTip("длинный грант на 8 часов — спросит ещё раз, «Нет» по умолчанию")
        self.approve_always_btn.setCursor(Qt.PointingHandCursor)
        self.approve_always_btn.clicked.connect(lambda: self.approve_choice.emit("always"))
        arow.addWidget(self.approve_always_btn, 0)
        self.approve_no_btn = QPushButton("нет")
        self.approve_no_btn.setObjectName("approveno")
        self.approve_no_btn.setToolTip("отклонить / снять одобрение")
        self.approve_no_btn.setCursor(Qt.PointingHandCursor)
        self.approve_no_btn.clicked.connect(lambda: self.approve_choice.emit("no"))
        arow.addWidget(self.approve_no_btn, 0)
        col.addWidget(self.approve_row)

        # Route line (wave 149, cloud round 1 §5.3): where Enter goes, always under
        # the field. A fixed-height layout row that is never hidden, so it is counted
        # once in content_height and showing a new verdict cannot move the seam.
        self.ghost = QLabel("", self)
        self.ghost.setObjectName("ghostroute")
        self.ghost.setFocusPolicy(Qt.NoFocus)
        self.ghost.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.ghost.setFixedHeight(ROUTE_H)
        self.ghost.setTextFormat(Qt.TextFormat.PlainText)
        self.ghost.setProperty("tone", "info")
        col.addWidget(self.ghost)

        self._ghost_text = ""
        # Prompt history walk (Grok Build `↑` on an empty prompt). The window
        # owns prompts.jsonl and seeds this list via set_history().
        self._history: list[str] = []
        self._history_at = 0
        self._ghost_timer = QTimer(self)
        self._ghost_timer.setSingleShot(True)
        self._ghost_timer.setInterval(GHOST_DEBOUNCE_MS)
        self._ghost_timer.timeout.connect(self._ghost_fire)

        self.setStyleSheet(
            f"""
            QWidget#composer {{
                background: {theme.BG};
                border: none;
            }}
            QListWidget#slashmenu {{
                background: {theme.BG};
                color: {theme.FG};
                border: 1px solid {theme.LINE_SOFT};
                border-radius: 4px;
                font-family: "{theme.FONT_MONO}";
                font-size: {theme.CHROME_FONT_PT}px;
                outline: none;
            }}
            QListWidget#slashmenu::item {{
                padding: 2px 8px;
                color: {theme.FG_DIM};
            }}
            QListWidget#slashmenu::item:selected {{
                background: {theme.CYAN_SELECT};
                color: {theme.CYAN};
            }}
            QPlainTextEdit {{
                background: {theme.BG};
                color: {theme.FG};
                border: none;
                border-bottom: 1px solid {theme.LINE_SOFT};
                border-radius: 0px;
                padding: 6px 8px;
                selection-background-color: {theme.CYAN_SELECT};
                font-family: "{theme.FONT_MONO}";
                font-size: {theme.CHAT_FONT_PT}px;
            }}
            QPlainTextEdit:focus {{ border-bottom-color: {theme.CYAN_DIM}; }}
            QPushButton#optbtn {{
                background: transparent;
                color: {theme.FG_DIM};
                border: none;
                padding: 0 6px;
                font-family: "{theme.FONT_MONO}";
                font-size: 13px;
            }}
            QPushButton#optbtn:hover {{ color: {theme.CYAN}; }}
            QWidget#partnerAskRow {{ background: transparent; }}
            QPushButton#partnerAsk {{
                background: transparent;
                color: {theme.PARTNER_DIM};
                border: none;
                padding: 0 4px;
                min-height: {getattr(theme, "ASK_H", 22)}px;
                max-height: {getattr(theme, "ASK_H", 22)}px;
                font-family: "{theme.FONT_UI}";
                font-size: {theme.CHROME_FONT_PT}px;
            }}
            QPushButton#partnerAsk:hover {{
                color: {theme.PARTNER};
                background: {theme.PARTNER_WASH};
            }}
            QPushButton#retryhire {{
                background: {theme.BG_PANEL};
                color: {theme.RED};
                border: 1px solid {theme.RED};
                border-radius: {theme.RADIUS}px;
                padding: 3px 10px;
                font-family: "{theme.FONT_UI}";
                font-size: 11px;
            }}
            QPushButton#retryhire:hover {{ background: {theme.RED}; color: {theme.BG}; }}
            QWidget#approverow {{ background: transparent; }}
            QLabel#approvehint {{
                background: transparent;
                color: {theme.FG_DIM};
                font-family: "{theme.FONT_MONO}";
                font-size: 11px;
            }}
            QPushButton#approveonce, QPushButton#approvealways {{
                background: {theme.BG_PANEL};
                color: {theme.CYAN};
                border: 1px solid {theme.CYAN_DIM};
                border-radius: {theme.RADIUS}px;
                padding: 3px 10px;
                font-family: "{theme.FONT_UI}";
                font-size: 11px;
            }}
            QPushButton#approveonce:hover, QPushButton#approvealways:hover {{
                background: {theme.CYAN}; color: {theme.BG};
            }}
            QPushButton#approveno {{
                background: {theme.BG_PANEL};
                color: {theme.FG_DIM};
                border: 1px solid {theme.LINE};
                border-radius: {theme.RADIUS}px;
                padding: 3px 10px;
                font-family: "{theme.FONT_UI}";
                font-size: 11px;
            }}
            QPushButton#approveno:hover {{ background: {theme.BG_RAISED}; color: {theme.FG}; border-color: {theme.LINE}; }}
            QLabel#ghostroute {{
                background: transparent;
                color: {theme.FG_DIM};
                font-family: "{theme.FONT_MONO}";
                font-size: 12px;
                padding: 1px 2px 0 2px;
            }}
            QLabel#ghostroute[tone="warn"] {{ color: {theme.GOLD}; }}
            QLabel#ghostroute[tone="fail"] {{ color: {theme.RED}; }}
            QLabel {{ background: transparent; }}
            """
        )

    def show_retry(self, on: bool) -> None:
        """Reveal retry only when the last hire is actually retryable."""
        try:
            self.retry_btn.setVisible(bool(on))
        except Exception:
            pass

    def show_approve(self, on: bool, reason: str = "") -> None:
        """Deprecated strip path: Soft FS ACL + chatlog popup own chrome.

        Always keep approve_row hidden so panel_height never jumps (fout).
        Window should call pane.show_approve; this stays as a safe no-op.
        """
        try:
            self._approve_reason = str(reason or "").strip() if on else ""
            if not self.approve_row.isHidden():
                self.approve_row.hide()
                self.resized.emit()
        except Exception:
            pass

    def approve_visible(self) -> bool:
        try:
            # isHidden (not isVisible): parents may be off-screen in tests/startup.
            return not bool(self.approve_row.isHidden())
        except Exception:
            return False

    def approve_reason(self) -> str:
        return str(getattr(self, "_approve_reason", "") or "")

    def show_ghost(self, label: str, tone: str = "info") -> None:
        """Render where Enter goes under the field. Tone: info | warn | fail.

        Display only: no read-back, no auto-send. Never raises into a keystroke.
        The row keeps its height when the label is empty, so nothing jumps.
        """
        try:
            text = str(label or "").strip()
            self._ghost_text = text
            self.ghost.setText(text)
            want = tone if tone in ("warn", "fail") else "info"
            if self.ghost.property("tone") != want:
                self.ghost.setProperty("tone", want)
                self.ghost.style().unpolish(self.ghost)
                self.ghost.style().polish(self.ghost)
        except Exception:
            pass

    def ghost_text(self) -> str:
        """Current ghost line. Test/inspection hook; the send path ignores it."""
        return self._ghost_text

    def _ghost_fire(self) -> None:
        """One debounced recompute. An empty field asks too: Enter still goes somewhere."""
        try:
            text = self.field.toPlainText().strip()
        except Exception:
            return
        self.ghost_requested.emit(text)

    def refresh_ghost(self) -> None:
        """Ask the window for the route now (a role, the plan mode or a turn changed)."""
        self._ghost_fire()

    def _ghost_schedule(self) -> None:
        """Restart the single timer. Called on text change only, never on paint."""
        try:
            self._ghost_timer.start()
        except Exception:
            pass

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(theme.BG))
        super().paintEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        self.wheel_requested.emit(event.angleDelta().y())
        event.accept()

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)

    def set_enter_claim(self, placeholder: str, tooltip: str = "") -> None:
        """Composer tells the truth about who Enter hits. Empty placeholder is allowed."""
        line = str(placeholder or "").strip()
        try:
            self.field.setPlaceholderText(line)
        except Exception:
            pass
        tip = str(tooltip or "").strip()
        if tip:
            self._enter_tip = tip
        if not self._turn_busy:
            try:
                self.send_btn.setToolTip(self._enter_tip)
            except Exception:
                pass

    def set_partner_bar(
        self,
        partner_on: bool,
        *,
        synth: bool = False,
        working: bool = False,
        plan: bool = False,
        summary: str = "",
        status: str = "",
    ) -> None:
        """Учитель on → «спросить». Off → no button. No strip in the composer."""
        pb = getattr(self, "partner_bar", None)
        ask_row = getattr(self, "ask_row", None)
        ask = getattr(self, "ask_btn", None)
        ask_was = ask_row is not None and not ask_row.isHidden()
        if pb is not None:
            pb.hide()
        if ask_row is not None:
            if partner_on:
                ask_row.show()
            else:
                ask_row.hide()
        if ask is not None:
            if partner_on:
                ask.show()
            else:
                ask.hide()
        ask_now = ask_row is not None and not ask_row.isHidden()
        if ask_now != ask_was:
            self.resized.emit()

    def content_height(self) -> int:
        """Stable panel: ask row (if Учитель on) + chips + field + slash. Not HUD.

        Process dock and ghost sit above this strip as overlays. Counting them
        here made the chat clip jump (fout). Empty composer is field + padding.

        Deterministic on purpose: the field's height comes from FIELD_MIN and its
        own clamped height, never from `field.height()`, and the two spacings are
        always counted. Reading live widget state made this answer 50 before the
        first layout pass and 56 after it — the startup placement then sized the
        strip 6px short, and the send button (still unlaid at (0,0)) did not
        appear until a keystroke forced a re-place (owner: "При запуске кнопки не
        было. Когда я написал и нажал enter - кнопка появилась").
        """
        m = self.layout().contentsMargins()
        sp = self.layout().spacing()
        # Margins + one gap before the field row are always spent, whether or not
        # the menu and chip slots above it are showing. Counting only VISIBLE
        # slots made this 50 before the first layout pass and 56 after it, so the
        # startup strip was 6px short and the send button did not appear.
        h = m.top() + m.bottom() + sp
        ask_row = getattr(self, "ask_row", None)
        if ask_row is not None and not ask_row.isHidden():
            h += int(getattr(theme, "ASK_H", 22)) + sp
        # Process dock + ghost are HUD overlays on the mouth, not layout slots.
        # Counting them here made the panel rebuild on click/focus.
        if not self.menu.isHidden():
            h += self.menu.height()
        if not self.chips.isHidden():
            h += max(0, self.chips.height())
        # The field row: its own real height when laid out, else the floor. Both
        # are the same 36 for an untouched field, so startup and steady state agree.
        h += max(theme.FIELD_MIN, self.field.height())
        # The route line under the field is a fixed row that is never hidden.
        h += ROUTE_H + sp
        # The process dock is a HUD overlay above this panel — it must not enter
        # panel_height or the chat bottom edge floats.
        if not self.approve_row.isHidden():
            h += max(28, self.approve_row.sizeHint().height()) + sp
        return h

    def panel_height(self) -> int:
        return self.content_height()

    def _on_text(self) -> None:
        grew = self.field.fit_height()
        self._ghost_schedule()
        q = self.field.toPlainText()
        rows = slash.matches(q)
        if not rows:
            if self.menu.isVisible():
                self.menu.hide()
                self.resized.emit()
            elif grew:
                self.resized.emit()
            return
        self.menu.clear()
        for name, label in rows:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, name)
            self.menu.addItem(item)
        self.menu.setCurrentRow(0)
        n = min(SLASH_MAX, len(rows))
        self.menu.setFixedHeight(n * SLASH_ROW + 6)
        self.menu.show()
        self.resized.emit()

    def _on_history(self, step: int) -> None:
        """Empty-field ↑/↓: hand the walk to the window, which owns the file.

        While the slash menu is open the arrows belong to the menu instead, so
        `_nav_menu` keeps them and this never steals a completion keystroke.
        """
        if not self.menu.isHidden():
            self._nav_menu(step)
            return
        self.history_requested.emit(-1 if int(step) < 0 else 1)

    def set_multiline(self, on: bool) -> None:
        """`/multiline`: Enter breaks the line, Shift+Enter sends."""
        try:
            self.field.set_multiline(bool(on))
        except Exception:
            pass

    def multiline(self) -> bool:
        try:
            return bool(self.field.multiline())
        except Exception:
            return False

    def set_history(self, rows: list[str]) -> None:
        """Seed the empty-field walk. The window reads prompts.jsonl; the
        composer only holds the list it was handed."""
        self._history = [str(r) for r in (rows or []) if str(r or "").strip()]
        self._history_at = len(self._history)

    def history(self) -> list[str]:
        return list(getattr(self, "_history", []))

    def history_walk(self, step: int) -> str | None:
        """One ↑/↓ move. Returns the text to show, or None when the field clears.

        `↓` past the newest is the way out of the walk: the field is emptied and
        the walk resets to its end.
        """
        rows = getattr(self, "_history", [])
        if not rows:
            return None
        at = int(getattr(self, "_history_at", len(rows)))
        at = (at - 1) if int(step) < 0 else (at + 1)
        if at >= len(rows):
            self._history_at = len(rows)
            return None
        at = max(0, at)
        self._history_at = at
        return rows[at]

    def put_history_text(self, text: str) -> None:
        """Replace the field with a history row, keeping the walk position."""
        self.field.blockSignals(True)
        self.field.setPlainText(str(text or ""))
        self.field.blockSignals(False)
        cursor = self.field.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.field.setTextCursor(cursor)
        self._on_text()

    def _nav_menu(self, step: int) -> None:
        if not self.menu.isVisible() or self.menu.count() == 0:
            return
        row = self.menu.currentRow()
        nxt = (row + step) % self.menu.count()
        self.menu.setCurrentRow(nxt)

    def _complete_menu(self) -> None:
        name = self._current_slash()
        if not name:
            return
        self.field.blockSignals(True)
        self.field.setPlainText(name + " ")
        self.field.blockSignals(False)
        cursor = self.field.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.field.setTextCursor(cursor)
        self._on_text()

    def _pick_item(self, item: QListWidgetItem) -> None:
        name = str(item.data(Qt.UserRole) or "")
        if not name:
            return
        self.field.blockSignals(True)
        self.field.setPlainText(name + " ")
        self.field.blockSignals(False)
        self.take_focus()
        self._on_text()

    def _current_slash(self) -> str:
        if not self.menu.isVisible():
            return ""
        item = self.menu.currentItem()
        if item is None:
            return ""
        return str(item.data(Qt.UserRole) or "")

    def _on_escape(self) -> None:
        if self.menu.isVisible():
            self.menu.hide()
            self.resized.emit()
            return
        self.stop_requested.emit()

    def set_turn_busy(self, busy: bool, *, send_is_stop: bool = True) -> None:
        """CTA: filled caret send when idle; Stop when a mouth turn is in flight.

        `send_is_stop=False` keeps the button a SEND while the mouth is busy —
        a Grok follow-up queues on the same session. Stop lives on the process
        card in the chatlog and on Esc.
        """
        busy = bool(busy)
        self._turn_busy = busy
        self._send_is_stop = bool(send_is_stop) if busy else True
        if busy and self._send_is_stop:
            self.send_btn.set_kind("stop")
            self.send_btn.setToolTip("остановить ход · Esc")
            # Visible affordance: gold border + stop glyph (owner missed tiny square).
            try:
                self.send_btn.setStyleSheet(
                    "QToolButton { background: transparent; border: 2px solid #E2A84A; border-radius: 9px; }"
                )
            except Exception:
                pass
        else:
            self.send_btn.set_kind("send")
            if busy:
                self.send_btn.setToolTip("в очереди · Enter")
            else:
                self.send_btn.setToolTip(getattr(self, "_enter_tip", None) or "отправить в рот · Enter")
            try:
                self.send_btn.setStyleSheet(
                    "QToolButton { background: transparent; border: none; }"
                )
            except Exception:
                pass

    def _on_send_or_stop(self) -> None:
        if self._turn_busy and getattr(self, "_send_is_stop", True):
            self.stop_requested.emit()
            return
        self._emit_send()

    def _emit_send(self) -> None:
        text = self.field.toPlainText().strip()
        picked = self._current_slash()
        if picked and text.startswith("/") and " " not in text.strip():
            text = picked
        if not text:
            return
        if self._turn_busy:
            # Keep the typed line. Window _on_send only sets the rail note;
            # clearing here ate follow-ups while the mouth was busy.
            self.send_requested.emit(text)
            return
        self.menu.hide()
        self.send_requested.emit(text)
        self.field.clear()
        # The verdict is spent: the empty field earns a fresh one.
        self._ghost_schedule()
        self.resized.emit()

    def _emit_btw(self) -> None:
        """Programmatic aside: open/send the answer frame, never the mouth turn.

        The composer no longer has a btw button. PartnerBar and `/btw` own the UI.
        An empty field still opens the frame so the owner can type follow-ups.
        """
        text = self.field.toPlainText().strip()
        aside = slash.extract_btw(text)
        if aside is not None:
            text = aside
        self.menu.hide()
        self.btw_requested.emit(text)
        self.field.clear()
        self._ghost_schedule()
        self.resized.emit()

    def clear_field(self) -> None:
        """Window calls this after a busy Enter was accepted as btw overflow."""
        try:
            self.field.clear()
        except Exception:
            pass
        try:
            self.menu.hide()
            self._ghost_schedule()
        except Exception:
            pass

    def take_focus(self) -> None:
        self.field.setFocus(Qt.OtherFocusReason)
        self.focused.emit()

    def sizeHint(self) -> QSize:
        return QSize(640, self.panel_height())

    def minimumSizeHint(self) -> QSize:
        return QSize(120, self.panel_height())


    def _on_retain_open(self) -> None:
        """T2: open thin retained Approve/Apply/Discard dialog. Fail-open."""
        try:
            from . import retain_rail as retain_rail_mod  # type: ignore
        except Exception:
            try:
                import retain_rail as retain_rail_mod  # type: ignore
            except Exception:
                return
        try:
            retain_rail_mod.open_dialog(self, on_changed=self._refresh_retain_live)
        except Exception:
            pass

    def _on_retain_command(self, text: str) -> None:
        """T2: ProcessDock context retain list|approve|apply|discard. Fail-open."""
        try:
            from . import retain_rail as retain_rail_mod  # type: ignore
        except Exception:
            try:
                import retain_rail as retain_rail_mod  # type: ignore
            except Exception:
                return
        try:
            got = retain_rail_mod.run_command(str(text or ""))
            if got.get("cmd") == "list":
                n = int(got.get("n") or 0)
                self.process_push_tool("retain", ok=True, detail=f"pending={n}")
            elif got.get("ok"):
                self.process_push_tool(
                    f"retain:{got.get('cmd')}",
                    ok=True,
                    detail=str(got.get("id") or got.get("status") or "")[:48],
                )
            else:
                self.process_push_tool(
                    "retain",
                    ok=False,
                    detail=str(got.get("error") or "fail")[:48],
                )
            self._refresh_retain_live()
        except Exception:
            pass

    def _refresh_retain_live(self) -> None:
        """After apply/discard: refresh retain:N on the live ProcessLine head."""
        dock = getattr(self, "process_dock", None)
        if dock is None:
            return
        try:
            from . import retain_rail as retain_rail_mod  # type: ignore
        except Exception:
            try:
                import retain_rail as retain_rail_mod  # type: ignore
            except Exception:
                return
        try:
            retain_rail_mod.invalidate_pending_cache()
        except Exception:
            pass
        try:
            head = getattr(dock, "_head", None)
            cur = str(head.text() if head is not None else "")
            # strip optional "процесс — " / "процесс - " prefix if present
            live = cur
            for sep in (" — ", " - ", " – "):
                if sep in cur:
                    live = cur.split(sep, 1)[-1].strip()
                    break
            patched = retain_rail_mod.patch_line(live)
            dock.set_live(patched)
            self.resized.emit()
        except Exception:
            pass

    def process_set_live(self, line: str) -> None:
        """No-op. Live process belongs in the chatlog (thinking/tools/hire), not a HUD line."""
        return

    def process_push_tool(self, name: str, ok: bool | None = True, detail: str = "") -> None:
        return

    def process_clear(self) -> None:
        dock = getattr(self, "process_dock", None)
        if dock is None:
            return
        try:
            dock.clear()
            self.resized.emit()
        except Exception:
            pass

