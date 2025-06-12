import customtkinter as ctk
import tkinter as tk
from collections import OrderedDict

# --- Mock Database Manager (dbms) ---
# This class simulates your database operations for demonstration purposes.
# In your actual project, this would be your 'dbms.py' module.

class MockDBManager:
    def __init__(self):
        # Dummy data to simulate existing persons and groups
        self._persons_data = {
            1: {
                "person_id": 1,
                "fn": "John",
                "n": "Doe",
                "nickname": "Johnny",
                "photo": "(base64 data for John)",
                "bday": "1990-01-15",
                "anniversary": "",
                "gender": "Male",
                "adr": "123 Main St, Anytown",
                "tel": "555-123-4567",
                "email": "john.doe@example.com",
                "impp": "johnny_im",
                "lang": "en",
                "tz": "America/New_York",
                "geo": "40.7128,-74.0060",
                "note": "A very important contact for project Alpha."
            },
            2: {
                "person_id": 2,
                "fn": "Jane",
                "n": "Smith",
                "nickname": "Janie",
                "photo": "",
                "bday": "1985-05-20",
                "anniversary": "2010-06-01",
                "gender": "Female",
                "adr": "456 Oak Ave, Somewhere",
                "tel": "555-987-6543",
                "email": "jane.smith@example.com",
                "impp": "",
                "lang": "es",
                "tz": "Europe/Madrid",
                "geo": "",
                "note": "Team lead for project Beta. Speaks Spanish."
            }
        }
        self._groups_data = {
            101: {
                "group_id": 101,
                "title": "Family Contacts",
                "logo": "(base64 data for family logo)",
                "org": "Family Enterprises",
                "related": "Personal",
                "url": "http://myfamily.example.com"
            },
            102: {
                "group_id": 102,
                "title": "Work Colleagues",
                "logo": "",
                "org": "Tech Solutions Inc.",
                "related": "Professional",
                "url": "http://techsolutions.example.com"
            }
        }
        # Keep track of the next available ID for new items
        self._next_person_id = max(self._persons_data.keys(), default=0) + 1
        self._next_group_id = max(self._groups_data.keys(), default=100) + 1


    def get_attributes(self, category):
        """
        Simulates fetching attribute names and types for a given category (table).
        Returns a list of (attribute_name, attribute_type) tuples,
        matching the structure from your `create_tables` function.
        """
        if category == "persons":
            # The order here defines the order of fields in the UI
            return [
                ("fn", "TEXT"), ("n", "TEXT"), ("nickname", "TEXT"),
                ("bday", "TEXT"), ("anniversary", "TEXT"), ("gender", "TEXT"),
                ("tel", "TEXT"), ("email", "TEXT"), ("impp", "TEXT"),
                ("adr", "TEXT"), ("lang", "TEXT"), ("tz", "TEXT"),
                ("geo", "TEXT"), ("note", "TEXT"), ("photo", "BLOB")
            ]
        elif category == "groups":
            return [
                ("title", "TEXT"), ("org", "TEXT"), ("url", "TEXT"),
                ("related", "TEXT"), ("logo", "BLOB")
            ]
        # For other tables, if you decide to extend the UI for them
        elif category == "role":
            return [("role", "TEXT"), ("member", "TEXT")]
        # Primary key attributes like 'person_id' or 'group_id' are handled internally
        # and not typically presented for direct user input in 'Add' mode.
        return []

    def get_item_data(self, category, item_id):
        """
        Simulates fetching all data for a specific item (person or group) by its ID.
        Returns a dictionary of attribute_name: value for the specified item.
        """
        if category == "persons":
            return self._persons_data.get(item_id, {})
        elif category == "groups":
            return self._groups_data.get(item_id, {})
        return {}

    def save_item_data(self, category, item_id, data):
        """
        Simulates saving or updating item data.
        In a real application, this would perform INSERT or UPDATE SQL queries
        based on whether item_id is None (new item) or an existing ID (update).
        """
        print("\n--- Mock DBMS: Saving Data ---")
        print(f"Category: {category}")

        if category == "persons":
            if item_id is None: # Adding a new person
                new_id = self._next_person_id
                data["person_id"] = new_id # Assign new ID
                self._persons_data[new_id] = data
                self._next_person_id += 1
                print(f"Added NEW person with ID: {new_id}")
            else: # Updating an existing person
                if item_id in self._persons_data:
                    # Update existing entry with new values
                    self._persons_data[item_id].update(data)
                    print(f"Updated person with ID: {item_id}")
                else:
                    print(f"ERROR: Person with ID {item_id} not found for update.")
        elif category == "groups":
            if item_id is None: # Adding a new group
                new_id = self._next_group_id
                data["group_id"] = new_id # Assign new ID
                self._next_group_id += 1
                self._groups_data[new_id] = data
                print(f"Added NEW group with ID: {new_id}")
            else: # Updating an existing group
                if item_id in self._groups_data:
                    self._groups_data[item_id].update(data)
                    print(f"Updated group with ID: {item_id}")
                else:
                    print(f"ERROR: Group with ID {item_id} not found for update.")
        else:
            print(f"ERROR: Unsupported category '{category}' for saving.")

        print("--- Data to be saved: ---")
        for key, value in data.items():
            print(f"  {key}: {value}")
        print("-------------------------\n")


# Instantiate the mock DB Manager, acting as your 'dbms' object
dbms = MockDBManager()

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

# --- Main Application for Demonstration ---
# This is a simple CustomTkinter application to demonstrate how to use
# the ExternalWindow class.
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Contacts Manager Main App")
        self.geometry("800x600") # Set a larger default size for the main app

        # Configure grid for the main app window
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create a main frame for buttons
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self.main_frame, text="Contacts Manager Dashboard",
                                  font=ctk.CTkFont(size=28, weight="bold"))
        self.label.pack(pady=30)

        # Buttons to open the external window for various operations
        self.add_person_button = ctk.CTkButton(
            self.main_frame,
            text="Add New Person",
            command=lambda: self.open_external_window("Add", "persons"),
            height=45,
            font=ctk.CTkFont(size=16)
        )
        self.add_person_button.pack(pady=10)

        self.edit_person_button = ctk.CTkButton(
            self.main_frame,
            text="Edit Existing Person (ID 1)",
            command=lambda: self.open_external_window("Edit", "persons", item_id=1),
            height=45,
            font=ctk.CTkFont(size=16)
        )
        self.edit_person_button.pack(pady=10)

        self.add_group_button = ctk.CTkButton(
            self.main_frame,
            text="Add New Group",
            command=lambda: self.open_external_window("Add", "groups"),
            height=45,
            font=ctk.CTkFont(size=16)
        )
        self.add_group_button.pack(pady=10)

        self.edit_group_button = ctk.CTkButton(
            self.main_frame,
            text="Edit Existing Group (ID 101)",
            command=lambda: self.open_external_window("Edit", "groups", item_id=101),
            height=45,
            font=ctk.CTkFont(size=16)
        )
        self.edit_group_button.pack(pady=10)

        self.external_window_instance = None # To keep track of the opened external window

    def open_external_window(self, mode, category, item_id=None):
        """
        Opens a new ExternalWindow instance.
        Ensures that only one external window is open at a time,
        and brings it to the front if it's already open.
        """
        if self.external_window_instance is None or not self.external_window_instance.winfo_exists():
            print(f"Opening external window: Mode='{mode}', Category='{category}', Item ID='{item_id}'")
            self.external_window_instance = ExternalWindow(self, mode=mode, category=category, item_id=item_id)
        else:
            print("External window is already open. Bringing it to front.")
            self.external_window_instance.focus_set() # Bring existing window to front

# --- Application Entry Point ---
if __name__ == "__main__":
    # Set CustomTkinter appearance mode and color theme
    ctk.set_appearance_mode("System")  # Options: "System" (default), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Options: "blue" (default), "dark-blue", "green"

    app = App()
    app.mainloop()