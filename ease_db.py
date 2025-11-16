import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import webbrowser

# =========================================================================
# 1. Custom Dialog Classes
# =========================================================================
class AlterColumnDialog(simpledialog.Dialog):
    """Custom dialog to get new column name and type preference."""
    def __init__(self, parent, column_name):
        self.column_name = column_name
        self.new_name = None
        self.new_type = None
        self.type_var = tk.StringVar(parent)
        super().__init__(parent, title=f"Modify Column: {column_name}")

    def body(self, master):
        main_frame = ttk.Frame(master)
        main_frame.pack(padx=10, pady=10)
        
        ttk.Label(main_frame, text=f"Modifying column: **{self.column_name}**", font=('TkDefaultFont', 10, 'bold')).grid(row=0, columnspan=2, pady=5)
        
        ttk.Label(main_frame, text="New Name:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.name_entry = ttk.Entry(main_frame, width=30)
        self.name_entry.insert(0, self.column_name)
        self.name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(main_frame, text="New Type (Affinity):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        type_frame = ttk.Frame(main_frame)
        type_frame.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        self.type_var.set('TEXT') 

        ttk.Radiobutton(type_frame, text="TEXT", variable=self.type_var, value="TEXT").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="NUMBER", variable=self.type_var, value="NUMERIC").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(main_frame, text="(Note: SQLite type enforcement is flexible)", foreground='gray').grid(row=3, columnspan=2)

        return self.name_entry

    def apply(self):
        self.new_name = self.name_entry.get().strip()
        self.new_type = self.type_var.get()

class RenameTableDialog(simpledialog.Dialog):
    def __init__(self, parent, table_list):
        self.table_list = table_list
        self.old_name = None
        self.new_name = None
        self.selected_table_var = tk.StringVar(parent)
        super().__init__(parent, title="Rename Table")

    def body(self, master):
        main_frame = ttk.Frame(master)
        main_frame.pack(padx=10, pady=10)

        ttk.Label(main_frame, text="Select Table to Rename:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.table_selector = ttk.Combobox(
            main_frame, 
            textvariable=self.selected_table_var,
            values=self.table_list,
            state="readonly",
            width=30
        )
        if self.table_list:
             self.table_selector.set(self.table_list[0])
        self.table_selector.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(main_frame, text="New Table Name:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.name_entry = ttk.Entry(main_frame, width=30)
        self.name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        return self.table_selector

    def apply(self):
        self.old_name = self.selected_table_var.get()
        self.new_name = self.name_entry.get().strip()

# =========================================================================
# 2. Main Viewer/Editor Class
# =========================================================================
class SQLViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Ease-DB")

        # --- Variables ---
        self.conn = None
        self.filepath = None
        self.selected_table = tk.StringVar()

        # --- Menu Bar Setup ---
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Database", command=self.open_file)
        file_menu.add_command(label="Create New Database", command=self.create_db)
        file_menu.add_command(label="Add New Table", command=self.add_table)
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=lambda: self.save_file(False))
        file_menu.add_command(label="Save As...", command=lambda: self.save_file(True))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        
        # Edit Menu (Main Menu)
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        self._populate_edit_menu(edit_menu)

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About Ease-DB", command=self.show_about) # Updated method
        help_menu.add_command(label="Documentation", command=self.open_docs)

        # --- Control Frame ---
        control_frame = ttk.Frame(root)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Table Selector
        ttk.Label(control_frame, text="Select Table:").pack(side=tk.LEFT, padx=(0, 5))
        self.table_selector = ttk.Combobox(
            control_frame, 
            textvariable=self.selected_table,
            state="readonly",
            width=25
        )
        self.table_selector.pack(side=tk.LEFT, padx=(0, 10))
        self.table_selector.bind("<<ComboboxSelected>>", self.select_table)

        # Query Entry
        self.query_text = tk.Text(root, height=4)
        self.query_text.pack(fill=tk.X, padx=5, pady=5)

        run_button = tk.Button(root, text="Run Query", command=self.run_query)
        run_button.pack(pady=5)

        # --- Treeview Setup ---
        self.tree = ttk.Treeview(root, show="headings")
        self.tree.bind("<Double-1>", self.on_cell_double_click)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- Right-Click Context Menu Setup ---
        self.context_menu = tk.Menu(root, tearoff=0)
        self._populate_edit_menu(self.context_menu)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def _populate_edit_menu(self, menu):
        """Helper function to populate both the main Edit menu and the context menu."""
        menu.add_command(label="Add Column", command=lambda: self.add_structural_element('column'))
        menu.add_command(label="Modify Selected Column", command=self.show_alter_column_dialog)
        menu.add_command(label="Modify Table Name", command=self.show_rename_table_dialog)
        menu.add_separator()
        menu.add_command(label="Add Row", command=self.add_row)
        menu.add_command(label="Delete Row", command=self.delete_row)
        menu.add_command(label="Delete Column (Warning)", command=lambda: self.delete_structural_element('column'))
        menu.add_separator()
        
        menu.add_command(label="Copy Selected Cell", command=lambda: self.copy_data('cell'))
        menu.add_command(label="Copy Selected Row", command=lambda: self.copy_data('row'))
        menu.add_command(label="Copy Selected Column", command=lambda: self.copy_data('column'))

    def show_context_menu(self, event):
        """Displays the right-click menu at the cursor position."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    # =====================================================================
    # HELP OPERATIONS
    # =====================================================================
    def show_about(self):
        """Displays the 'About' message box with project and author info."""
        messagebox.showinfo(
            "About Ease-DB",
            "Ease-DB is an **open-source**, lightweight SQLite database editor built using Python's Tkinter.\n\n"
            "It provides essential CRUD (Create, Read, Update, Delete) functionality through a user-friendly "
            "graphical interface, making SQLite management accessible and efficient.\n\n"
            "Creator: Zrng\n"
            "GitHub: https://github.com/zrnge"
        )

    def open_docs(self):
        """Opens the documentation URL in the default web browser."""
        documentation_url = "https://github.com/zrnge/ease-db"
        webbrowser.open_new(documentation_url)

    # =====================================================================
    # FILE OPERATIONS
    # =====================================================================
    def open_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("SQLite DB", "*.db *.sqlite"), ("All Files", "*.*")]
        )
        
        if filepath:
            if self.conn: 
                try: self.conn.close() 
                except Exception: pass

            try:
                self.conn = sqlite3.connect(filepath)
                self.filepath = filepath
                messagebox.showinfo("Success", f"Opened database: {filepath}")
                self.populate_table_selector()
            except Exception as e:
                messagebox.showerror("Error", str(e))
                self.conn = None
                self.filepath = None
    
    def create_db(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        if filepath:
            if self.conn: self.conn.close()
            try:
                self.conn = sqlite3.connect(filepath)
                self.filepath = filepath
                messagebox.showinfo("Success", f"New database created: {filepath}")
                self.populate_table_selector()
                if messagebox.askyesno("Table Creation", "Do you want to create a default 'NewTable'?"):
                    self.conn.execute("CREATE TABLE NewTable (id INTEGER PRIMARY KEY, name TEXT, value TEXT)")
                    self.conn.commit()
                    self.populate_table_selector()
            except Exception as e:
                messagebox.showerror("Error", str(e))
                self.conn = None
                self.filepath = None
                
    def add_table(self):
        if not self.conn:
            messagebox.showwarning("No DB", "Open or create a database file first.")
            return

        table_name = simpledialog.askstring("Add Table", "Enter the name for the new table:")
        
        if table_name:
            if not table_name.isidentifier():
                messagebox.showerror("Error", "Invalid table name. Use alphanumeric characters and underscores.")
                return

            try:
                query = f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY, name TEXT);"
                self.conn.execute(query)
                self.conn.commit()
                messagebox.showinfo("Success", f"Table '{table_name}' created successfully.")
                self.populate_table_selector()
                self.selected_table.set(table_name)
                self.select_table(None)
            except Exception as e:
                messagebox.showerror("Creation Error", f"Failed to create table: {e}")

    def save_file(self, save_as=False):
        if not self.conn:
            messagebox.showwarning("No DB", "Open or create a database file first.")
            return

        target_path = self.filepath
        
        if save_as or not target_path:
            target_path = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[
                    ("SQLite Database", "*.db"), 
                    ("SQL Dump", "*.sql"),
                    ("All Files", "*.*")
                ]
            )
        
        if target_path:
            if target_path.lower().endswith('.sql'):
                try:
                    with open(target_path, 'w') as f:
                        for line in self.conn.iterdump():
                            f.write('%s\n' % line)
                    messagebox.showinfo("Success", f"Database saved to SQL file: {target_path}")
                except Exception as e:
                    messagebox.showerror("Save Error", f"Failed to save SQL dump: {e}")
            else:
                try:
                    self.conn.commit() 
                    self.filepath = target_path 
                    messagebox.showinfo("Success", f"Database saved to: {target_path}")
                except Exception as e:
                    messagebox.showerror("Save Error", f"Failed to save DB file: {e}")

    # =====================================================================
    # EDIT/STRUCTURE OPERATIONS
    # =====================================================================

    def get_table_list(self):
        if not self.conn:
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []

    def show_rename_table_dialog(self):
        if not self.conn:
            messagebox.showwarning("No DB", "Open a database file first.")
            return

        table_list = self.get_table_list()
        if not table_list:
            messagebox.showwarning("No Tables", "The current database contains no tables to rename.")
            return

        dialog = RenameTableDialog(self.root, table_list)

        if dialog.old_name and dialog.new_name:
            if dialog.old_name == dialog.new_name:
                messagebox.showinfo("No Change", "The new name is the same as the old name. No modification performed.")
                return

            if not dialog.new_name.isidentifier():
                messagebox.showerror("Error", "Invalid new table name. Use alphanumeric characters and underscores.")
                return
                
            self.rename_table(dialog.old_name, dialog.new_name)

    def rename_table(self, old_name, new_name):
        try:
            query = f"ALTER TABLE {old_name} RENAME TO {new_name};"
            self.conn.execute(query)
            self.conn.commit()
            
            messagebox.showinfo("Success", f"Table '{old_name}' successfully renamed to '{new_name}'.")
            
            self.populate_table_selector() 
            self.selected_table.set(new_name)
            self.select_table(None)
            
        except Exception as e:
            messagebox.showerror("Rename Error", f"Failed to rename table: {e}")


    def show_alter_column_dialog(self):
        if not self.conn or not self.selected_table.get():
            messagebox.showwarning("Warning", "Please select a table first.")
            return

        current_cols = self.tree["columns"]
        if not current_cols:
            messagebox.showwarning("Warning", "The current table has no columns to modify.")
            return

        col_to_modify = simpledialog.askstring(
            "Select Column", 
            f"Enter the exact name of the column to modify (e.g., {current_cols[0]}):"
        )

        if not col_to_modify or col_to_modify not in current_cols:
            messagebox.showwarning("Warning", "Invalid column name selected or cancelled.")
            return
            
        dialog = AlterColumnDialog(self.root, col_to_modify)

        if dialog.new_name and dialog.new_type:
            self.alter_column(col_to_modify, dialog.new_name, dialog.new_type)
            
    def alter_column(self, old_name, new_name, new_type):
        table_name = self.selected_table.get()
        
        if old_name != new_name:
            try:
                rename_query = f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name};"
                self.conn.execute(rename_query)
                self.conn.commit()
                messagebox.showinfo("Success", f"Column renamed from '{old_name}' to '{new_name}'.")
            except Exception as e:
                messagebox.showerror("Rename Error", f"Failed to rename column: {e}")
                return
        
        if new_type in ["NUMERIC", "TEXT"]:
            messagebox.showwarning(
                "Type Change Note", 
                f"Column **'{new_name}'** has been conceptually noted as **'{new_type}'**.\n\n"
                "SQLite is dynamically typed; it does not strictly enforce type changes via simple ALTER TABLE. "
                "For actual type definition, manual table recreation is needed."
            )
            
        self.select_table(None)
        
    def add_structural_element(self, element_type='column'):
        table_name = self.selected_table.get()
        if not self.conn or not table_name:
            messagebox.showwarning("Warning", "Please select a table first.")
            return

        if element_type == 'column':
            new_col_name = simpledialog.askstring("Add Column", "Enter new column name (e.g., new_col):")
            new_col_type = simpledialog.askstring("Add Column", "Enter column data type (e.g., TEXT, INTEGER):")
            
            if new_col_name and new_col_type:
                new_col_name = new_col_name.strip()
                new_col_type = new_col_type.strip().upper()
                try:
                    query = f"ALTER TABLE {table_name} ADD COLUMN {new_col_name} {new_col_type};"
                    self.conn.execute(query)
                    self.conn.commit()
                    messagebox.showinfo("Success", f"Column '{new_col_name}' added to {table_name}.")
                    self.select_table(None)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to add column: {e}")

    def delete_structural_element(self, element_type='column'):
        if element_type == 'column':
            messagebox.showerror("Error", "SQLite does not easily support dropping columns. You must use the SQL Query box to perform this complex operation manually (CREATE TEMP TABLE, INSERT data, DROP old table, RENAME new table).")
        
    def add_row(self):
        table_name = self.selected_table.get()
        if not self.conn or not table_name:
            messagebox.showwarning("Warning", "Please select a table first.")
            return
            
        try:
            cursor = self.conn.execute(f"PRAGMA table_info({table_name});")
            columns = [info[1] for info in cursor.fetchall()]
            
            placeholders = ', '.join(['NULL'] * len(columns))
            query = f"INSERT INTO {table_name} VALUES ({placeholders});"

            self.conn.execute(query)
            self.conn.commit()
            self.run_query()
        except Exception as e:
            messagebox.showerror("Row Add Error", f"Failed to add row: {e}")

    def delete_row(self):
        table_name = self.selected_table.get()
        selected_item = self.tree.selection()
        
        if not self.conn or not table_name or not selected_item:
            messagebox.showwarning("Warning", "Select a row and a table first.")
            return
            
        row_values = self.tree.item(selected_item[0], 'values')
        if not row_values: return
        
        cursor = self.conn.execute(f"PRAGMA table_info({table_name});")
        pk_info = [info for info in cursor.fetchall() if info[5] == 1]
        
        if not pk_info:
            messagebox.showerror("Error", "Table must have a Primary Key column to delete rows safely.")
            return
            
        pk_name = pk_info[0][1]
        pk_index = pk_info[0][0]
        pk_value = row_values[pk_index]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete row with {pk_name} = {pk_value}?"):
            try:
                query = f"DELETE FROM {table_name} WHERE {pk_name} = ?;"
                self.conn.execute(query, (pk_value,))
                self.conn.commit()
                self.tree.delete(selected_item[0])
                self.run_query()
            except Exception as e:
                messagebox.showerror("Delete Error", f"Failed to delete row: {e}")

    # =====================================================================
    # UI/UTILITY OPERATIONS
    # =====================================================================

    def on_cell_double_click(self, event):
        if not self.conn or not self.selected_table.get(): return

        item_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)
        if not item_id or not column_id: return

        col_index = int(column_id.replace('#', '')) - 1
        col_name = self.tree["columns"][col_index]

        bbox = self.tree.bbox(item_id, column_id)
        if not bbox: return
        x, y, width, height = bbox

        current_values = self.tree.item(item_id, 'values')
        old_value = current_values[col_index]

        pk_cursor = self.conn.execute(f"PRAGMA table_info({self.selected_table.get()});")
        pk_info = [info for info in pk_cursor.fetchall() if info[5] == 1]
        
        if not pk_info:
             messagebox.showerror("Error", "Cannot edit cell. Table must have a Primary Key.")
             return

        pk_name = pk_info[0][1]
        pk_index = pk_info[0][0]
        pk_value = current_values[pk_index]

        entry = ttk.Entry(self.tree, justify='left', width=width)
        entry.insert(0, old_value)
        entry.focus()
        entry.select_range(0, tk.END)

        def save_edit(event=None):
            new_value = entry.get()
            if new_value != str(old_value):
                try:
                    query = f"UPDATE {self.selected_table.get()} SET {col_name} = ? WHERE {pk_name} = ?;"
                    self.conn.execute(query, (new_value, pk_value))
                    self.conn.commit()
                    
                    new_values_list = list(current_values)
                    new_values_list[col_index] = new_value
                    self.tree.item(item_id, values=new_values_list)
                    
                except Exception as e:
                    messagebox.showerror("Update Error", f"Failed to update cell: {e}")

            entry.destroy()
        
        entry.bind('<Return>', save_edit)
        entry.bind('<FocusOut>', save_edit)
        
        entry.place(x=x, y=y, anchor='nw', width=width, height=height)

    def copy_data(self, scope):
        data_to_copy = ""
        
        if scope == 'row':
            selected_item = self.tree.focus()
            if selected_item:
                values = self.tree.item(selected_item, 'values')
                if values:
                    data_to_copy = '\t'.join(map(str, values))
                    
        elif scope == 'column':
            col_name = simpledialog.askstring("Copy Column", "Enter the exact name of the column to copy:")
            if col_name and col_name in self.tree["columns"]:
                col_index = list(self.tree["columns"]).index(col_name)
                all_rows = self.tree.get_children()
                column_data = [self.tree.item(row, 'values')[col_index] for row in all_rows]
                data_to_copy = '\n'.join(map(str, column_data))
        
        elif scope == 'cell':
             selected_item = self.tree.focus()
             if selected_item:
                 values = self.tree.item(selected_item, 'values')
                 if values:
                     data_to_copy = str(values[0])

        if data_to_copy:
            self.root.clipboard_clear()
            self.root.clipboard_append(data_to_copy)
            messagebox.showinfo("Copied", f"Copied {scope} data to clipboard.")
        else:
            messagebox.showwarning("Copy Error", f"Could not copy {scope}. Ensure data is loaded.")
            
    def populate_table_selector(self):
        if not self.conn: return
        try:
            tables = self.get_table_list()
            
            self.table_selector['values'] = tables
            if tables:
                if self.selected_table.get() not in tables:
                     self.table_selector.set(tables[0])
            else:
                 self.table_selector.set("")
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not list tables: {str(e)}")

    def select_table(self, event):
        table_name = self.selected_table.get()
        if table_name:
            self.query_text.delete("1.0", tk.END)
            self.query_text.insert("1.0", f"SELECT * FROM {table_name};")
            self.run_query()

    def run_query(self):
        if not self.conn:
            messagebox.showwarning("No DB", "Open a database file first.")
            return

        query = self.query_text.get("1.0", tk.END).strip()
        if not query: return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            
            if query.upper().startswith("SELECT"): 
                rows = cursor.fetchall()
                headers = [desc[0] for desc in cursor.description] if cursor.description else []
            
                self.tree.delete(*self.tree.get_children())
                self.tree["columns"] = headers
                for col in headers:
                    self.tree.heading(col, text=col)
                    self.tree.column(col, width=100, anchor=tk.W)

                for row in rows:
                    self.tree.insert("", tk.END, values=row)

            else:
                self.conn.commit()
                messagebox.showinfo("Success", f"Query executed successfully. Rows affected: {cursor.rowcount}")
                if query.upper().startswith(("CREATE", "DROP", "ALTER")):
                    self.populate_table_selector()
                self.select_table(None) 
                
        except Exception as e:
            messagebox.showerror("Query Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = SQLViewer(root)
    root.geometry("1000x700")
    root.mainloop()
