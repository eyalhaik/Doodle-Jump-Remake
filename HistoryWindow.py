from datetime import datetime

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import csv


class HistoryWindow(QDialog):
    MODE_PROGRESS = "progress" # score over time
    MODE_COMPARE = "compare" # compare top players

    def __init__(self, parent=None, db=None, player_name=None):
        super().__init__(parent)
        self.db = db
        self.player_name = player_name
        self.current_mode = self.MODE_PROGRESS # default mode

        self.setWindowTitle("History")
        self.setFixedSize(700, 340)

        # Title
        self.title = QLabel(f"History for: {player_name}", self)
        self.title.setGeometry(10, 10, 300, 22)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title.setFont(title_font)

        # Table
        self.table = QTableWidget(self)
        self.table.setGeometry(15, 30, 200, 250)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Score", "Date"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers) # make table read-only

        table_font = QFont()
        table_font.setPointSize(10)
        self.table.setFont(table_font)

        self.table.verticalHeader().setDefaultSectionSize(20) # set row height

        self.table.setColumnWidth(0, 70)    # Score width
        self.table.setColumnWidth(1, 100)   # Date width
        self.table.horizontalHeader().setStretchLastSection(True) # stretch date column to fill remaining

        # Graph
        self.fig = Figure(figsize=(3.8, 2.4), dpi=100) # create figure for plotting in inches and dots per inch
        self.ax = self.fig.add_subplot(111) # create axes for plotting

        self.canvas = FigureCanvas(self.fig) # create canvas to display the figure on the PySide6 window
        self.canvas.setParent(self) # set parent to this dialog so it shows up in the window
        self.canvas.setGeometry(230, 30, 450, 250)
        self.canvas.show()

        self.fig.subplots_adjust(left=0.15, right=0.95, bottom=0.28, top=0.88) # adjust subplot to fit within the figure area with specified margins

        # Buttons
        self.export_btn = QPushButton("Export CSV", self)
        self.export_btn.setGeometry(15, 300, 140, 26)
        self.export_btn.clicked.connect(self.export_to_csv)

        self.toggle_btn = QPushButton("Compare Players", self)
        self.toggle_btn.setGeometry(200, 300, 140, 26)
        self.toggle_btn.clicked.connect(self.toggle_graph_mode)

        self.close_btn = QPushButton("Close", self)
        self.close_btn.setGeometry(600, 300, 90, 26)
        self.close_btn.clicked.connect(self.close)

        self.load_history()
        self.show_progress_graph()  # default

    def format_date(self, date_str): # make date string nice for display
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%d/%m %H:%M:%S")
        except Exception:
            return str(date_str)

    def load_history(self):
        rows = self.db.get_player_scores(self.player_name) if self.db else [] # fetch scores for player
        self.history_rows = rows # store for export

        self.table.setRowCount(len(rows)) # set number of rows
        for r, (score, date_str) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(score))) # score
            self.table.setItem(r, 1, QTableWidgetItem(self.format_date(date_str))) # date

    def style_axes(self, title, xlabel, ylabel): # style graph axes
        self.ax.set_title(title, fontsize=10, pad=6) # set graph title with spacing from top
        self.ax.set_xlabel(xlabel, fontsize=9, labelpad=6) # set x-axis label with spacing from axis
        self.ax.set_ylabel(ylabel, fontsize=9, labelpad=6) # set y-axis label with spacing from axis
        self.ax.tick_params(axis="both", labelsize=8) # set tick label size for both axes

    def show_progress_graph(self):
        self.ax.clear()

        if not self.db or not self.player_name:
            self.canvas.draw()
            return

        rows = self.db.get_player_scores(self.player_name) # fetch scores for player
        data = []
        for score, date_str in rows:
            try:
                data.append((datetime.fromisoformat(date_str), int(score)))
            except Exception:
                pass

        if len(data) < 2:
            self.style_axes("Score over Time", "Date", "Score") # set axes even if no data
            self.ax.text(
                0.5, 0.5, "Not enough data",
                ha="center", va="center",
                transform=self.ax.transAxes
            ) # show message if not enough data to plot in the center of the graph area
            self.canvas.draw()
            return

        data.sort(key=lambda x: x[0]) # sort by date from oldest to newest date
        x, y = zip(*data) # merge into x (dates) and y (scores)

        self.ax.plot(x, y, marker="o", linewidth=1, color = "#0ea860")
        self.style_axes("Score over Time", "Date", "Score")

        for lbl in self.ax.get_xticklabels():
            lbl.set_rotation(30) # rotate x-axis labels for better readability
            lbl.set_ha("right") # align x-axis labels to the right for better readability when rotated

        self.canvas.draw()

    def show_compare_graph(self):
        self.ax.clear()

        if not self.db:
            self.canvas.draw()
            return

        top = self.db.get_top_scores(10)
        if not top:
            QMessageBox.information(self, "No data", "No scores available yet.")
            self.canvas.draw()
            return

        players, scores, seen = [], [], set() # track unique players
        for player, score in top:
            if player in seen:
                continue
            seen.add(player) # avoid duplicates
            players.append(player) # player names
            scores.append(int(score)) # scores

        self.ax.scatter(players, scores, color="#690a65")
        self.style_axes("Players Comparison", "Player", "Best Score")

        self.canvas.draw()

    def toggle_graph_mode(self):
        if self.current_mode == self.MODE_PROGRESS: # switch to compare mode
            self.current_mode = self.MODE_COMPARE
            self.toggle_btn.setText("Score over Time")
            self.show_compare_graph()
        else:
            self.current_mode = self.MODE_PROGRESS # switch to progress mode
            self.toggle_btn.setText("Compare Players")
            self.show_progress_graph()

    def export_to_csv(self):
        if not getattr(self, "history_rows", None): # no data to export
            QMessageBox.information(self, "No data", "No history to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV",
            f"history_{self.player_name}.csv" if self.player_name else "history.csv",
            "CSV Files (*.csv)"
        ) # ask user for file path
        if not path:
            return # user cancelled

        if not path.lower().endswith(".csv"):
            path += ".csv" # ensure .csv extension

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f: # avoid jibrish in Excel in case of hebrew names and ensure there are no extra blank lines in Windows
                writer = csv.writer(f) # create CSV writer
                writer.writerow(["Score", "Date"]) # write header
                for score, date_str in self.history_rows:
                    writer.writerow([int(score), self.format_date(date_str)]) # write score and formatted date

            QMessageBox.information(self, "Exported", "CSV file saved.") # inform user of success
        except Exception as e:
            QMessageBox.critical(self, "Export failed", f"Could not save CSV file:\n{e}") # inform user of failure with error message