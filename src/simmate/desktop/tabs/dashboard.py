from contextlib import contextmanager
from pathlib import Path

from PySide6.QtCore import (
    QEvent,
    QItemSelection,
    QItemSelectionModel,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.data import ToolkitDataset
from simmate.desktop.example_data.compounds import build_dataset
from simmate.desktop.tabs.placeholder import PlaceholderTab
from simmate.desktop.widgets import (
    PLOT_TYPES,
    AnalyzePanel,
    BackgroundTask,
    ChatbotPanel,
    ColumnChooser,
    CompoundDetails,
    CompoundFilterProxy,
    CompoundTable,
    CompoundTableModel,
    DatasetStart,
    ExportPanel,
    FeaturizePanel,
    FilterPanel,
    HistogramPanel,
    IncrementalTask,
    MouseModeToggle,
    Pane,
    PaneLayout,
    PlotPanel,
    PlotTypeChooser,
    PrimaryButton,
    ScatterPanel,
    SettingsButton,
    SidePanel,
    StyledCheckBox,
    close_icon,
    columns_icon,
    confirm,
    get_datasets_dir,
    import_dataset,
    input_style,
    lock_icon,
    plus_icon,
)

# Datasets with more rows than this ask before opening, as they can use a lot of
# memory (until large datasets are handled more frugally).
LARGE_DATASET_ROWS = 250_000


class DashboardTab(QStackedWidget):
    """
    The Toolkit tab: a start page for choosing a dataset (the sample, one from the
    Datasets tab, or an upload), then a `ToolkitWorkspace` exploring it.

    Opening another dataset builds a new workspace in place of the old one.

    `go_to_datasets` asks the window to show the Datasets tab. Subclasses can use
    their own workspace by setting `workspace_class`.
    """

    go_to_datasets = Signal()

    workspace_class: type["ToolkitWorkspace"]  # set below the class

    def __init__(self):
        super().__init__()
        self.start = DatasetStart()
        self.start.sample_requested.connect(self.open_sample)
        self.start.datasets_requested.connect(self.go_to_datasets)
        self.start.upload_requested.connect(self.upload)
        self.addWidget(self.start)
        self.workspace: ToolkitWorkspace | None = None
        self.load_task: BackgroundTask | None = None

    # --- opening datasets -----------------------------------------------------------------

    def open_sample(self):
        """Open the practice dataset (see `example_data.compounds`)."""
        self._load(
            "the sample dataset",
            lambda _: ToolkitDataset(build_dataset(), name="Sample compounds"),
        )

    def open_path(self, path: Path):
        """Open a dataset file (e.g. one from the Datasets tab)."""
        rows = ToolkitDataset.count_rows(path)
        if (
            rows is not None
            and rows > LARGE_DATASET_ROWS
            and not confirm(
                self,
                "Open a large dataset?",
                f"{path.stem} has {rows:,} rows, so it may use a lot of memory "
                "and be slow to explore.",
            )
        ):
            return
        self._load(path.stem, lambda _: ToolkitDataset.from_file(path))

    def upload(self, source: Path):
        """Save a copy of `source` to the datasets folder (as parquet), then open it."""

        def work(_):
            path = import_dataset(source, get_datasets_dir())
            return ToolkitDataset.from_file(path)

        self._load(source.name, work)

    def close_dataset(self):
        """Back to the start page, dropping the open dataset."""
        self._drop_workspace()
        self.start.reset()
        self.setCurrentWidget(self.start)

    def _load(self, name: str, work):
        self._drop_workspace()
        self.setCurrentWidget(self.start)
        self.start.set_loading(f"Opening {name}…")
        task = BackgroundTask(work, self)
        self.load_task = task
        task.finished.connect(lambda dataset: self._loaded(task, dataset))
        task.failed.connect(lambda error: self._load_failed(task, name, error))
        task.start()

    def _loaded(self, task: BackgroundTask, dataset: ToolkitDataset):
        if task is not self.load_task:
            return  # replaced by a newer request
        self.load_task = None
        self.start.reset()
        self.workspace = self.workspace_class(dataset)
        self.workspace.close_requested.connect(self.close_dataset)
        self.addWidget(self.workspace)
        self.setCurrentWidget(self.workspace)

    def _load_failed(self, task: BackgroundTask, name: str, error: str):
        if task is not self.load_task:
            return
        self.load_task = None
        self.start.set_error(f"Couldn't open {name}: {error}")

    def _drop_workspace(self):
        if self.load_task is not None:
            self.load_task.cancel()
            self.load_task = None
        if self.workspace is not None:
            self.removeWidget(self.workspace)
            self.workspace.deleteLater()
            self.workspace = None


class ToolkitWorkspace(QWidget):
    """Plots and a table of one dataset, flanked by tabbed side panels, all kept in sync.

    - The plots and table sit in an editable layout. "Add plot" adds one (pick a type
      in the new pane: scatter, histogram, bar or line; see `PLOT_TYPES`), and "Add table" (shown once the table's removed) puts it back.
      "Edit layout" unlocks it: drag a pane by its header onto another's edge to move
      it, or remove panes. By default, a scatter plot and a histogram sit above the table.
    - The left panel holds bulk tools; its Filters tab narrows everything: draw a substructure in the sketcher
      and/or set column filters. Filtered-out points/bars show in grey, or are hidden (plot settings).
    - Its Featurize tab adds columns made with `simmate.toolkit` (properties, fingerprints,
      chemical-space maps, clusters, ...), which then show in the table, filters, plots and card.
    - Its Chatbot tab is a chat about the dataset, whose replies can include Python scripts
      to run on it (e.g. to add columns, which then show everywhere like featurized ones).
    - Its Analyze tab works things out from every row at once (e.g. fitting a model that
      predicts one column from others), showing each result as a card and adding any
      columns it gives (e.g. predictions). Hovering or clicking a result's table row
      highlights or selects its compounds, and its plot button adds a plot of it.
    - Its Export tab saves every row and column (added ones too) to a file: CSV, Excel, or
      Parquet, plus molecule (SDF, SMILES, XYZ) or crystal (CIF, POSCAR) formats.
    - Zooming/panning any plot further narrows the table to the compounds in view.
    - Hovering a point (or a row) highlights its row, rings its point in every scatter
      and line plot, and outlines its bin or bar in every histogram and bar chart.
    - Hovering a point also shows a small card (structure + ID) beside the cursor
      (can be turned off in the plot settings).
    - Hovering a histogram bin (or a bar) highlights all of its rows and rings their
      points (can be turned off in its settings).
    - Clicking points, bins or bars (Ctrl+click to add/remove) selects rows; selecting rows
      rings their points and counts them in red in the histograms and bar charts. Clicking empty plot space clears the selection.
    - The selected compound shows in full in the detail card (the right panel's Selection tab).
      It shows one compound at a time, so it shows a message instead while several are selected.
    - The table settings choose whether the table scrolls to hovered/selected points,
      and the columns button beside them chooses which columns show.

    Subclasses can add or swap side panel pages by overriding `get_left_pages` and
    `get_right_pages`, the plots on offer with `get_plot_types`, and the starting
    layout with `build_default_layout` (then set `DashboardTab.workspace_class`).

    `close_requested` fires from its "Close" button, once the user confirms.
    """

    close_requested = Signal()

    def __init__(self, dataset: ToolkitDataset):
        super().__init__()
        self.dataset = dataset
        self.df = dataset.df
        self.model = CompoundTableModel(dataset)
        self.proxy = CompoundFilterProxy(self.model)

        # Our own record of the selection. The table's selection model forgets rows that
        # get filtered out, but we want them re-selected when they come back.
        self.selected_rows: set[int] = set()
        # the selected compound the detail card shows
        self.focus_row: int | None = None
        self._syncing = False

        # Every pan/zoom step fires this; debounce so we filter once the view settles.
        self.range_timer = QTimer(self, singleShot=True, interval=80)
        self.range_timer.timeout.connect(self._filter_to_view)

        # --- detail card --------------------------------------------------------------
        self.details = CompoundDetails(dataset)
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidget(self.details)
        self.details_scroll.setWidgetResizable(True)
        # no frame, and the same padding as the filter panel (mirrored)
        self.details_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.details_scroll.setContentsMargins(12, 8, 8, 8)

        # --- table --------------------------------------------------------------------
        self.table = CompoundTable(self.proxy)
        self.table.entered.connect(self._on_table_hover)
        # to notice the mouse leaving the table
        self.table.viewport().installEventFilter(self)
        self.table.selectionModel().selectionChanged.connect(self._on_table_selection)
        # how many rows are shown (and selected), above the table on the left
        self.count_label = QLabel()
        self.count_label.setStyleSheet(f"color: {theme.MUTED_COLOR};")

        # --- side panels --------------------------------------------------------------
        # One page per tab; only the open tab's page shows.
        self.filter_panel = FilterPanel(dataset)
        self.filter_panel.filters_changed.connect(self._apply_filters)
        # re-draw thumbnails and the card with the new substructure highlighted & aligned
        self.filter_panel.query_changed.connect(self.model.set_highlight)
        self.filter_panel.query_changed.connect(self.details.set_query)
        self.featurize_panel = FeaturizePanel(dataset)
        self.featurize_panel.columns_added.connect(self._on_columns_added)
        self.chatbot_panel = ChatbotPanel(dataset)
        self.chatbot_panel.columns_added.connect(self._on_columns_added)
        self.analyze_panel = AnalyzePanel(dataset)
        self.analyze_panel.columns_added.connect(self._on_columns_added)
        self.analyze_panel.rows_hovered.connect(
            lambda rows: self._on_rows_hovered(rows, None)
        )
        self.analyze_panel.rows_selected.connect(
            lambda rows: self._select_in_table(rows, scroll=True)
        )
        self.analyze_panel.plot_requested.connect(self._show_plot)
        self.export_panel = ExportPanel(dataset)
        left_pages = self.get_left_pages()
        # Filters starts open (when a subclass's pages still include it)
        left_widgets = [page for _, page in left_pages]
        self.left_panel = SidePanel(
            left_pages,
            side="left",
            width=385,
            min_width=385,
            current=(
                left_widgets.index(self.filter_panel)
                if self.filter_panel in left_widgets
                else 0
            ),
        )
        self.right_panel = SidePanel(
            self.get_right_pages(),
            side="right",
            width=385,
            min_width=385,
            open=False,  # starts collapsed
        )
        for panel in (self.left_panel, self.right_panel):
            panel.tabs.current_changed.connect(
                lambda index, panel=panel: self._show_side_page(panel, index)
            )

        # --- layout -------------------------------------------------------------------
        # A row of controls over the table, like the plots', with its own settings.
        self.scroll_to_hover_checkbox = StyledCheckBox("Scroll to hovered plot point")
        self.scroll_to_hover_checkbox.setToolTip(
            "Scroll the table to a compound's row while its point is hovered"
        )
        self.scroll_to_selection_checkbox = StyledCheckBox(
            "Scroll to selected plot point"
        )
        self.scroll_to_selection_checkbox.setToolTip(
            "Scroll the table to a compound's row when its point is clicked"
        )
        self.scroll_to_selection_checkbox.setChecked(True)
        table_settings = QWidget()
        table_settings.setStyleSheet(input_style())
        table_settings_layout = QFormLayout(table_settings)
        table_settings_layout.setContentsMargins(12, 12, 12, 12)
        table_settings_layout.setVerticalSpacing(10)
        table_settings_layout.addRow(self.scroll_to_hover_checkbox)
        table_settings_layout.addRow(self.scroll_to_selection_checkbox)
        column_chooser = ColumnChooser(self.table)
        column_chooser.setStyleSheet(input_style())
        table_controls = QHBoxLayout()
        table_controls.setSpacing(2)  # the two buttons sit close together
        table_controls.addWidget(self.count_label)
        table_controls.addStretch()
        table_controls.addWidget(
            SettingsButton(
                column_chooser, tooltip="Show/hide columns", icon=columns_icon()
            )
        )
        table_controls.addWidget(
            SettingsButton(table_settings, tooltip="Table settings")
        )

        table_panel = QWidget()
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(6)  # between the gear and the table
        table_layout.addLayout(table_controls)
        table_layout.addWidget(self.table, stretch=1)

        # The plots and table, in a layout that can be rearranged while unlocked.
        self.plots: list[PlotPanel] = []
        # one Zoom/Pan switch for every plot
        self.mouse_mode = MouseModeToggle()
        self.mouse_mode.mode_changed.connect(
            lambda mode: [plot.set_mouse_mode(mode) for plot in self.plots]
        )
        self.table_pane = Pane(table_panel, "Table")
        self.pane_layout = PaneLayout("Add a plot or the table to the layout")
        self.pane_layout.pane_removed.connect(self._on_pane_removed)
        self.build_default_layout()

        self.edit_button = PrimaryButton("Edit layout", muted=True)
        self.edit_button.setIcon(lock_icon())
        self.edit_button.setCheckable(True)
        self.edit_button.setToolTip("Unlock the layout to move, add, or remove panes")
        self.edit_button.toggled.connect(self._set_editing)
        self.add_plot_button = PrimaryButton("Add plot", muted=True)
        self.add_plot_button.setIcon(plus_icon())
        self.add_plot_button.clicked.connect(self._add_plot_pane)
        self.add_table_button = PrimaryButton("Add table", muted=True)
        self.add_table_button.setIcon(plus_icon())
        self.add_table_button.setToolTip("Put the table back in the layout")
        self.add_table_button.clicked.connect(self._add_table_pane)
        self.close_button = PrimaryButton("Close", muted=True)
        self.close_button.setIcon(close_icon())
        self.close_button.setToolTip("Close this dataset and go back to choose another")
        self.close_button.clicked.connect(self._confirm_close)
        name_label = QLabel(dataset.name)
        name_label.setStyleSheet(f"color: {theme.MUTED_COLOR}; font-weight: 600;")
        name_label.setToolTip(f"{dataset.height:,} rows")
        layout_controls = QHBoxLayout()
        layout_controls.setSpacing(8)
        layout_controls.addWidget(self.mouse_mode)
        layout_controls.addSpacing(8)
        layout_controls.addWidget(name_label)
        layout_controls.addStretch()
        for button in [
            self.add_plot_button,
            self.add_table_button,
            self.edit_button,
            self.close_button,
        ]:
            layout_controls.addWidget(button)
        self._update_add_table()

        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)
        main_layout.addLayout(layout_controls)
        main_layout.addWidget(self.pane_layout, stretch=1)

        # Each tab bar sits just inside its splitter handle, so it hugs its panel's
        # edge when open and the window's edge when collapsed.
        main_with_tabs = QWidget()
        tabs_layout = QHBoxLayout(main_with_tabs)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        tabs_layout.setSpacing(14)
        tabs_layout.addWidget(self.left_panel.tabs)
        tabs_layout.addWidget(main, stretch=1)
        tabs_layout.addWidget(self.right_panel.tabs)

        # Only the side panels can collapse: by closing their open tab or by
        # dragging their handle all the way to the window's edge.
        self.outer_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.outer_splitter.setHandleWidth(3)
        self.outer_splitter.addWidget(self.left_panel)
        self.outer_splitter.addWidget(main_with_tabs)
        self.outer_splitter.addWidget(self.right_panel)
        self.outer_splitter.setCollapsible(1, False)
        # Extra width (e.g. a bigger window) goes to the center, so the side panels
        # open at their set widths.
        for index, stretch in enumerate([0, 1, 0]):
            self.outer_splitter.setStretchFactor(index, stretch)
        left, right = (
            panel.open_width if panel.tabs.current() >= 0 else 0  # 0 = collapsed
            for panel in (self.left_panel, self.right_panel)
        )
        self.outer_splitter.setSizes([left, 640, right])
        self.outer_splitter.splitterMoved.connect(self._sync_side_tabs)

        layout = QVBoxLayout(self)
        layout.addWidget(self.outer_splitter)

        self._apply_filters()

        # The sketcher's substructure search needs an index of every molecule. It's
        # slow to build for large datasets, so it's built a little at a time (and
        # stops if the workspace is closed first).
        if dataset.has_molecules:
            self.index_task = IncrementalTask(
                dataset.build_substructure_index(), dataset.height, self
            )
            self.index_task.progress.connect(self.filter_panel.set_index_progress)
            self.index_task.finished.connect(self.filter_panel.set_index_ready)
            self.index_task.failed.connect(
                lambda error: self.filter_panel.set_index_ready(False, error)
            )
            self.filter_panel.set_index_progress(0, dataset.height)
            self.index_task.start()

    # --- side panel pages -----------------------------------------------------------------

    def get_left_pages(self) -> list[tuple[str, QWidget]]:
        """The (title, page) pairs of the left panel, for bulk / table operations.

        Tabs not built yet open a "coming soon" page for now.
        """
        return [
            ("Chatbot", self.chatbot_panel),
            ("Filter", self.filter_panel),
            ("Featurize", self.featurize_panel),
            ("Analyze", self.analyze_panel),
            ("Export", self.export_panel),
        ]

    def get_right_pages(self) -> list[tuple[str, QWidget]]:
        """The (title, page) pairs of the right panel, for work on the selected compound(s).

        Tabs not built yet open a "coming soon" page for now.
        """
        return [
            ("Select", self.details_scroll),
            ("Transform", PlaceholderTab("Transform")),
            ("Enumerate", PlaceholderTab("Enumerate")),
            ("Workflows", PlaceholderTab("Workflows")),
        ]

    # --- layout ---------------------------------------------------------------------------

    def get_plot_types(self) -> dict[str, type[PlotPanel]]:
        """The plots that can be added to the layout, by the name shown for each."""
        return PLOT_TYPES

    def build_default_layout(self):
        """Fill the empty layout: a scatter plot and a histogram above the table."""
        scatter = Pane(self._add_plot(ScatterPanel), ScatterPanel.title)
        histogram = Pane(self._add_plot(HistogramPanel), HistogramPanel.title)
        self.pane_layout.add_pane(scatter)
        self.pane_layout.add_pane(histogram, scatter, "right")
        self.pane_layout.add_pane(self.table_pane, side="bottom")

    def _confirm_close(self):
        if confirm(
            self,
            "Close this dataset?",
            f"Your plots, filters, selection and added columns for "
            f"{self.dataset.name} will be cleared. The dataset itself stays in My "
            "datasets, so you can open it again anytime.",
        ):
            self.close_requested.emit()

    def _set_editing(self, editing: bool):
        self.pane_layout.set_editing(editing)
        self.edit_button.setText("Done" if editing else "Edit layout")

    def _update_add_table(self):
        # there's only ever one table, so this shows only while it's been removed
        self.add_table_button.setVisible(
            self.table_pane not in self.pane_layout.panes()
        )

    def _add_plot(self, plot_type: type[PlotPanel]) -> PlotPanel:
        """Make a plot of `plot_type` that's kept in sync with everything else."""
        plot = plot_type(
            self.dataset.columns,
            self.details.svg if self.dataset.has_molecules else None,
        )
        plot.rows_hovered.connect(
            lambda rows, plot=plot: self._on_rows_hovered(rows, plot)
        )
        plot.rows_clicked.connect(self._on_rows_clicked)
        plot.background_clicked.connect(self._clear_selection)
        plot.view_changed.connect(self.range_timer.start)
        plot.set_mouse_mode(self.mouse_mode.mode)
        plot.set_passing(self.proxy.passing)
        plot.set_selected(self.selected_rows)
        self.plots.append(plot)
        self.range_timer.start()  # narrow the table to its view too
        return plot

    def _add_plot_pane(self):
        """Add a new plot beside the last one, showing a choice of plot types."""
        chooser = PlotTypeChooser(self.get_plot_types())
        pane = Pane(chooser, "New plot")
        chooser.chosen.connect(lambda name: self._choose_plot(pane, name))
        self._add_beside_plots(pane)

    def _show_plot(self, name: str, config: dict):
        """Add a plot of type `name` with the settings in `config` (as from
        `PlotPanel.config`) beside the last plot, e.g. a result's parity plot."""
        plot_type = self.get_plot_types()[name]
        plot = self._add_plot(plot_type)
        plot.apply_config(config)
        self._add_beside_plots(Pane(plot, plot_type.title))

    def _add_beside_plots(self, pane: Pane):
        """Put a new pane to the right of the last plot, or above the table."""
        others = [p for p in self.pane_layout.panes() if p is not self.table_pane]
        if others:
            self.pane_layout.add_pane(pane, others[-1], "right")
        else:
            self.pane_layout.add_pane(pane, side="top")

    def _choose_plot(self, pane: Pane, name: str):
        plot_type = self.get_plot_types()[name]
        pane.set_content(self._add_plot(plot_type), plot_type.title)

    def _add_table_pane(self):
        self.pane_layout.add_pane(self.table_pane, side="bottom")
        self._update_add_table()

    def _on_pane_removed(self, pane: Pane):
        # The table is only ever hidden, so it (and its selection) can come back.
        if pane is self.table_pane:
            self._update_add_table()
            return
        if pane.content in self.plots:
            self.plots.remove(pane.content)
            self._on_rows_hovered(set(), None)  # it may have had the hover
            self._filter_to_view()  # its view no longer narrows the table
        pane.deleteLater()

    # --- helpers --------------------------------------------------------------------------

    def _proxy_index(self, row: int):
        return self.proxy.index_of(row)

    def _show_selection_card(self):
        if len(self.selected_rows) > 1:
            self.details.show_many(len(self.selected_rows))
        else:
            self.details.show_row(self.focus_row)

    def _update_count(self):
        text = f"{self.proxy.rowCount():,} of {self.df.height:,} rows shown"
        if self.selected_rows:
            text += f", {len(self.selected_rows):,} selected"
        self.count_label.setText(text)

    # --- side panels -----------------------------------------------------------------------

    def _show_side_page(self, panel: SidePanel, index: int):
        """Open `panel` on page `index`, or collapse it when -1."""
        self._update_min_widths(panel)
        sizes = self.outer_splitter.sizes()
        i = self.outer_splitter.indexOf(panel)
        if index < 0:
            if sizes[i] > 0:
                panel.open_width = sizes[i]
            sizes[1] += sizes[i]
            sizes[i] = 0
        else:
            panel.setCurrentIndex(index)
            if sizes[i] == 0:
                # take the space from the center, but never more than half of it
                sizes[i] = min(panel.open_width, sizes[1] // 2)
                sizes[1] -= sizes[i]
        self.outer_splitter.setSizes(sizes)

    def _update_min_widths(self, panel: SidePanel):
        # A panel's minimum width depends on whether it's open; have the splitter and
        # the layouts above it re-read it.
        panel.updateGeometry()
        self.outer_splitter.updateGeometry()

    def _sync_side_tabs(self, *_):
        # The user dragged a handle: dragged shut closes the panel's open tab, and
        # dragged back open re-opens the page that was showing.
        for panel in (self.left_panel, self.right_panel):
            width = self.outer_splitter.sizes()[self.outer_splitter.indexOf(panel)]
            if width == 0:
                panel.tabs.set_current(-1, emit=False)
            else:
                panel.open_width = width
                if panel.tabs.current() < 0:
                    panel.tabs.set_current(panel.currentIndex(), emit=False)
            self._update_min_widths(panel)

    # --- added columns ------------------------------------------------------------------------

    def _on_columns_added(self, added: list[str], replaced: list[str]):
        """The Featurize, Analyze or Chatbot panel added columns to the dataset
        (replacing any of the same name): show them everywhere."""
        self.df = self.dataset.df
        self.model.add_columns(added, replaced)
        self.filter_panel.add_columns(added, replaced)
        self.analyze_panel.add_columns(added, replaced)
        self.featurize_panel.mark_present()  # e.g. a fingerprint a model needed
        self.details.add_columns(added)
        for plot in self.plots:
            plot.refresh_columns()
        # replaced values may pass the filters (or plots' views) differently
        self._apply_filters()
        self._filter_to_view()

    # --- filters ----------------------------------------------------------------------------

    @contextmanager
    def _refiltering(self):
        """Wrap a change to the table's rows: the selection churn it causes is ignored,
        then rows of our selection that are (back) in the table are re-selected."""
        self._syncing = True
        try:
            yield
            self._select_in_table(self.selected_rows, scroll=False)
        finally:
            self._syncing = False

    def _apply_filters(self):
        with self._refiltering():
            self.proxy.set_filters(**self.filter_panel.filters())
        for plot in self.plots:
            plot.set_passing(self.proxy.passing)
        self._update_count()

    # --- plots -> table ---------------------------------------------------------------------

    def _on_rows_hovered(self, rows: set[int], source: PlotPanel | None):
        """`rows` are hovered in `source` (a plot, or the table when None): highlight
        their rows and mark them in every other plot."""
        self.model.set_highlighted_rows(rows)
        for plot in self.plots:
            if plot is not source:
                plot.show_hovered(rows)
        if (
            source is not None
            and len(rows) == 1
            and self.scroll_to_hover_checkbox.isChecked()
        ):
            self.table.scrollTo(
                self._proxy_index(next(iter(rows))),
                QAbstractItemView.ScrollHint.EnsureVisible,
            )

    def _on_rows_clicked(self, rows: set[int], modifiers, current: int | None):
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            # add the rows, or remove them when they're all selected already
            if rows <= self.selected_rows:
                rows = self.selected_rows - rows
            else:
                rows = self.selected_rows | rows
        self._select_in_table(
            rows, scroll=self.scroll_to_selection_checkbox.isChecked(), current=current
        )

    def _clear_selection(self):
        self.table.clearSelection()

    def _filter_to_view(self):
        with self._refiltering():
            self.proxy.set_view_ranges(
                [view for plot in self.plots for view in plot.view_ranges()]
            )
        self._update_count()

    def _select_in_table(
        self, rows: set[int], scroll: bool, current: int | None = None
    ):
        selection = QItemSelection()
        for row in rows:
            index = self._proxy_index(row)
            if index.isValid():  # invalid = currently filtered out of the table
                selection.select(index, index)
        flags = (
            QItemSelectionModel.SelectionFlag.ClearAndSelect
            | QItemSelectionModel.SelectionFlag.Rows
        )
        selection_model = self.table.selectionModel()
        if current in rows:
            # also make the clicked row "current" so the card focuses on it
            selection_model.setCurrentIndex(
                self._proxy_index(current), QItemSelectionModel.SelectionFlag.NoUpdate
            )
        selection_model.select(selection, flags)
        if scroll and not selection.isEmpty():
            self.table.scrollTo(
                selection.indexes()[0], QAbstractItemView.ScrollHint.EnsureVisible
            )

    # --- table -> plot ----------------------------------------------------------------------

    def _on_table_selection(self, *_):
        if self._syncing:
            return  # selection churn caused by filtering, not by the user
        indexes = self.table.selectionModel().selectedRows()
        self.selected_rows = {self.proxy.dataset_row(i) for i in indexes}

        current = self.table.selectionModel().currentIndex()
        current_row = self.proxy.dataset_row(current) if current.isValid() else None
        if current_row in self.selected_rows:
            self.focus_row = current_row
        elif self.selected_rows:
            self.focus_row = min(self.selected_rows)
        else:
            self.focus_row = None
        self._show_selection_card()

        self._refresh_selection_marks()
        self._update_count()

    def _refresh_selection_marks(self):
        for plot in self.plots:
            plot.set_selected(self.selected_rows)

    def _on_table_hover(self, index):
        self._on_rows_hovered({self.proxy.dataset_row(index)}, None)

    def eventFilter(self, watched, event):
        if watched is self.table.viewport() and event.type() == QEvent.Type.Leave:
            self._on_rows_hovered(set(), None)
        return super().eventFilter(watched, event)


DashboardTab.workspace_class = ToolkitWorkspace
