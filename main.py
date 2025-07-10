from textual.app import App, ComposeResult
from textual.widgets import Footer, DataTable, Static
from textual.containers import Grid
from textual import events
from textual.app import App, ComposeResult
from textual.widgets import TextArea


class CodeEditor(TextArea):
    """A subclass of TextArea with parenthesis-closing functionality."""

    def _on_key(self, event: events.Key) -> None:
        if event.character == "(":
            self.insert("()")
            self.move_cursor_relative(columns=-1)
            event.prevent_default()

    def compose(self) -> ComposeResult:
        editor = TextArea.code_editor(language="sql", id="bottom_section")
        editor.border_title = 'Query Editor'
        yield editor

class Sidebar(Static):

    def compose(self) -> ComposeResult:
        static = Static(
                "📊 Statistics\n🔍 Search\n⚙️ Settings\n📋 Actions\n\nThis sidebar takes up the full height of the screen.", 
                id="sidebar"
            )
        static.border_title = 'Static'
        yield static

class DisplayTable(DataTable):

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
        # Use self directly since this class IS a DataTable
        self.add_columns(*self.ROWS[0])
        self.add_rows(self.ROWS[1:])
        self.zebra_stripes = True
        self.border_title = 'Data Table'


class InfotronApp(App):
    """A Textual app using CSS Grid for layout."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    
    CSS = """
    Grid {
        grid-size: 3 2;
        grid-gutter: 1;
        grid-rows: 3fr 1fr;
        grid-columns: 1fr 2fr;
        height: 1fr;
    }
    
    #sidebar {
        column-span: 1;
        row-span: 3;
        background: $surface;
        border: solid $primary;
        border-title-align: center;
        padding: 1;
    }
    
    #main_table {
        column-span: 2;
        row-span: 1;
        border: solid $primary;
        border-title-align: center;
    }
    
    #bottom_section {
        column-span: 3;
        row-span: 1;
        background: $surface;
        border: solid $secondary;
        border-title-align: center;
        padding: 1;
    }

    """

    def compose(self) -> ComposeResult:

        yield Grid(
            Sidebar(),
            DisplayTable(id="main_table"),
            CodeEditor(),
        )
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = InfotronApp()
    app.run()