import threading
from functools import cache, partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from PySide6.QtCore import QFile, QIODevice, QObject, QTimer, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView

from simmate.config import settings
from simmate.toolkit import Molecule
from simmate.website.core.utils import download_ketcher

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


@cache
def serve_ketcher() -> int:
    """Serve the Ketcher standalone build on a free localhost port and return it.

    Ketcher loads Indigo as WASM, which doesn't work reliably over file:// URLs.
    The server is started once and shared by every sketcher.
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


class KetcherWidget(QWebEngineView):
    """An embedded Ketcher sketcher that reports the drawn structure as a `Molecule`.

    `mol_changed` emits the sketch (with Ketcher's 2D coords), or None once the
    canvas is empty. Invalid mid-edit structures are skipped.
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
        try:
            molecule = Molecule.from_sdf(self._molfile)
        except Molecule.EmptyMoleculeError:
            molecule = None  # the canvas was cleared
        except Exception:
            return  # keep the last good query while the user is mid-edit
        self.mol_changed.emit(molecule)
