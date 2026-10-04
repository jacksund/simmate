import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from PySide6.QtCore import (
    QByteArray,
    QFile,
    QIODevice,
    QObject,
    Qt,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QLabel, QSplitter, QVBoxLayout, QWidget
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors

from simmate.config import settings
from simmate.desktop.utilities import mol_to_svg
from simmate.website.core.utils import download_ketcher

# RDKit prints parse errors to stderr; we report them in the UI instead.
RDLogger.DisableLog("rdApp.*")

# Runs inside the Ketcher page: once Ketcher is ready, forward every edit to
# Python as a molfile through the QWebChannel bridge.
BRIDGE_JS = """
new QWebChannel(qt.webChannelTransport, function (channel) {
    var bridge = channel.objects.bridge;
    var check = setInterval(function () {
        if (!window.ketcher || !window.ketcher.editor) return;
        clearInterval(check);
        window.ketcher.editor.subscribe("change", function () {
            window.ketcher.getMolfile().then(function (molfile) {
                bridge.mol_changed(molfile);
            });
        });
    }, 100);
});
"""


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve_ketcher() -> int:
    """Serve the Ketcher standalone build on a free localhost port and return it.

    Ketcher loads Indigo as WASM, which doesn't work reliably over file:// URLs.
    """
    download_ketcher()
    ketcher_dir = settings.config_directory / "static_files" / "ketcher"
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(_QuietHandler, directory=str(ketcher_dir))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server.server_address[1]


class _Bridge(QObject):
    """The Python object that the page's JavaScript calls into."""

    changed = Signal(str)

    @Slot(str)
    def mol_changed(self, molfile: str):
        self.changed.emit(molfile)


class SketcherTab(QWidget):
    """Draw a molecule in Ketcher (left); RDKit renders it and reports MW live (right)."""

    status = Signal(str)

    def __init__(self):
        super().__init__()
        self._molfile = ""

        # Ketcher fires many change events per edit, so wait for a short pause
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(150)
        self._debounce.timeout.connect(self.update_preview)

        self.bridge = _Bridge()
        self.bridge.changed.connect(self._on_mol_changed)
        channel = QWebChannel(self)
        channel.registerObject("bridge", self.bridge)

        self.web_view = QWebEngineView()
        page = self.web_view.page()
        page.setWebChannel(channel)
        page.scripts().insert(self._bridge_script())
        self.web_view.setUrl(f"http://127.0.0.1:{serve_ketcher()}/index.html")

        self.svg_widget = QSvgWidget()
        self.svg_widget.setStyleSheet("background: white;")
        self.svg_widget.setMinimumWidth(250)
        self.mw_label = QLabel()
        self.mw_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.formula_label = QLabel()
        self.smiles_label = QLabel()
        self.smiles_label.setWordWrap(True)
        self.smiles_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        preview = QWidget()
        preview_layout = QVBoxLayout(preview)
        preview_layout.addWidget(self.svg_widget, stretch=1)
        preview_layout.addWidget(self.mw_label)
        preview_layout.addWidget(self.formula_label)
        preview_layout.addWidget(self.smiles_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.web_view)
        splitter.addWidget(preview)
        splitter.setSizes([650, 350])

        layout = QVBoxLayout(self)
        layout.addWidget(splitter)

        self._clear_preview()

    @staticmethod
    def _bridge_script() -> QWebEngineScript:
        # qwebchannel.js ships inside Qt's resources; prepend it to our bridge code
        source = QFile(":/qtwebchannel/qwebchannel.js")
        source.open(QIODevice.OpenModeFlag.ReadOnly)
        script = QWebEngineScript()
        script.setSourceCode(bytes(source.readAll()).decode() + BRIDGE_JS)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        return script

    def _on_mol_changed(self, molfile: str):
        self._molfile = molfile
        self._debounce.start()

    def update_preview(self):
        mol = Chem.MolFromMolBlock(self._molfile)
        if mol is None:
            # keep the last good drawing while the user is mid-edit
            self.status.emit("Invalid or incomplete structure")
            return
        if mol.GetNumAtoms() == 0:
            self._clear_preview()
            return

        self.svg_widget.load(QByteArray(mol_to_svg(mol)))
        # load() swaps in a new renderer config, so re-apply the aspect ratio.
        self.svg_widget.renderer().setAspectRatioMode(
            Qt.AspectRatioMode.KeepAspectRatio
        )
        formula = rdMolDescriptors.CalcMolFormula(mol)
        self.mw_label.setText(f"MW: {Descriptors.MolWt(mol):.2f} g/mol")
        self.formula_label.setText(f"Formula: {formula}")
        self.smiles_label.setText(f"SMILES: {Chem.MolToSmiles(mol)}")
        self.status.emit(f"{formula} - {mol.GetNumAtoms()} heavy atoms")

    def _clear_preview(self):
        self.svg_widget.load(QByteArray())
        self.mw_label.setText("MW: -")
        self.formula_label.setText("Formula: -")
        self.smiles_label.setText("SMILES: -")
        self.status.emit("Draw a molecule to see its properties")
