from textual.app import App, ComposeResult
from textual.widgets import Footer
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header
from textual.binding import Binding
from rich.text import Text
from itertools import cycle

class InfotronApp(App):
    """A Textual app to manage stopwatches."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    
    CSS = """
    DataTable {
        height: 1fr;
        margin: 1;
    }
    """
    
    ROWS = [
        ("Lane", "Swimmer", "Country", "Time"),
        (4, "Joseph Schooling", "Singapore", 50.39),
        (2, "Michael Phelps", "United States", 51.14),
        (5, "Chad le Clos", "South Africa", 51.14),
        (6, "László Cseh", "Hungary", 51.14),
        (3, "Li Zhuhao", "China", 51.26),
        (8, "Mehdy Metella", "France", 51.58),
        (7, "Tom Shields", "United States", 51.73),
        (1, "Aleksandr Sadovnikov", "Russia", 51.84),
        (10, "Darren Burns", "Scotland", 51.84),
    ]

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*self.ROWS[0])
        table.add_rows(self.ROWS[1:])
        table.zebra_stripes = True

    def compose(self) -> ComposeResult:
        yield DataTable()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = InfotronApp()
    app.run()