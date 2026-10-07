from collections.abc import Iterator

from PySide6.QtCore import QMimeData, QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.theme import tint
from simmate.desktop.widgets.button import button_style
from simmate.desktop.widgets.plot_toolbar import GEAR_SIZE, grip_icon, trash_icon

# Marks a drag as one of our panes, so the drop overlay ignores anything else.
MIME_TYPE = "application/x-simmate-pane"
HANDLE_WIDTH = 14  # px; doubles as the gap between panes
EDIT_MARGIN = 8  # px between the dashed outline and a pane's content while editing
DRAG_PREVIEW_WIDTH = 240  # px

PANE_STYLE = """
#pane[editing="true"] {
    border: 1px dashed palette(mid); border-radius: 6px;
}
"""


class _PaneHeader(QWidget):
    """The bar a pane shows while editing: drag it to move the pane, or remove it."""

    def __init__(self, pane: "Pane", title: str, removable: bool):
        super().__init__()
        self.pane = pane
        self._press_pos: QPoint | None = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("Drag to move")

        grip = QLabel()
        grip.setPixmap(grip_icon().pixmap(GEAR_SIZE, GEAR_SIZE))
        self.title_label = QLabel(title)
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet(f"color: {theme.MUTED_COLOR};")

        self.remove_button = QToolButton()
        self.remove_button.setProperty("muted", True)  # grey, read by button_style
        self.remove_button.setStyleSheet(button_style())
        self.remove_button.setIcon(trash_icon())
        self.remove_button.setIconSize(QSize(GEAR_SIZE, GEAR_SIZE))
        self.remove_button.setToolTip("Remove from the layout")
        self.remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_button.clicked.connect(pane.remove)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(grip)
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.remove_button)
        # Only once it has a parent: showing a parentless widget opens it as a window
        # of its own for a moment, which can leave the OS's busy cursor up for a while.
        self.remove_button.setVisible(removable)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self._press_pos is None:
            return
        moved = event.position().toPoint() - self._press_pos
        if moved.manhattanLength() >= QApplication.startDragDistance():
            self._press_pos = None
            self.pane.start_drag()

    def mouseReleaseEvent(self, event):
        self._press_pos = None


class Pane(QFrame):
    """One widget (e.g. a plot or the table) in a `PaneLayout`.

    While the layout is being edited, the pane is outlined and gets a header with its
    title: drag the header to move the pane, or click its trash button to remove it
    (unless the pane isn't `removable`).
    """

    def __init__(self, content: QWidget, title: str, removable: bool = True):
        super().__init__(objectName="pane")
        self.setStyleSheet(PANE_STYLE)
        self.content = content
        self.header = _PaneHeader(self, title, removable)
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(6)
        self._layout.addWidget(self.header)
        self._layout.addWidget(content, stretch=1)
        self.set_editing(False)

    @property
    def title(self) -> str:
        return self.header.title_label.text()

    def set_content(self, content: QWidget, title: str):
        """Swap the pane's content (deleting the old one) and title."""
        self._layout.replaceWidget(self.content, content)
        self.content.deleteLater()
        self.content = content
        self.header.title_label.setText(title)

    def set_editing(self, editing: bool):
        self.header.setVisible(editing)
        self._layout.setContentsMargins(*[EDIT_MARGIN if editing else 0] * 4)
        self.setProperty("editing", editing)
        self.style().polish(self)  # re-read the stylesheet for the new property

    def pane_layout(self) -> "PaneLayout | None":
        """The layout this pane is in (or was last in)."""
        parent = self.parentWidget()
        while parent is not None and not isinstance(parent, PaneLayout):
            parent = parent.parentWidget()
        return parent

    def remove(self):
        self.pane_layout().remove_pane(self)

    def start_drag(self):
        layout = self.pane_layout()
        mime = QMimeData()
        mime.setData(MIME_TYPE, b"")
        drag = QDrag(self)
        drag.setMimeData(mime)
        # a snapshot of the pane, so it looks like you're carrying it
        preview = self.grab()
        width = min(DRAG_PREVIEW_WIDTH, self.width())
        preview = preview.scaledToWidth(
            round(width * preview.devicePixelRatio()),
            Qt.TransformationMode.SmoothTransformation,
        )
        drag.setPixmap(preview)
        drag.setHotSpot(QPoint(width // 2, 12))
        layout.begin_drag(self)
        try:
            drag.exec(Qt.DropAction.MoveAction)
        finally:
            layout.end_drag()


class _DropOverlay(QWidget):
    """A see-through layer over the whole layout, shown only while a pane is dragged.

    It takes the drop instead of the panes' contents (plots would otherwise swallow
    the drag events), and shades the half of the pane under the cursor that the
    dragged pane would land in.
    """

    def __init__(self, layout: "PaneLayout"):
        super().__init__(layout)
        self.pane_layout = layout
        self.setAcceptDrops(True)
        self.target: Pane | None = None
        self.side: str | None = None
        self.hide()

    def _set_spot(self, target: Pane | None, side: str | None):
        if (target, side) != (self.target, self.side):
            self.target, self.side = target, side
            self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MIME_TYPE):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        self._set_spot(*self.pane_layout.drop_spot(event.position().toPoint()))
        if self.target is None:
            event.ignore()
        else:
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._set_spot(None, None)

    def dropEvent(self, event):
        target, side = self.target, self.side
        self._set_spot(None, None)
        if target is None:
            event.ignore()
            return
        event.acceptProposedAction()
        self.pane_layout.move_pane(self.pane_layout.dragged, target, side)

    def paintEvent(self, event):
        if self.target is None:
            return
        rect = self.pane_layout.drop_rect(self.target, self.side)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(tint(theme.PRIMARY_COLOR, theme.PRESSED_ALPHA))
        painter.setPen(QPen(QColor(theme.PRIMARY_COLOR), 2))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)


class PaneLayout(QWidget):
    """Panes in nested splitters, which can be rearranged by drag-and-drop.

    Each pane sits in a splitter next to its neighbors, so the gaps between them can
    be dragged to resize them at any time. While editing (`set_editing(True)`), panes
    show a header to drag them by: dropping one on a pane's edge places it on that
    side of the pane. Moving a pane only moves its widget, so it keeps its contents
    (e.g. a plot keeps its zoom).

    Removed panes are hidden and kept, and `pane_removed` is emitted so their owner
    can delete them or add them back later.
    """

    pane_removed = Signal(object)

    def __init__(self, empty_text: str = "Nothing to show"):
        super().__init__()
        self.root: QWidget | None = None  # a Pane, or a QSplitter of them
        self.editing = False
        self.dragged: Pane | None = None

        self.empty_label = QLabel(empty_text)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"color: {theme.MUTED_COLOR};")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.empty_label)
        self.overlay = _DropOverlay(self)

    # --- panes --------------------------------------------------------------------------

    def panes(self) -> list[Pane]:
        """The panes in the layout, in order (left to right, top to bottom)."""
        return list(self._walk(self.root))

    def _walk(self, widget: QWidget | None) -> Iterator[Pane]:
        if isinstance(widget, Pane):
            yield widget
        elif isinstance(widget, QSplitter):
            for index in range(widget.count()):
                yield from self._walk(widget.widget(index))

    def add_pane(self, pane: Pane, target: Pane | None = None, side: str = "right"):
        """Place `pane` on `side` ("left", "right", "top" or "bottom") of `target`, or
        of the whole layout when `target` is None. The two split the space evenly."""
        pane.set_editing(self.editing)
        if self.root is None:
            self._set_root(pane)
            return
        if target is None:
            target = self.root
        orientation = (
            Qt.Orientation.Horizontal
            if side in ("left", "right")
            else Qt.Orientation.Vertical
        )
        after = side in ("right", "bottom")
        parent = target.parentWidget()

        if target is self.root and isinstance(target, QSplitter):
            if target.orientation() == orientation:
                # one more pane at the start/end, with an even share of the space
                sizes = target.sizes()
                share = sum(sizes) // (len(sizes) + 1)
                target.insertWidget(target.count() if after else 0, pane)
                target.setSizes(sizes + [share] if after else [share] + sizes)
                pane.show()
                return
        elif isinstance(parent, QSplitter) and parent.orientation() == orientation:
            # split the target's share of the splitter it's already in
            index = parent.indexOf(target)
            sizes = parent.sizes()
            half = sizes[index] // 2
            sizes[index : index + 1] = [sizes[index] - half, half]
            parent.insertWidget(index + after, pane)
            parent.setSizes(sizes)
            pane.show()
            return

        # Otherwise the target gets a new splitter of its own, in the same place.
        splitter = self._splitter(orientation)
        if target is self.root:
            self._layout.replaceWidget(target, splitter)
            self.root = splitter
        else:
            index = parent.indexOf(target)
            sizes = parent.sizes()
            parent.replaceWidget(index, splitter)  # hides & un-parents the target
            parent.setSizes(sizes)
        for widget in [target, pane] if after else [pane, target]:
            splitter.addWidget(widget)
            widget.show()
        splitter.setSizes([1000, 1000])  # half each
        splitter.show()

    def remove_pane(self, pane: Pane):
        self._detach(pane)
        self.pane_removed.emit(pane)

    def move_pane(self, pane: Pane, target: Pane, side: str):
        if pane is target:
            return
        self._detach(pane)
        self.add_pane(pane, target, side)

    def set_editing(self, editing: bool):
        self.editing = editing
        for pane in self.panes():
            pane.set_editing(editing)

    def _detach(self, pane: Pane):
        """Take `pane` out of the layout (hidden, but kept as our child), then tidy up
        the splitter it leaves behind."""
        parent = pane.parentWidget()
        if pane is self.root:
            self._layout.removeWidget(pane)
            self._set_root(None)
        pane.hide()
        pane.setParent(self)
        if isinstance(parent, QSplitter):
            self._collapse(parent)

    def _collapse(self, splitter: QSplitter):
        """Replace a splitter left holding one widget with that widget."""
        if splitter.count() != 1:
            return
        only = splitter.widget(0)
        if splitter is self.root:
            self._layout.replaceWidget(splitter, only)
            self.root = only
        else:
            grandparent = splitter.parentWidget()
            sizes = grandparent.sizes()
            grandparent.replaceWidget(grandparent.indexOf(splitter), only)
            grandparent.setSizes(sizes)
        only.show()
        splitter.deleteLater()

    def _set_root(self, widget: QWidget | None):
        self.root = widget
        if widget is not None:
            self._layout.addWidget(widget)
            widget.show()
        self.empty_label.setVisible(widget is None)

    def _splitter(self, orientation: Qt.Orientation) -> QSplitter:
        # Parented now so Qt owns it: PySide's QSplitter.replaceWidget doesn't take
        # ownership, so Python would otherwise delete it (and its panes) once unused.
        splitter = QSplitter(orientation, self)
        splitter.hide()  # until it's placed
        splitter.setHandleWidth(HANDLE_WIDTH)
        # a pane dragged down to nothing would be easy to lose track of
        splitter.setChildrenCollapsible(False)
        return splitter

    # --- dragging -----------------------------------------------------------------------

    def begin_drag(self, pane: Pane):
        self.dragged = pane
        self.overlay.setGeometry(self.rect())
        self.overlay.show()
        self.overlay.raise_()

    def end_drag(self):
        self.overlay.hide()
        self.dragged = None

    def _rect_of(self, pane: Pane) -> QRect:
        return QRect(pane.mapTo(self, QPoint(0, 0)), pane.size())

    def drop_spot(self, pos: QPoint) -> tuple[Pane | None, str | None]:
        """The pane under `pos` and which of its edges `pos` is closest to, or
        (None, None) over a gap or the pane being dragged."""
        for pane in self.panes():
            rect = self._rect_of(pane)
            if not rect.contains(pos):
                continue
            if pane is self.dragged:
                return None, None
            x = (pos.x() - rect.left()) / max(rect.width(), 1)
            y = (pos.y() - rect.top()) / max(rect.height(), 1)
            distances = {"left": x, "right": 1 - x, "top": y, "bottom": 1 - y}
            return pane, min(distances, key=distances.get)
        return None, None

    def drop_rect(self, pane: Pane, side: str) -> QRect:
        """The half of `pane` on `side`, where a pane dropped there would go."""
        rect = self._rect_of(pane)
        if side == "left":
            rect.setWidth(rect.width() // 2)
        elif side == "right":
            rect.setLeft(rect.left() + rect.width() // 2)
        elif side == "top":
            rect.setHeight(rect.height() // 2)
        else:
            rect.setTop(rect.top() + rect.height() // 2)
        return rect
