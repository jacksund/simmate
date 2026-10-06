from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from simmate.desktop.widgets import DatasetBrowser, DatasetChat, DatasetDownloads


class DatasetsTab(QWidget):
    """
    The datasets on this computer (left), plus two ways to get more (right):
    ready-made downloads, or asking an AI assistant for data from the Simmate API.
    Each dataset is one table, saved as a parquet file in the datasets folder (see
    `get_datasets_dir`), for exploring in the Toolkit tab.
    """

    status = Signal(str)

    def __init__(self):
        super().__init__()
        self.browser = DatasetBrowser()
        self.downloads = DatasetDownloads()
        self.chat = DatasetChat()

        for section in [self.browser, self.downloads]:
            section.status.connect(self.status)
        # reveal finished downloads, and keep the "Downloaded" labels up to date
        # as datasets are moved, renamed or deleted
        self.downloads.downloaded.connect(self.browser.select)
        model = self.browser.model
        for signal in [model.rowsInserted, model.rowsRemoved, model.fileRenamed]:
            signal.connect(self.downloads.refresh)

        sources = QSplitter(Qt.Orientation.Vertical)
        sources.addWidget(self.downloads)
        sources.addWidget(self.chat)
        sources.setSizes([450, 350])
        splitter = QSplitter()
        splitter.addWidget(self.browser)
        splitter.addWidget(sources)
        splitter.setSizes([700, 700])
        for split in [sources, splitter]:
            split.setChildrenCollapsible(False)
            split.setHandleWidth(16)  # room between the sections
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.addWidget(splitter)
