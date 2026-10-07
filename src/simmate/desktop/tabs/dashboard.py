from contextlib import contextmanager

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
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop.example_data.compounds import build_dataset
from simmate.desktop.tabs.placeholder import PlaceholderTab
from simmate.desktop.widgets import (
    PLOT_TYPES,
    ColumnChooser,
    CompoundDetails,
    CompoundFilterProxy,
    CompoundTable,
    CompoundTableModel,
    FilterPanel,
    HistogramPanel,
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
    columns_icon,
    input_style,
    lock_icon,
    plus_icon,
)


class DashboardTab(QWidget):
    """Plots and a table, flanked by tabbed side panels, all kept in sync.

    - The plots and table sit in an editable layout. "Add plot" adds one (pick a type
      in the new pane), and "Add table" (shown once the table's removed) puts it back.
      "Edit layout" unlocks it: drag a pane by its header onto another's edge to move
      it, or remove panes. By default, a scatter plot and a histogram sit above the table.
    - The left panel holds bulk tools; its Filters tab narrows everything: draw a substructure in the sketcher
      and/or set column filters. Filtered-out points/bars show in grey, or are hidden (plot settings).
    - Zooming/panning any plot further narrows the table to the compounds in view.
    - Hovering a point (or a row) highlights its row, rings its point in every scatter
      plot, and outlines its bin in every histogram.
    - Hovering a point also shows a small card (structure + ID) beside the cursor
      (can be turned off in the plot settings).
    - Hovering a histogram bin highlights all of its rows and rings their points
      (can be turned off in the histogram settings).
    - Clicking points or bins (Ctrl+click to add/remove) selects rows; selecting rows rings
      their points and counts them in red in the histograms. Clicking empty plot space clears the selection.
    - The selected compound shows in full in the detail card (the right panel's Selection tab).
      It shows one compound at a time, so it shows a message instead while several are selected.
    - The table settings choose whether the table scrolls to hovered/selected points,
      and the columns button beside them chooses which columns show.

    Subclasses can add or swap side panel pages by overriding `get_left_pages` and
    `get_right_pages`, the plots on offer with `get_plot_types`, and the starting
    layout with `build_default_layout`.
    """

    status = Signal(str)

    def __init__(self):
        super().__init__()
        self.mdf = build_dataset()
        self.df = self.mdf.df
        self.model = CompoundTableModel(self.mdf)
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
        self.details = CompoundDetails(self.mdf)
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

        # --- side panels --------------------------------------------------------------
        # One page per tab; only the open tab's page shows.
        self.filter_panel = FilterPanel(self.mdf)
        self.filter_panel.filters_changed.connect(self._apply_filters)
        # re-draw thumbnails and the card with the new substructure highlighted & aligned
        self.filter_panel.query_changed.connect(self.model.set_highlight)
        self.filter_panel.query_changed.connect(self.details.set_query)
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
        layout_controls = QHBoxLayout()
        layout_controls.setSpacing(8)
        layout_controls.addWidget(self.mouse_mode)
        layout_controls.addStretch()
        for button in [self.add_plot_button, self.add_table_button, self.edit_button]:
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
        # Again once the window is listening, so the count replaces its "Ready".
        QTimer.singleShot(0, self._update_count)

    # --- side panel pages -----------------------------------------------------------------

    def get_left_pages(self) -> list[tuple[str, QWidget]]:
        """The (title, page) pairs of the left panel, for bulk / table operations.

        Tabs not built yet open a "coming soon" page for now.
        """
        return [
            ("Logs", PlaceholderTab("Logs")),
            ("Filter", self.filter_panel),
            ("Featurize", PlaceholderTab("Featurize")),
            ("Analyze", PlaceholderTab("Analyze")),
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
        plot = plot_type(self.df, self.details.svg)
        plot.rows_hovered.connect(
            lambda rows, plot=plot: self._on_rows_hovered(rows, plot)
        )
        plot.rows_clicked.connect(self._on_rows_clicked)
        plot.background_clicked.connect(self._clear_selection)
        plot.view_changed.connect(self.range_timer.start)
        plot.status.connect(self.status)
        plot.set_mouse_mode(self.mouse_mode.mode)
        plot.set_passing(self.proxy.passing)
        plot.set_selected(self.selected_rows)
        self.plots.append(plot)
        self.range_timer.start()  # narrow the table to its view too
        return plot

    def _add_plot_pane(self):
        """Add a new plot beside the last one, showing a choice of plot types."""
        chooser = PlotTypeChooser(list(self.get_plot_types()))
        pane = Pane(chooser, "New plot")
        chooser.chosen.connect(lambda name: self._choose_plot(pane, name))
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
        return self.proxy.mapFromSource(self.model.index(row, 0))

    def _show_selection_card(self):
        if len(self.selected_rows) > 1:
            self.details.show_many(len(self.selected_rows))
        else:
            self.details.show_row(self.focus_row)

    def _update_count(self):
        shown = self.proxy.rowCount()
        self.status.emit(f"{shown} of {self.df.height} compounds shown")

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
        if not rows:
            if source is not None:
                self._update_count()  # back to the count once off the points/bars
        elif (
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
        self.selected_rows = {self.proxy.mapToSource(i).row() for i in indexes}

        current = self.table.selectionModel().currentIndex()
        current_row = (
            self.proxy.mapToSource(current).row() if current.isValid() else None
        )
        if current_row in self.selected_rows:
            self.focus_row = current_row
        elif self.selected_rows:
            self.focus_row = min(self.selected_rows)
        else:
            self.focus_row = None
        self._show_selection_card()

        self._refresh_selection_marks()
        if self.selected_rows:
            self.status.emit(f"{len(self.selected_rows)} compound(s) selected")

    def _refresh_selection_marks(self):
        for plot in self.plots:
            plot.set_selected(self.selected_rows)

    def _on_table_hover(self, index):
        self._on_rows_hovered({self.proxy.mapToSource(index).row()}, None)

    def eventFilter(self, watched, event):
        if watched is self.table.viewport() and event.type() == QEvent.Type.Leave:
            self._on_rows_hovered(set(), None)
        return super().eventFilter(watched, event)
