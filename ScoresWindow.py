from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView

class ScoresWindow(QDialog):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db

        self.setWindowTitle("High Scores")
        self.setFixedSize(220, 360)

        title = QLabel("Top 10 Scores", self)
        title.setGeometry(40, 10, 200, 25)

        self.table = QTableWidget(self) # create table for scores
        self.table.setGeometry(10, 40, 200, 270)
        self.table.setColumnCount(2) # two columns: Player, Score
        self.table.setHorizontalHeaderLabels(["Player", "Score"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.close_btn = QPushButton("Close", self)
        self.close_btn.setGeometry(110, 320, 100, 30)
        self.close_btn.clicked.connect(self.close)

        self.load_scores() # load scores into table

    def load_scores(self):
        rows = self.db.get_top_scores(10) if self.db else [] # fetch top 10 scores
        self.table.setRowCount(len(rows)) # set number of rows
        for r, (player, score) in enumerate(rows): 
            self.table.setItem(r, 0, QTableWidgetItem(str(player))) # set player name
            self.table.setItem(r, 1, QTableWidgetItem(str(score))) # set score
        header = self.table.horizontalHeader() # adjust column widths
        header.setSectionResizeMode(QHeaderView.Stretch) # stretch columns to fit