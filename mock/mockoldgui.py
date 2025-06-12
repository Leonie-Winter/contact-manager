import customtkinter as ctk
import tkinter as tk
from collections import OrderedDict # To preserve the order of attributes
from dbms.vcard_import import import_vcard
from dbms import dbms


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
        self._categories = ["Persons", "Groups", "Files"]

        # Add a title label for the sidebar
        self.title_label = ctk.CTkLabel(self, text="Categories", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=5, pady=(10, 5), sticky="ew")

        # Create category selection buttons
        for i, category_text in enumerate(self._categories):
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
            self.import_button.grid(row=len(self._categories) + 1, column=0, padx=5, pady=(10, 10), sticky="ew")


        # Set initial selection
        self._select_category(self._categories[0]) # Select the first category by default

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

class ActionBar(ctk.CTkFrame):
    def __init__(self, master, on_refresh_callback=None):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.grid(row=0, column=3, sticky="ew")

        self.on_refresh_callback = on_refresh_callback

        button_width = 50  # Adjust as needed

        # Add Add Button
        self.add_button = ctk.CTkButton(self, text="Add", command=self._add_action, width=button_width)
        self.add_button.grid(row=0, column=0, padx=1, pady=1)
        # Add Edit Button
        self.edit_button = ctk.CTkButton(self, text="Edit", command=self._edit_action, width=button_width)
        self.edit_button.grid(row=0, column=1, padx=1, pady=1)
        # Add Delete Button
        self.delete_button = ctk.CTkButton(self, text="Delete", command=self._delete_action, width=button_width)
        self.delete_button.grid(row=0, column=2, padx=1, pady=1)
        # Add Refresh Button
        self.refresh_button = ctk.CTkButton(self, text="Refresh", command=self._refresh_action, width=button_width)
        self.refresh_button.grid(row=0, column=3, padx=1, pady=1)

    def _add_action(self):
        print("Add action triggered.")
        
        # Create Window
        add_window = ExternalWindow(self.master, mode="Add", category=self.master.current_category)
        add_window.grab_set()


    def _edit_action(self):
        print("Edit action triggered.")
        
        # Create Window
        add_window = ExternalWindow(self.master, mode="Edit", category=self.master.current_category)
        add_window.grab_set()

    def _delete_action(self):
        print("Delete action triggered.")
        # Here you might want to implement a confirmation dialog before deletion
        # For example, you could use a messagebox to confirm deletion
        if tk.messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?"):
            print("Item deleted.")
            # Implement deletion logic here, e.g., remove from database or list

    def _refresh_action(self):
        print("Refresh action triggered.")
        self.on_refresh_callback()


class DetailSidebar(ctk.CTkFrame):
    def __init__(self, master, on_item_selected_callback):
        super().__init__(master, width=200, corner_radius=0)
        self.grid(row=0, column=1, sticky="nswe")
        self.grid_columnconfigure(0, weight=1) # Allow items to expand horizontally

        self.on_item_selected_callback = on_item_selected_callback
        self.current_category = None
        self.current_item_selection = ctk.IntVar(value=0)

        self.item_buttons = []

        # Add a title label for the sidebar
        self.title_label = ctk.CTkLabel(self, text="Items", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=5, pady=(10, 5), sticky="ew")

        # Add Action Bar (now in row=1)
        self.action_bar = ActionBar(self, on_refresh_callback=lambda: self.update_content(self.current_category, force_update=True))
        self.action_bar.grid(row=1, column=0, padx=5, pady=(5, 0), sticky="ew")

        # Frame to hold scrollable items (now in row=2)
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.grid(row=2, column=0, sticky="nswe", padx=5, pady=5)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Make scrollable frame expand vertically

        # Placeholder label
        self.placeholder_label = ctk.CTkLabel(self.scrollable_frame, text="Select a category...")
        self.placeholder_label.pack(expand=True)


    def update_content(self, category_name, force_update=False):
        """Updates the list of items based on the selected category."""
        if self.current_category == category_name: # No change needed if same category
            return

        self.current_category = category_name
        self.current_item_selection.set(0) # Reset item selection when category changes

        # Clear existing buttons
        for button in self.item_buttons:
            button.destroy()
        self.item_buttons.clear()

        # Remove placeholder if present
        if self.placeholder_label:
            self.placeholder_label.destroy()
            self.placeholder_label = None

        items = OrderedDict(dbms.get_all_items_ids_and_names(category_name))

        # If no items found, display placeholder message
        if not items:
            self.placeholder_label = ctk.CTkLabel(self.scrollable_frame, text=f"No {category_name} found.")
            self.placeholder_label.pack(expand=True)
            self.on_item_selected_callback(self.current_category, None) # Notify App no item selected
            return

        # Create buttons for each item in the selected category
        for item_id, item_text in items.items():
            button = ctk.CTkButton(
                self.scrollable_frame,
                text=item_text,
                command=lambda id=item_id: self._select_item(id),
                height=30,
                fg_color="transparent",
                hover_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
                text_color=ctk.ThemeManager.theme["CTkButton"]["text_color"]
            )
            button.item_id = item_id  # Store item_id in button for reference
            button.pack(fill="x", padx=2, pady=1) # fill="x" makes it fill horizontal space
            self.item_buttons.append(button)

        # Automatically select the first item in the new category
        if items:
            # Select the first item by default
            first_item_id = next(iter(items))
            self._select_item(first_item_id)
        else:
            self.on_item_selected_callback(self.current_category, None)


    def _select_item(self, item_id):
        """Internal method to handle item selection and update appearance."""
        print(f"Item Selected: {item_id} from {self.current_category}")
        self.current_item_selection.set(item_id)
        self._update_button_appearance()
        self.on_item_selected_callback(self.current_category, item_id) # Notify the App class

    def _update_button_appearance(self):
        """Updates the background color of item buttons based on current_item_selection."""
        selected_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        deselected_color = "transparent"

        for button in self.item_buttons:
            if getattr(button, "item_id") == self.current_item_selection.get():
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


    def update_content(self, category, item_id=0):
        """Updates the content displayed based on category and item selection."""
        self.current_category = category
        self.current_item = dbms.get_item_data(category, item_id)

        # Clear previous content if needed (excluding the main button)
        for widget in self.winfo_children():
            if widget not in [self.display_label, self.my_button]: # Keep label and main button
                widget.destroy()

        if self.current_item:
            # self.display_label.configure(text=f"Viewing {self.current_item} from {category}!")
            # # Add specific widgets based on category and item here
            # if category == "Persons":
            #     # Example: Add a detailed view for a person
            #     detail_text = f"Details for {self.current_item}:\n\n- Age: XX\n- Email: {self.current_item.replace(' ', '.').lower()}@example.com\n- Role: {self.current_item.split(' ')[0]}!"
            #     info_label = ctk.CTkLabel(self, text=detail_text, font=("Roboto", 14), justify="left")
            #     info_label.pack(padx=20, pady=10, fill="x")
            # elif category == "Files":
            #     # Example: Show file properties
            #     file_info = f"File: {self.current_item}\nType: {self.current_item.split('.')[-1].upper()}\nSize: 1.2MB"
            #     file_label = ctk.CTkLabel(self, text=file_info, font=("Roboto", 14), justify="left")
            #     file_label.pack(padx=20, pady=10, fill="x")
            pass

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


# --- ExternalWindow Class ---
class ExternalWindow(ctk.CTkToplevel):
    """
    A CustomTkinter Toplevel window for adding new persons/groups or editing existing ones.
    It dynamically generates input fields based on the attributes of the selected category.
    All attribute fields are placed within a scrollable frame.
    """
    def __init__(self, master, mode="Add", category=None, item_id=None):
        """
        Initializes the ExternalWindow.

        Args:
            master (ctk.CTk): The parent CustomTkinter window.
            mode (str): The operation mode: "Add" for creating a new item,
                        "Edit" for modifying an existing one.
            category (str): The type of item being handled (e.g., "persons", "groups").
            item_id (int, optional): The ID of the item if in "Edit" mode. Defaults to None.
        """
        super().__init__(master)

        self.mode = mode
        self.category = category
        self.item_id = item_id # Store the item ID for edit operations

        # --- Configure Window Properties ---
        # Set window title based on mode and category
        # Removes 's' from category name (e.g., "persons" -> "person")
        title_category = category[:-1] if category and category.endswith('s') else category
        if self.mode == "Add":
            self.title(f"Add New {title_category.capitalize()}")
        else: # Edit mode
            self.title(f"Edit {title_category.capitalize()}")

        # Calculate and set window size based on screen dimensions
        window_size_factor = 0.45 # Factor to determine window size relative to screen
        window_width = int(self.winfo_screenwidth() * window_size_factor)
        window_height = int(self.winfo_screenheight() * window_size_factor)
        self.geometry(f"{window_width}x{window_height}")
        self.minsize(450, 400) # Minimum size for the window

        # Configure main window grid layout to allow content to expand
        self.grid_rowconfigure(0, weight=1)    # Allows the scrollable frame to expand vertically
        self.grid_columnconfigure(0, weight=1) # Allows content to expand horizontally

        # --- Attribute Display Name Mapping ---
        # This dictionary maps internal database column names to user-friendly labels.
        self.attribute_display_names = {
            "fn": "First Name",
            "n": "Last Name",
            "nickname": "Nickname",
            "photo": "Photo (Base64 Encoded)", # Note: Storing large images directly in DB is often discouraged
            "bday": "Birthday (YYYY-MM-DD)",
            "anniversary": "Anniversary (YYYY-MM-DD)",
            "gender": "Gender",
            "adr": "Address",
            "tel": "Telephone Number",
            "email": "Email Address",
            "impp": "Instant Messenger ID",
            "lang": "Language",
            "tz": "Time Zone",
            "geo": "Geolocation (Lat,Long)",
            "note": "Notes",
            "title": "Group Title",
            "logo": "Group Logo (Base64 Encoded)",
            "org": "Organization",
            "related": "Related Information",
            "url": "Website URL"
            # Add mappings for any other attribute names from 'role', 'is_in', 'other' tables
            # if you intend to extend this window's functionality for them.
            # Primary keys are generally skipped in 'Add' mode and shown read-only in 'Edit'.
        }

        # --- Fetch Attributes and Item Data ---
        # Fetch attribute names and types from the database manager.
        # OrderedDict is used to ensure the UI fields appear in the same order
        # as returned by get_attributes, which is important for a consistent layout.
        self.attributes = OrderedDict(dbms.get_attributes(self.category))

        # Retrieve existing item data if in "Edit" mode to pre-fill the fields.
        self.item_data = {}
        if self.mode == "Edit" and self.item_id is not None:
            self.item_data = dbms.get_item_data(self.category, self.item_id)
            print(f"Debug: Fetched existing data for {self.category} ID {self.item_id}: {self.item_data}")

        # --- Create Scrollable Frame for Attributes ---
        # This frame will contain all the label and entry pairs for attributes.
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            label_text=f"{title_category.capitalize()} Details",
            label_font=ctk.CTkFont(size=16, weight="bold")
        )
        # Place the scrollable frame in the main window's grid
        self.scrollable_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="nsew")
        # Configure the scrollable frame's internal grid:
        # Column 1 (for entry fields) will expand horizontally
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        self.attribute_entry_widgets = {} # Stores {original_attr_name: CTkEntry_widget} for easy access

        # --- Populate Scrollable Frame with Attribute Fields ---
        row_num = 0
        for attr_name, attr_type in self.attributes.items():
            # Skip primary key IDs for 'Add' mode, as they are usually auto-generated by the DB.
            if self.mode == "Add" and (attr_name.endswith('_id') or attr_name == "person_id" or attr_name == "group_id"):
                continue

            # Determine the display name for the attribute
            display_name = self.attribute_display_names.get(attr_name, attr_name.replace("_", " ").title())

            # Create a label for the attribute
            label = ctk.CTkLabel(self.scrollable_frame, text=f"{display_name}:",
                                 font=ctk.CTkFont(size=13, weight="bold"))
            label.grid(row=row_num, column=0, padx=(10, 5), pady=5, sticky="w")

            # Create an entry field for the attribute
            entry = ctk.CTkEntry(self.scrollable_frame, placeholder_text=f"Enter {display_name}...",
                                 font=ctk.CTkFont(size=13))
            entry.grid(row=row_num, column=1, padx=(5, 10), pady=5, sticky="ew")

            # If in 'Edit' mode, pre-fill the entry with existing data
            if self.mode == "Edit":
                current_value = self.item_data.get(attr_name, "")
                if current_value is not None: # Ensure None doesn't get inserted as "None" string
                    entry.insert(0, str(current_value))
                # For primary key IDs, make them read-only in edit mode
                if attr_name.endswith('_id') or attr_name == "person_id" or attr_name == "group_id":
                    entry.configure(state="readonly") # Disable editing for IDs

            # Store the entry widget reference with its original attribute name
            self.attribute_entry_widgets[attr_name] = entry
            row_num += 1

        # --- Button Frame for Save and Cancel ---
        # Group the Save and Cancel buttons in a frame for better layout control
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent") # Transparent background
        self.button_frame.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1) # Makes buttons expand
        self.button_frame.grid_columnconfigure(1, weight=1) # Makes buttons expand

        # Add a save button
        self.save_button = ctk.CTkButton(self.button_frame, text="Save Changes", command=self._save_changes,
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         height=40, hover=True)
        self.save_button.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="e") # Right-align in its column

        # Add a cancel button
        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel", command=self._cancel_changes,
                                           font=ctk.CTkFont(size=14),
                                           height=40, hover=True, fg_color="gray", hover_color="darkgray")
        self.cancel_button.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="w") # Left-align in its column

        # --- Window Close Protocol ---
        # Ensures that 'on_closing' is called when the user clicks the 'X' button
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.transient(master) # Make this window a transient window for the master
        self.grab_set()        # Make this window modal (grabs all input)
        self.focus_set()       # Give focus to this window

    def _save_changes(self):
        """
        Retrieves the current values from all attribute entry fields,
        collects them into a dictionary, and then calls the dbms to save them.
        Finally, it closes the window.
        """
        collected_data = {}
        for attr_name, entry_widget in self.attribute_entry_widgets.items():
            # Only collect data from editable fields (not read-only IDs in edit mode)
            if entry_widget.cget("state") == "normal": # 'normal' means editable
                value = entry_widget.get().strip() # Get value and remove leading/trailing whitespace
                # Convert empty strings to None, as it's common for empty DB fields to be NULL
                collected_data[attr_name] = value if value != "" else None
            elif self.mode == "Edit" and entry_widget.cget("state") == "readonly":
                # For readonly fields (like IDs in edit mode), retrieve their existing value
                collected_data[attr_name] = entry_widget.get().strip()

        # Call the mock dbms to save the collected data
        # Pass self.item_id (which will be None for 'Add' mode) to differentiate between add/edit
        dbms.save_item_data(self.category, self.item_id, collected_data)

        print(f"Data for {self.category} {self.mode} operation processed and saved.")
        self.destroy() # Close the external window

    def _cancel_changes(self):
        """
        Closes the external window without saving any changes.
        """
        print("Changes cancelled. Window closed without saving.")
        self.grab_release() # Release the input grab
        self.destroy()      # Destroy the window

    def on_closing(self):
        """
        Handles the window close event (e.g., when the user clicks the 'X' button).
        Releases the grab and destroys the window. It acts like a cancel operation.
        """
        self._cancel_changes() # Call the cancel method to ensure proper cleanup


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

    def on_item_selected(self, category_name, item_id):
        """Callback from DetailSidebar when an item is selected."""
        self.main_content_frame.update_content(category_name, item_id)


def launch():
    app = App()
    app.mainloop()
