from textual.app import App, ComposeResult
from textual.widgets import Button, DataTable, DirectoryTree, Footer, TextArea, Static
from textual.containers import Horizontal, Vertical
from textual import events
import sqlite3
import time

class CodeEditor(TextArea):
    """A subclass of TextArea with parenthesis-closing functionality and double-click selection."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.language = "sql"
        self.last_click_time = 0
        self.double_click_threshold = 0.5  # 500ms threshold for double-click

    def on_key(self, event: events.Key) -> None:
        if event.character == "(":
            self.insert("()")
            self.move_cursor_relative(columns=-1)
            event.prevent_default()

    def on_click(self, event: events.Click) -> None:
        """Handle click events to detect double-clicks."""
        current_time = time.time()
        
        # Check if this is a double-click
        if current_time - self.last_click_time < self.double_click_threshold:
            # Double-click detected - select all text
            self.select_all()
            event.prevent_default()
        
        self.last_click_time = current_time

class Explorer(DirectoryTree):

    def __init__(self, **kwargs):
        conn = sqlite3.connect('database/database.db')
        conn.close()
        directory = "./database"
        super().__init__(directory, **kwargs)
        self.border_title = 'Explorer'

class DisplayTable(DataTable):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.database_path = 'database/database.db'

    def load_data_from_db(self, query: str = None):
        """Load data from SQLite database and populate the table."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            if query is None:
                # Get the first table from the database
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                if tables:
                    table_name = tables[0][0]
                    query = f"SELECT * FROM {table_name}"
                else:
                    # No tables found, show empty table
                    conn.close()
                    return
            
            cursor.execute(query)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            self.clear()
            self.add_columns(*columns)
            
            # Add rows if they exist, otherwise just show empty table with column headers
            if rows:
                self.add_rows(rows)
            
            self.zebra_stripes = True
            
        except sqlite3.Error as e:
            self.clear()
            self.add_columns("Error")
            self.add_rows([(f"Database error: {str(e)}",)])
        except Exception as e:
            self.clear()
            self.add_columns("Error")
            self.add_rows([(f"Error: {str(e)}",)])

    def execute_query(self, query: str):
        """Execute a custom SQL query and update the table."""
        query_upper = query.strip().upper()
        
        # Check if it's a DDL statement (CREATE, DROP, ALTER) or DML that doesn't return data
        if (query_upper.startswith('CREATE') or 
            query_upper.startswith('DROP') or 
            query_upper.startswith('ALTER') or
            query_upper.startswith('INSERT') or
            query_upper.startswith('UPDATE') or
            query_upper.startswith('DELETE')):
            
            # Execute the statement
            try:
                conn = sqlite3.connect(self.database_path)
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
                conn.close()
                
                # After successful execution, refresh the table display
                # For CREATE TABLE, show the new empty table structure
                if query_upper.startswith('CREATE TABLE'):
                    # Extract table name and show its structure
                    self.refresh_display_after_ddl()
                elif query_upper.startswith('DROP'):
                    # After DROP, show the default table or empty display
                    self.load_data_from_db()
                else:
                    # For INSERT/UPDATE/DELETE, refresh the current table view
                    self.load_data_from_db()
                    
            except sqlite3.Error as e:
                self.clear()
                self.add_columns("Error")
                self.add_rows([(f"Database error: {str(e)}",)])
            except Exception as e:
                self.clear()
                self.add_columns("Error")
                self.add_rows([(f"Error: {str(e)}",)])
        else:
            # For SELECT queries, load data normally
            self.load_data_from_db(query)
    
    def refresh_display_after_ddl(self):
        """Refresh the display after DDL operations like CREATE TABLE."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get the most recently created table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            tables = cursor.fetchall()
            
            if tables:
                # Show the last table (most recently created)
                table_name = tables[-1][0]
                query = f"SELECT * FROM {table_name}"
                cursor.execute(query)
                columns = [description[0] for description in cursor.description]
                
                self.clear()
                self.add_columns(*columns)
                # Don't add any rows - just show the empty table structure
                self.zebra_stripes = True
            
            conn.close()
            
        except Exception as e:
            # Fallback to default display
            self.load_data_from_db()

    def on_mount(self) -> None:
        self.border_title = 'Data Table'
        # Load data on mount
        self.load_data_from_db()

class AppFooter(Footer):
    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

class InfotronApp(App):
    """A Textual app using CSS Grid for layout."""

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+r", "execute_query", "Execute query"),
        ("ctrl+a", "select_all_in_editor", "Select all in query editor")
    ]
    
    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 3;
        grid-columns: 1fr;
        grid-gutter: 1;
    }
    
    #sidebar {
        column-span: 1;
        row-span: 3;
        background: $surface;
        border: solid $primary;
        border-title-align: center;
        height: 100%;
    }
    
    #main_table {
        column-span: 2;
        row-span: 2;
        border: solid $primary;
        border-title-align: center;
        height: 100%;
    }
    
    #query_section {
        column-span: 2;
        row-span: 1;
        background: $surface;
        border: solid $secondary;
        border-title-align: center;
    }
    
    #query_editor {
        height: 2fr;
    }
    
    #execute_btn {
        height: 1;
        width: 10;
        margin: 0 1;
        text-align: center;
        text-style: bold;
    }
    
    .clickable:hover {
        background: $primary-darken-1;
        text-style: bold;
    }
    
    Footer {
        column-span: 2;
        row-span: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Explorer(id='sidebar')
        yield DisplayTable(id='main_table')
        
        # Create a container for the query editor and button
        with Vertical(id='query_section') as query_section:
            query_section.border_title = 'Query Editor'
            with Horizontal():
                yield Static("▶ Execute", id='execute_btn', classes="clickable")
            yield CodeEditor(id='query_editor')
            
        yield AppFooter()

    def action_execute_query(self) -> None:
        """Execute the SQL query from the editor."""
        query_editor = self.query_one("#query_editor", CodeEditor)
        data_table = self.query_one("#main_table", DisplayTable)
        
        query = query_editor.text.strip()
        if query:
            data_table.execute_query(query)

    def action_select_all_in_editor(self) -> None:
        """Select all text in the query editor."""
        query_editor = self.query_one("#query_editor", CodeEditor)
        query_editor.select_all()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "execute_btn":
            self.action_execute_query()

    def on_click(self, event: events.Click) -> None:
        """Handle click events on clickable elements."""
        if event.widget.id == "execute_btn":
            self.action_execute_query()

if __name__ == "__main__":
    app = InfotronApp()
    app.run()