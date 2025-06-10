# --- DB Import into GUI 
from dbms.vcard_import import import_vcard
import sqlite3

DB_PATH = "dbms/contacts.db"

def get_items_from_db(category):
    """Fetch items from the database based on the selected category."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if category == "Persons":
        cursor.execute("SELECT fn FROM contact")
        results = [row[0] for row in cursor.fetchall()]
    elif category == "Groups":
        cursor.execute("SELECT title FROM groups")
        results = [row[0] for row in cursor.fetchall()]
    elif category == "Files":
        # Replace with your actual file-handling table/column logic if needed
        results = ["No file table defined"]  # Placeholder
    else:
        results = []

    conn.close()
    return results

# ---


import tkinter.filedialog as fd
import customtkinter as ctk
# --- Data Simulation (In a real app, this would come from a database/API) ---
# We'll use dictionaries to simulate different lists of items.
# mock_data = {
#    "Persons": ["Alice Smith", "Bob Johnson", "Charlie Brown", "Diana Prince", "Ethan Hunt"],
#    "Groups": ["Developers", "Designers", "Marketing", "HR", "Sales"],
#    "Files": ["document.pdf", "image.jpg", "report.xlsx", "presentation.pptx", "code.py"]
#}

# --- CategorySidebar Class (Leftmost Sidebar: Persons, Groups, Files) ---
class CategorySidebar(ctk.CTkFrame):
    def __init__(self, master, on_category_selected_callback, on_import_callback):
        super().__init__(master, width=150, corner_radius=0)
        self.grid(row=0, column=0, sticky="nswe")
        self.grid_columnconfigure(0, weight=1) # Allow buttons to expand horizontally

        self.on_category_selected_callback = on_category_selected_callback
        self.current_selection = ctk.StringVar(value="") # To track selected category
        self.on_import_callback = on_import_callback
        self.category_buttons = []
        categories = ["Persons", "Groups", "Files"]

        # Add a title label for the sidebar
        self.title_label = ctk.CTkLabel(self, text="Categories", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=5, pady=(10, 5), sticky="ew")

        # Create category selection buttons
        for i, category_text in enumerate(categories):
            button = ctk.CTkButton(
                self,
                text=category_text,
                command=lambda text=category_text: self._select_category(text),
                height=40,
                fg_color="transparent",
                hover_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
                text_color=ctk.ThemeManager.theme["CTkButton"]["text_color"]
            )
            button.grid(row=i + 1, column=0, padx=5, pady=2, sticky="ew") # +1 to account for title label
            self.category_buttons.append(button)
            # Add "Import vCard" button below category buttons
            self.import_button = ctk.CTkButton(
                self,
                text="Import vCard",
                command=self.on_import_callback
            )
            self.import_button.grid(row=len(categories) + 1, column=0, padx=5, pady=(10, 10), sticky="ew")


        # Set initial selection
        self._select_category(categories[0]) # Select the first category by default

    def _select_category(self, category_text):
        """Internal method to handle category selection and update appearance."""
        if self.current_selection.get() != category_text: # Only update if selection changed
            print(f"Category Selected: {category_text}")
            self.current_selection.set(category_text)
            self._update_button_appearance()
            self.on_category_selected_callback(category_text) # Notify the App class

    def _update_button_appearance(self):
        """Updates the background color of category buttons based on current_selection."""
        selected_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        deselected_color = "transparent"

        for button in self.category_buttons:
            if button.cget("text") == self.current_selection.get():
                button.configure(fg_color=selected_color)
            else:
                button.configure(fg_color=deselected_color)

# --- DetailSidebar Class (Second Sidebar: Lists items based on category) ---
class DetailSidebar(ctk.CTkFrame):
    def __init__(self, master, on_item_selected_callback):
        super().__init__(master, width=200, corner_radius=0)
        self.grid(row=0, column=1, sticky="nswe")
        self.grid_columnconfigure(0, weight=1) # Allow items to expand horizontally

        self.on_item_selected_callback = on_item_selected_callback
        self.current_category = None
        self.current_item_selection = ctk.StringVar(value="")

        self.item_buttons = []

        # Add a title label for the sidebar
        self.title_label = ctk.CTkLabel(self, text="Items", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=5, pady=(10, 5), sticky="ew")

        # Frame to hold scrollable items (optional but good practice for long lists)
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.grid(row=1, column=0, sticky="nswe", padx=5, pady=5)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Make scrollable frame expand vertically

        # Placeholder label
        self.placeholder_label = ctk.CTkLabel(self.scrollable_frame, text="Select a category...")
        self.placeholder_label.pack(expand=True)


    def update_content(self, category_name):
        """Updates the list of items based on the selected category."""
        if self.current_category == category_name: # No change needed if same category
            return

        self.current_category = category_name
        self.current_item_selection.set("") # Reset item selection when category changes

        # Clear existing buttons
        for button in self.item_buttons:
            button.destroy()
        self.item_buttons.clear()

        # Remove placeholder if present
        if self.placeholder_label:
            self.placeholder_label.destroy()
            self.placeholder_label = None

       # items = mock_data.get(category_name, [])
        items = get_items_from_db(category_name)


        if not items:
            self.placeholder_label = ctk.CTkLabel(self.scrollable_frame, text=f"No {category_name} found.")
            self.placeholder_label.pack(expand=True)
            self.on_item_selected_callback(self.current_category, None) # Notify App no item selected
            return

        for i, item_text in enumerate(items):
            button = ctk.CTkButton(
                self.scrollable_frame,
                text=item_text,
                command=lambda text=item_text: self._select_item(text),
                height=30,
                fg_color="transparent",
                hover_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
                text_color=ctk.ThemeManager.theme["CTkButton"]["text_color"]
            )
            button.pack(fill="x", padx=2, pady=1) # fill="x" makes it fill horizontal space
            self.item_buttons.append(button)

        # Automatically select the first item in the new category
        if items:
            self._select_item(items[0])
        else:
            self.on_item_selected_callback(self.current_category, None)


    def _select_item(self, item_text):
        """Internal method to handle item selection and update appearance."""
        print(f"Item Selected: {item_text} from {self.current_category}")
        self.current_item_selection.set(item_text)
        self._update_button_appearance()
        self.on_item_selected_callback(self.current_category, item_text) # Notify the App class

    def _update_button_appearance(self):
        """Updates the background color of item buttons based on current_item_selection."""
        selected_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        deselected_color = "transparent"

        for button in self.item_buttons:
            if button.cget("text") == self.current_item_selection.get():
                button.configure(fg_color=selected_color)
            else:
                button.configure(fg_color=deselected_color)

# --- MainContentFrame Class ---
class MainContentFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.grid(row=0, column=2, sticky="nswe")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.current_category = None
        self.current_item = None

        self.display_label = ctk.CTkLabel(self, text="Select an item to view details.", font=("Roboto", 24))
        self.display_label.pack(expand=True, padx=20, pady=20)

        # Your original button (can be integrated into specific content views later)
        self.my_button = ctk.CTkButton(self, text="Main Action Button", command=self._main_button_callback)
        self.my_button.pack(padx=20, pady=20, side="bottom")
        self.import_button = ctk.CTkButton(self, text="Import vCard", command=self.import_vcard_file)
        self.import_button.pack(padx=20, pady=(0, 20), side="bottom")


    def update_content(self, category, item=None):
        """Updates the content displayed based on category and item selection."""
        self.current_category = category
        self.current_item = item

        # Clear previous content if needed (excluding the main button)
        for widget in self.winfo_children():
            if widget not in [self.display_label, self.my_button]: # Keep label and main button
                widget.destroy()

        if item:
            self.display_label.configure(text=f"Viewing {item} from {category}!")
            # Add specific widgets based on category and item here
            if category == "Persons":
                # Example: Add a detailed view for a person
                detail_text = f"Details for {item}:\n\n- Age: XX\n- Email: {item.replace(' ', '.').lower()}@example.com\n- Role: {item.split(' ')[0]}!"
                info_label = ctk.CTkLabel(self, text=detail_text, font=("Roboto", 14), justify="left")
                info_label.pack(padx=20, pady=10, fill="x")
            elif category == "Files":
                # Example: Show file properties
                file_info = f"File: {item}\nType: {item.split('.')[-1].upper()}\nSize: 1.2MB"
                file_label = ctk.CTkLabel(self, text=file_info, font=("Roboto", 14), justify="left")
                file_label.pack(padx=20, pady=10, fill="x")

        elif category:
            self.display_label.configure(text=f"Select an item from {category} to view details.")
        else:
            self.display_label.configure(text="Select a category from the first sidebar.")

    def _main_button_callback(self):
        print(f"Main Action Button clicked. Current view: {self.current_category}, {self.current_item}")
        # Logic for the main button, might depend on current_category/current_item

    def import_vcard_file(self):
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            title="Select a vCard file",
            filetypes=[("vCard files", "*.vcf"), ("All files", "*.*")]
        )
        if file_path:
            try:
                import_vcard(file_path)
                print("vCard import successful.")
                self.master.detail_sidebar.update_content("Persons")
            except Exception as e:
                print(f"Error importing vCard: {e}")





# --- Main App Class ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize window
        self.title("Contact Box")
        window_size_factor = 0.6
        window_width = int(self.winfo_screenwidth() * window_size_factor)
        window_height = int(self.winfo_screenheight() * window_size_factor)
        self.geometry(f"{window_width}x{window_height}")
        self.minsize(700, 400)

        # Configure grid layout for the main window (1 row, 3 columns)
        self.grid_rowconfigure(0, weight=1) # Allow content area to expand vertically
        self.grid_columnconfigure(0, weight=0) # CategorySidebar fixed width
        self.grid_columnconfigure(1, weight=0) # DetailSidebar fixed width
        self.grid_columnconfigure(2, weight=1) # MainContentFrame expands horizontally

        # Instantiate sidebars and main content frame
        self.main_content_frame = MainContentFrame(self)
        self.detail_sidebar = DetailSidebar(self, self.on_item_selected)
        self.category_sidebar = CategorySidebar(self, self.on_category_selected, self.main_content_frame.import_vcard_file)


    def on_category_selected(self, category_name):
        """Callback from CategorySidebar when a category is selected."""
        self.detail_sidebar.update_content(category_name)
        # Update main content with a general message for the category
        self.main_content_frame.update_content(category_name)

    def on_item_selected(self, category_name, item_name):
        """Callback from DetailSidebar when an item is selected."""
        self.main_content_frame.update_content(category_name, item_name)

def launch():
    app = App()
    app.mainloop()
