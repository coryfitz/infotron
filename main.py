from textual.app import App, ComposeResult
from textual.widgets import Button, DataTable, DirectoryTree, Footer, TextArea, Static
from textual.containers import Horizontal, Vertical
from textual import events
import sqlite3
import time
from ai import query_database

class QueryEditor(TextArea):
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

    def clear_text(self) -> None:
        """Clear all text in the editor."""
        self.text = ""

class AiEditor(Vertical):
    """A container with two text areas: one for LLM responses (top) and one for user input (bottom)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        """Create the two text areas."""
        yield TextArea(
            id="ai_response_area",
            read_only=True,
            show_line_numbers=False,
            text="AI responses will appear here..."
        )
        yield TextArea(
            id="ai_input_area", 
            language="sql"
        )

    def on_mount(self) -> None:
        """Set up the text areas after mounting."""
        response_area = self.query_one("#ai_response_area", TextArea)
        input_area = self.query_one("#ai_input_area", TextArea)
        
        # Make response area take up more space (read-only display)
        response_area.styles.height = "70%"
        input_area.styles.height = "30%"
        
        # Add borders and titles
        response_area.border_title = "AI Response"
        input_area.border_title = "Your Input"

    @property
    def text(self) -> str:
        """Get text from the input area (for compatibility with existing code)."""
        try:
            input_area = self.query_one("#ai_input_area", TextArea)
            return input_area.text
        except:
            return ""

    @text.setter 
    def text(self, value: str) -> None:
        """Set text in the input area (for compatibility with existing code)."""
        try:
            input_area = self.query_one("#ai_input_area", TextArea)
            input_area.text = value
        except:
            pass

    def clear_text(self) -> None:
        """Clear text in the input area."""
        try:
            input_area = self.query_one("#ai_input_area", TextArea)
            input_area.clear()
        except:
            pass

    def set_response(self, response: str) -> None:
        """Set the AI response text."""
        try:
            response_area = self.query_one("#ai_response_area", TextArea)
            response_area.text = response
        except:
            pass

    def get_input(self) -> str:
        """Get the user input text."""
        try:
            input_area = self.query_one("#ai_input_area", TextArea)
            return input_area.text
        except:
            return ""

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
        self.current_display_query = None  # Track exactly what query is currently displayed

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
            
            # Store the current query for refresh purposes
            if query.strip().upper().startswith('SELECT'):
                self.current_display_query = query
            
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
                if query_upper.startswith('CREATE TABLE'):
                    # For CREATE TABLE, show the new empty table structure
                    self.refresh_display_after_ddl()
                elif query_upper.startswith('DROP'):
                    # After DROP, show the default table or empty display
                    self.current_display_query = None
                    self.load_data_from_db()
                else:
                    # For INSERT/UPDATE/DELETE, refresh the current table view
                    self.refresh_current_table_view()
                    
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
    
    def refresh_current_table_view(self):
        """Refresh the current table view after DML operations."""
        if not self.current_display_query:
            self.load_data_from_db()
            return
            
        try:
            # Get fresh data
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute(self.current_display_query)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            # Force complete table rebuild
            self.clear(columns=True)  # Clear both data and columns
            self.add_columns(*columns)
            
            if rows:
                self.add_rows(rows)
            
            self.zebra_stripes = True
                
        except Exception as e:
            # Fallback - try to re-execute the same query through load_data_from_db
            try:
                self.load_data_from_db(self.current_display_query)
            except Exception as e2:
                # Last resort: clear everything and show error
                self.clear(columns=True)
                self.add_column("Error")
                self.add_row(f"Refresh failed: {str(e)}")
    
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
                self.current_display_query = query
                
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
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
    ]
    
    CSS = """
Screen {
    layout: grid;
    grid-size: 4 4;
    grid-columns: 1fr;
    grid-gutter: 1;
}

#sidebar {
    column-span: 1;
    row-span: 4;
    background: $surface;
    border: solid $primary;
    border-title-align: center;
    height: 100%;
}

#main_table {
    column-span: 3;
    row-span: 2;
    border: solid $primary;
    border-title-align: center;
    height: 100%;
}

#query_section {
    column-span: 3;
    row-span: 2;
    background: $surface;
    border: solid $secondary;
    border-title-align: center;
}

#query_section > Horizontal {
    align: left top;
}

#current_editor {
    height: 2fr;
}

#ai_response_area {
    border-title-color: white;
}

#ai_input_area {
    border-title-color: white;
}

#execute_btn {
    height: 1;
    width: 10;
    margin: 0 1;
    text-align: center;
    text-style: bold;
}

#clear_btn {
    height: 1;
    width: 10;
    margin: 0 1;
    text-align: center;
    text-style: bold;
}

#toggle_btn {
    height: 1;
    width: 10;
    margin: 0 1;
    text-align: center;
    text-style: bold;
    dock: right;
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_ai_mode = False  # Track current mode
        self.query_editor_text = ""  # Store SQL editor content
        self.ai_input_text = ""  # Store AI input content

    def compose(self) -> ComposeResult:
        yield Explorer(id='sidebar')
        yield DisplayTable(id='main_table')
        
        # Create a container for the query editor and button
        with Vertical(id='query_section') as query_section:
            query_section.border_title = 'Query Editor'
            with Horizontal():
                yield Static("▶ Execute", id='execute_btn', classes="clickable")
                yield Static("▶ Clear", id='clear_btn', classes="clickable")
                yield Static("▶ AI", id='toggle_btn', classes="clickable")
            yield QueryEditor(id='current_editor')
            
        yield AppFooter()

    async def toggle_editor_mode(self) -> None:
        """Toggle between Query Editor and AI Editor modes."""
        query_section = self.query_one("#query_section", Vertical)
        current_editor = self.query_one("#current_editor")
        toggle_btn = self.query_one("#toggle_btn", Static)
        
        # Store current text before switching
        if self.is_ai_mode:
            # Coming from AI mode, save AI input text
            self.ai_input_text = current_editor.text
        else:
            # Coming from Query mode, save query text
            self.query_editor_text = current_editor.text
        
        # Remove current editor and wait for it to complete
        await current_editor.remove()
        
        if self.is_ai_mode:
            # Switch back to Query Editor
            new_editor = QueryEditor(id='current_editor')
            query_section.border_title = 'Query Editor'
            toggle_btn.update("▶ AI")
            self.is_ai_mode = False
            # Restore query editor text
            new_editor.text = self.query_editor_text
        else:
            # Switch to AI Editor
            new_editor = AiEditor(id='current_editor')
            query_section.border_title = 'AI Editor'
            toggle_btn.update("▶ SQL")
            self.is_ai_mode = True
            # Restore AI input text (but only if it's not the placeholder)
            if self.ai_input_text and self.ai_input_text != "Enter your prompt here...":
                new_editor.text = self.ai_input_text
            else:
                # Clear the placeholder text when switching to AI mode
                new_editor.text = ""
        
        # Add new editor
        query_section.mount(new_editor)

    def action_execute_query(self) -> None:
        """Execute the SQL query or AI query depending on current mode."""
        current_editor = self.query_one("#current_editor")
        
        if self.is_ai_mode:
            # AI mode - use natural language query
            user_input = current_editor.text.strip()
            if user_input:
                try:
                    # Query the database using AI
                    #current_editor.set_response(user_input)
                    result = query_database(user_input)
                    current_editor.set_response(str(result))
                    
                    """

                    if result['success']:
                        # Display the AI response
                        response_text = result['answer']
                        if result['sql_query']:
                            response_text += f"\n\n--- Generated SQL ---\n{result['sql_query']}"
                        
                        current_editor.set_response(response_text)
                        
                        # Optionally, if there's a SQL query, execute it to show results in the table
                        if result['sql_query']:
                            data_table = self.query_one("#main_table", DisplayTable)
                            data_table.execute_query(result['sql_query'])
                    else:
                        # Display error message
                        current_editor.set_response(result['answer'])

                    """
                        
                except Exception as e:
                    current_editor.set_response(f"Error processing AI query: {str(e)}")
        else:
            # SQL mode - execute SQL directly
            data_table = self.query_one("#main_table", DisplayTable)
            query = current_editor.text.strip()
            if query:
                data_table.execute_query(query)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "execute_btn":
            self.action_execute_query()

    async def on_click(self, event: events.Click) -> None:
        """Handle click events on clickable elements."""
        if event.widget.id == "execute_btn":
            self.action_execute_query()
        elif event.widget.id == "clear_btn":
            current_editor = self.query_one("#current_editor")
            current_editor.clear_text()
        elif event.widget.id == "toggle_btn":
            await self.toggle_editor_mode()

if __name__ == "__main__":
    app = InfotronApp()
    app.run()