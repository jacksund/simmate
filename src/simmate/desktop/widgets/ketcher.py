import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
from PySide6.QtCore import QFile, QIODevice, QObject, QTimer, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView
from rdkit import Chem, RDLogger

from simmate.config import settings
from simmate.website.core.utils import download_ketcher

# RDKit prints parse errors to stderr; we report them in the UI instead.
RDLogger.DisableLog("rdApp.*")

# RDKit's 2D depictions use this bond length; Ketcher's molfiles use a shorter one.
RDKIT_BOND_LENGTH = 1.5

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


def _rescale_to_rdkit(mol: Chem.Mol):
    """Scale the sketch's 2D coords so its bonds match RDKit's depiction bond length."""
    if not mol.GetNumBonds() or not mol.GetNumConformers():
        return
    conformer = mol.GetConformer()
    positions = conformer.GetPositions()
    mean_bond = np.mean(
        [
            np.linalg.norm(
                positions[b.GetBeginAtomIdx()] - positions[b.GetEndAtomIdx()]
            )
            for b in mol.GetBonds()
        ]
    )
    if mean_bond == 0:
        return
    scale = RDKIT_BOND_LENGTH / mean_bond
    for i, position in enumerate(positions):
        conformer.SetAtomPosition(i, (position * scale).tolist())


class KetcherWidget(QWebEngineView):
    """An embedded Ketcher sketcher that reports the drawn structure as an RDKit Mol.

    `mol_changed` emits the sketch (with its 2D coords scaled to RDKit's bond
    length), or None once the canvas is empty. Invalid mid-edit structures are skipped.
    """

    mol_changed = Signal(object)

    def __init__(self):
        super().__init__()
        self._molfile = ""

        # Ketcher fires many change events per edit, so wait for a short pause
        self._debounce = QTimer(self, singleShot=True, interval=150)
        self._debounce.timeout.connect(self._parse)

        self.bridge = _Bridge()
        self.bridge.changed.connect(self._on_molfile)
        channel = QWebChannel(self)
        channel.registerObject("bridge", self.bridge)

        page = self.page()
        page.setWebChannel(channel)
        page.scripts().insert(self._bridge_script())
        self.setUrl(f"http://127.0.0.1:{serve_ketcher()}/index.html")

    def clear(self):
        self.page().runJavaScript('window.ketcher && window.ketcher.setMolecule("")')

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

    def _on_molfile(self, molfile: str):
        self._molfile = molfile
        self._debounce.start()

    def _parse(self):
        mol = Chem.MolFromMolBlock(self._molfile)
        if mol is None:
            return  # keep the last good query while the user is mid-edit
        if mol.GetNumAtoms() == 0:
            self.mol_changed.emit(None)
            return
        _rescale_to_rdkit(mol)
        self.mol_changed.emit(mol)
