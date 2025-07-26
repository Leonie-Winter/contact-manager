import customtkinter as ctk
import tkinter as tk
from collections import OrderedDict
from tkinter import filedialog, messagebox
import base64
import io
from PIL import Image, ImageTk

from dbms import dbms
from dbms.vcard_import import import_vcard


# --- CategorySidebar Class (Leftmost Sidebar: Persons, Groups, Files) ---
class CategorySidebar(ctk.CTkFrame):
    def __init__(self, master, on_category_selected_callback, on_import_callback):
        super().__init__(master, width=150, corner_radius=0)
        self.grid(row=0, column=0, sticky="nswe")
        self.grid_columnconfigure(0, weight=1) # Allow buttons to expand horizontally

        self.on_category_selected_callback = on_category_selected_callback
        self.current_selection = ctk.StringVar(value="")
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
            
        # Add other buttons below the categories
        self.clear_data_button = ctk.CTkButton(
            self, text="Clear all data", command=self._clear_all_data
        )
        self.clear_data_button.grid(row=len(self._categories) + 1, column=0, padx=5, pady=(10, 2), sticky="ew")

        self.generate_data_button = ctk.CTkButton(
            self, text="Test: Generate new Data", command=self._generate_test_data
        )
        self.generate_data_button.grid(row=len(self._categories) + 2, column=0, padx=5, pady=(2, 10), sticky="ew")

        self.import_button = ctk.CTkButton(
            self, text="Import vCard", command=on_import_callback
        )
        self.import_button.grid(row=len(self._categories) + 3, column=0, padx=5, pady=(2, 10), sticky="ew")

        # Set initial selection
        self._select_category(self._categories[0]) # Select the first category by default


    def _clear_all_data(self):
        if messagebox.askyesno("Confirm", "Really delete all data?"):
            dbms.clear_tables()
            messagebox.showinfo("Success", "All data deleted!")
            self.on_category_selected_callback(self.current_selection.get())

    def _generate_test_data(self):
        dbms.generate_test_data()
        messagebox.showinfo("Success", "Test data generated!")
        self.on_category_selected_callback(self.current_selection.get())

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
    def __init__(self, master, current_category_getter, on_refresh_callback=None):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.grid(row=0, column=0, sticky="ew")
        self.grid_columnconfigure((0,1,2,3), weight=1) # Distribute buttons evenly

        self.current_category_getter = current_category_getter # Callback to get the current category
        self.on_refresh_callback = on_refresh_callback

        button_width = 70 # Adjust as needed

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
        current_category = self.current_category_getter()
        if current_category and current_category != "Files": # Cannot add "Files"
            # Create Window
            add_window = ExternalWindow(self.master.master, mode="Add", category=current_category)
            # When the external window closes, refresh the list
            self.master.master.wait_window(add_window)
            self._refresh_action() # Refresh after window closes
        else:
            messagebox.showinfo("Cannot Add", "Cannot add items to 'Files' category or no category selected.")

    def _edit_action(self):
        print("Edit action triggered.")
        current_category = self.current_category_getter()
        selected_item_id = self.master.current_item_selection.get() # Get ID from DetailSidebar's selection
        
        if current_category and selected_item_id != 0 and current_category != "Files":
            # Create Window
            edit_window = ExternalWindow(self.master.master, mode="Edit", category=current_category, item_id=selected_item_id)
            # When the external window closes, refresh the list and update main content
            self.master.master.wait_window(edit_window)
            self._refresh_action() # Refresh after window closes
            # Re-select the item to update its details in MainContentFrame
            self.master.on_item_selected_callback(current_category, selected_item_id)
        else:
            messagebox.showinfo("Cannot Edit", "Please select a person or group to edit.")


    def _delete_action(self):
        print("Delete action triggered.")
        current_category = self.current_category_getter()
        selected_item_id = self.master.current_item_selection.get()

        if current_category and selected_item_id != 0 and current_category.lower() != "files":
            # Get item name for confirmation message
            item_data = dbms.get_item_data(current_category.lower(), selected_item_id)
            item_name = ""
            if item_data:
                # Prioritize 'fn' for persons, 'title' for groups
                item_name = item_data.get('fn') or item_data.get('title')
            
            if not item_name: # Fallback if no specific name attribute found
                item_name = f"{current_category[:-1].capitalize()} ID: {selected_item_id}"

            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{item_name}'?"):
                try:
                    # Call the database function to delete the item
                    dbms.delete_item(current_category.lower(), selected_item_id)
                    messagebox.showinfo("Delete Success", f"'{item_name}' deleted successfully.")
                    
                    # Refresh the list in DetailSidebar to remove the deleted item
                    self._refresh_action() 
                    
                    # Notify MainContentFrame that the item is deleted, so it clears its display
                    self.master.on_item_selected_callback(current_category, None) 
                except Exception as e:
                    messagebox.showerror("Delete Error", f"Failed to delete '{item_name}': {e}")
                    print(f"Error deleting item {item_name} (ID: {selected_item_id}) from {current_category}: {e}")
        else:
            messagebox.showinfo("Cannot Delete", "Please select a person or group to delete.")

    def _refresh_action(self):
        print("Refresh action triggered.")
        if self.on_refresh_callback:
            self.on_refresh_callback()


class DetailSidebar(ctk.CTkFrame):
    def __init__(self, master, on_item_selected_callback):
        super().__init__(master, width=200, corner_radius=0)
        self.grid(row=0, column=1, sticky="nswe")
        self.grid_columnconfigure(0, weight=1) # Allow items to expand horizontally

        self.on_item_selected_callback = on_item_selected_callback
        self.current_category = None
        self.current_item_selection = ctk.IntVar(value=0) # Stores the ID of the selected item

        self.item_buttons = []

        # Add a title label for the sidebar
        self.title_label = ctk.CTkLabel(self, text="Items", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=5, pady=(10, 5), sticky="ew")

        # Add Action Bar (now in row=1)
        # Pass a lambda to get the current category from this DetailSidebar
        self.action_bar = ActionBar(self,
                                    current_category_getter=lambda: self.current_category,
                                    on_refresh_callback=lambda: self.update_content(self.current_category, force_update=True))
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
        """
        Updates the list of items based on the selected category.
        `force_update` can be used to re-fetch even if category hasn't changed.
        """
        if self.current_category == category_name and not force_update:
            return

        self.current_category = category_name
        
        # Preserve selected item if it exists in the new list, otherwise reset
        previous_selection_id = self.current_item_selection.get()
        self.current_item_selection.set(0) # Reset before re-populating

        # Clear existing buttons
        for button in self.item_buttons:
            button.destroy()
        self.item_buttons.clear()

        # Remove placeholder if present
        if self.placeholder_label:
            self.placeholder_label.destroy()
            self.placeholder_label = None

        items = OrderedDict()
        if category_name != "Files": # Only query DB for Persons/Groups
            items = dbms.get_all_items_ids_and_names(category_name)
        else:
            # For "Files" category, you might list actual files or have mock data
            # For this example, we'll just show a message.
            self.placeholder_label = ctk.CTkLabel(self.scrollable_frame, text="File listing not implemented yet.")
            self.placeholder_label.pack(expand=True)
            self.on_item_selected_callback(self.current_category, None) # Notify App no item selected
            return

        # If no items found, display placeholder message
        if not items:
            self.placeholder_label = ctk.CTkLabel(self.scrollable_frame, text=f"No {category_name.lower()} found.")
            self.placeholder_label.pack(expand=True)
            self.on_item_selected_callback(self.current_category, None) # Notify App no item selected
            return

        # Create buttons for each item in the selected category
        selected_item_found = False
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

            if item_id == previous_selection_id:
                self.current_item_selection.set(item_id)
                selected_item_found = True

        # Automatically select the first item in the new category or re-select previous
        if items:
            if not selected_item_found:
                first_item_id = next(iter(items))
                self._select_item(first_item_id)
            else:
                self._select_item(self.current_item_selection.get()) # Trigger update for display
        else:
            self.on_item_selected_callback(self.current_category, None)


    def _select_item(self, item_id):
        """Internal method to handle item selection and update appearance."""
        if self.current_item_selection.get() == item_id: # Avoid re-selection if already selected
            return

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
class AssignmentWindow(ctk.CTkToplevel):
    """
    A Toplevel window for assigning persons to groups or groups to persons.
    """
    def __init__(self, master, item_id, category_to_assign, current_category, refresh_callback):
        """
        Initializes the AssignmentWindow.

        Args:
            master: The parent widget (e.g., MainContentFrame).
            item_id: The ID of the current person or group.
            category_to_assign: The category of items to assign (e.g., "groups" or "persons").
            current_category: The category of the item being viewed (e.g., "Persons" or "Groups").
            refresh_callback: A callback function to refresh the main content after saving.
        """
        super().__init__(master)
        self.master = master
        self.item_id = item_id
        self.category_to_assign = category_to_assign
        self.current_category = current_category
        self.refresh_callback = refresh_callback
        self.vars = {} # To store BooleanVar for each checkbox

        window_size_factor = 0.3
        window_width = int(self.winfo_screenwidth() * window_size_factor)
        window_height = int(self.winfo_screenheight() * window_size_factor)
        self.geometry(f"{window_width}x{window_height}")
        self.minsize(200, 250)
        self.transient(master)  # Make this window transient relative to the master
        self.grab_set()         # Grab all events to this window

        self._create_widgets()

    def _create_widgets(self):
        """Creates the widgets for the assignment window."""
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text=f"Select {self.category_to_assign}:")
        self.scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

        all_items = dbms.get_all_items_ids_and_names(self.category_to_assign)
        
        if self.current_category == "Persons":
            assigned_items = set(id for id, _ in dbms.get_groups_for_person(self.item_id))
        elif self.current_category == "Groups":
            assigned_items = set(id for id, _ in dbms.get_persons_for_group(self.item_id))
        else:
            assigned_items = set() # Should not happen with current logic

        for item_id, item_name in all_items.items():
            var = ctk.BooleanVar(value=(item_id in assigned_items))
            chk = ctk.CTkCheckBox(self.scrollable_frame, text=item_name, variable=var)
            chk.pack(anchor="w", padx=5, pady=2)
            self.vars[item_id] = var

        save_button = ctk.CTkButton(self, text="Save Assignments", command=self._save_assignments)
        save_button.pack(pady=10)

    def _save_assignments(self):
        """Saves the assignments based on checkbox states."""
        for item_id_to_assign, var in self.vars.items():
            if self.current_category == "Persons":
                if var.get():
                    dbms.assign_person_to_group(self.item_id, item_id_to_assign)
                else:
                    dbms.remove_person_from_group(self.item_id, item_id_to_assign)
            elif self.current_category == "Groups":
                if var.get():
                    dbms.assign_person_to_group(item_id_to_assign, self.item_id)
                else:
                    dbms.remove_person_from_group(item_id_to_assign, self.item_id)
        
        messagebox.showinfo("Assignment Saved", "Assignments updated successfully!")
        self.destroy() # Close the Toplevel window

        # Refresh the content in the MainContentFrame
        if self.refresh_callback:
            self.refresh_callback(self.current_category, self.item_id)

class MainContentFrame(ctk.CTkFrame):
    """
    This frame displays the detailed attributes of a selected item (person or group).
    It dynamically generates labels for each attribute and its value in a scrollable view.
    """
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.grid(row=0, column=2, sticky="nswe")
        self.grid_rowconfigure(0, weight=1)    # Details scroll frame
        self.grid_rowconfigure(1, weight=0)    # My button row
        self.grid_rowconfigure(2, weight=0)    # Import button row
        self.grid_columnconfigure(0, weight=1) # Allows content to expand horizontally

        self.current_category = None
        self.current_item_id = None


        # Initial placeholder label, visible when no item is selected
        self.placeholder_label = ctk.CTkLabel(
            self,
            text="Select a category and an item to view details.",
            font=("Roboto", 18, "bold"),
            text_color="gray" # Make it slightly less prominent
        )
        self.placeholder_label.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Define assign button
        self.assign_btn = None
        
        # This will hold the CTkScrollableFrame for item details
        self.details_scroll_frame = None

        # Attribute display name mapping for friendly labels
        self.attribute_display_names = {
            "fn": "First Name", "n": "Last Name", "nickname": "Nickname",
            "photo": "Photo", "bday": "Birthday", "anniversary": "Anniversary",
            "gender": "Gender", "adr": "Address", "tel": "Telephone",
            "email": "Email", "impp": "Instant Messenger", "lang": "Language",
            "tz": "Time Zone", "geo": "Geolocation", "note": "Notes",
            "title": "Group Title", "logo": "Group Logo", "org": "Organization",
            "related": "Related Information", "url": "Website URL"
        }

    def _clear_content(self):
        """Clears all dynamically created content within the MainContentFrame."""
        if self.details_scroll_frame:
            self.details_scroll_frame.destroy()
            self.details_scroll_frame = None
        
        # Ensure placeholder is visible and packed when no item is selected
        if self.placeholder_label:
            self.placeholder_label.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

    def update_content(self, category, item_id=None):
        """
        Updates the content displayed based on the selected category and item ID.
        If item_id is None, a placeholder message is shown.
        """
        self._clear_content() # Always clear previous content first

        self.current_category = category
        self.current_item_id = item_id

        # Handle "Files" category separately as it doesn't have item details in DB
        if self.current_category == "Files":
            self.placeholder_label.configure(text="File details can be shown here (not yet implemented).")
            return

        if item_id is None:
            self.placeholder_label.configure(text=f"Select an item from '{category}' to view details.")
            return

        # Fetch item data from the database
        item_data = dbms.get_item_data(category, item_id)

        if not item_data:
            self.placeholder_label.configure(text=f"No details found for the selected {category[:-1]} (ID: {item_id}).")
            return

        # Hide the initial placeholder label since we have content to display
        if self.placeholder_label:
            self.placeholder_label.grid_forget()

        # Create a scrollable frame for the item details
        display_title = item_data.get('fn') or item_data.get('title') or f"{category[:-1].capitalize()} Details"
        self.details_scroll_frame = ctk.CTkScrollableFrame(
            self,
            label_text=f"Details for: {display_title}",
            label_font=ctk.CTkFont(size=18, weight="bold")
        )
        self.details_scroll_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="nsew")
        self.details_scroll_frame.grid_columnconfigure(1, weight=1) # Value column expands

        row_num = 0
        # Fetch attributes from dbms to ensure correct order and types for display
        attributes_info = OrderedDict(dbms.get_attributes(self.current_category))

        for attr_name, attr_type in attributes_info.items():

            display_name = self.attribute_display_names.get(attr_name, attr_name.replace("_", " ").title())
            value = item_data.get(attr_name) # Get raw value

            # Special handling for BLOB types (assuming base64 encoded image data)
            if attr_type == "BLOB" and value:
                try:
                    # Ensure value is a string, then decode
                    img_data_bytes = base64.b64decode(str(value))
                    img = Image.open(io.BytesIO(img_data_bytes))
                    img.thumbnail((200, 200)) # Resize for display in UI
                    tk_img = ImageTk.PhotoImage(img)

                    # Create a label to hold the image
                    img_label = ctk.CTkLabel(self.details_scroll_frame, text="", image=tk_img)
                    img_label.image = tk_img
                    img_label.grid(row=row_num, column=0, columnspan=2, padx=10, pady=5)
                    row_num += 1
                except (base64.binascii.Error, IOError, Exception) as e:
                    # Fallback if image decoding or loading fails
                    print(f"Error displaying image for attribute {attr_name}: {e}")
                    value_text = f"[Image Data - Unable to Display: {e}]"
                    
                    name_label = ctk.CTkLabel(self.details_scroll_frame, text=f"{display_name}:",
                                              font=ctk.CTkFont(size=13, weight="bold"))
                    name_label.grid(row=row_num, column=0, padx=(10, 5), pady=2, sticky="nw")
                    value_label = ctk.CTkLabel(self.details_scroll_frame, text=value_text, wraplength=400, justify="left")
                    value_label.grid(row=row_num, column=1, padx=(5, 10), pady=2, sticky="w")
                    row_num += 1
            else:
                # Regular text attributes
                name_label = ctk.CTkLabel(self.details_scroll_frame, text=f"{display_name}:",
                                          font=ctk.CTkFont(size=13, weight="bold"))
                name_label.grid(row=row_num, column=0, padx=(10, 5), pady=2, sticky="nw")

                value_text = str(value) if value is not None else "N/A"

                value_label = ctk.CTkLabel(self.details_scroll_frame, text=value_text, wraplength=400, justify="left")
                value_label.grid(row=row_num, column=1, padx=(5, 10), pady=2, sticky="w")
                row_num += 1

        # --- Show linked groups/persons ---
        if self.current_category == "Persons":
            groups = dbms.get_groups_for_person(item_id)
            group_names = ", ".join(title for _, title in groups) if groups else "None"
            name_label = ctk.CTkLabel(self.details_scroll_frame, text="Groups:",
                                      font=ctk.CTkFont(size=13, weight="bold"))
            name_label.grid(row=row_num, column=0, padx=(10, 5), pady=2, sticky="nw")
            value_label = ctk.CTkLabel(self.details_scroll_frame, text=group_names, wraplength=400, justify="left")
            value_label.grid(row=row_num, column=1, padx=(5, 10), pady=2, sticky="w")
            row_num += 1

        elif self.current_category == "Groups":
            persons = dbms.get_persons_for_group(item_id)
            person_names = ", ".join(name for _, name in persons) if persons else "None"
            name_label = ctk.CTkLabel(self.details_scroll_frame, text="Members:",
                                      font=ctk.CTkFont(size=13, weight="bold"))
            name_label.grid(row=row_num, column=0, padx=(10, 5), pady=2, sticky="nw")
            value_label = ctk.CTkLabel(self.details_scroll_frame, text=person_names, wraplength=400, justify="left")
            value_label.grid(row=row_num, column=1, padx=(5, 10), pady=2, sticky="w")
            row_num += 1

        # --- Assignment Buttons ---
        if self.assign_btn:
            self.assign_btn.destroy()

        if self.current_item_id: # Only show assign button if an item is selected
            if self.current_category == "Persons":
                self.assign_btn = ctk.CTkButton(
                    self.details_scroll_frame,
                    text="Assign to Groups",
                    command=lambda: self._open_assignment_window(
                        self.current_item_id, "groups", "Persons"
                    )
                )
                self.assign_btn.grid(row=999, column=0, columnspan=2, pady=(10, 5)) # Use a high row number to place it at the bottom
                row_num += 1
            elif self.current_category == "Groups":
                self.assign_btn = ctk.CTkButton(
                    self.details_scroll_frame,
                    text="Assign Persons",
                    command=lambda: self._open_assignment_window(
                        self.current_item_id, "persons", "Groups"
                    )
                )
                self.assign_btn.grid(row=999, column=0, columnspan=2, pady=(10, 5))
                row_num += 1

    def _open_assignment_window(self, item_id, category_to_assign, current_category):
        """
        Opens the AssignmentWindow for person/group assignments.
        """
        # Pass self.update_content as the refresh_callback to refresh the main frame
        AssignmentWindow(self.master, item_id, category_to_assign, current_category, self.update_content)

    def _main_button_callback(self):
        """
        Generic action button. Its behavior can be customized based on the
        currently selected category and item.
        """
        item_title = None
        if self.current_item_id and self.current_category:
            item_data = dbms.get_item_data(self.current_category, self.current_item_id)
            if item_data:
                item_title = item_data.get('fn') or item_data.get('title')

        current_info = f"Category: {self.current_category}, Item: {item_title or 'None'}"
        messagebox.showinfo("Main Action", f"Performing action on:\n{current_info}")
        print(f"Main Action Button clicked. Current view: {current_info}")

    def import_vcard_file(self):
        """Opens a file dialog to select a vCard file for import."""
        file_path = filedialog.askopenfilename(
            title="Select a vCard file",
            filetypes=[("vCard files", "*.vcf"), ("All files", "*.*")]
        )
        if file_path:
            try:
                # Call the external vCard import function
                import_vcard(file_path)
                messagebox.showinfo("vCard Import", "vCard import successful! Refreshing persons list.")
                # After successful import, refresh the 'Persons' category in the DetailSidebar
                # This needs to be done via the App's on_category_selected or directly calling DetailSidebar
                # self.master is the App instance
                self.master.detail_sidebar.update_content("Persons", force_update=True)
                # Optionally, re-select the first person or the newly imported one if its ID is known
            except Exception as e:
                print(f"Error importing vCard: {e}")
                messagebox.showerror("vCard Import Error", f"Failed to import vCard: {e}")



# --- ExternalWindow Class (Moved here for self-containment in gui.py) ---
class ExternalWindow(ctk.CTkToplevel):
    def __init__(self, master, mode="Add", category=None, item_id=None):
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
            "photo": "Photo",
            "bday": "Birthday",
            "anniversary": "Anniversary",
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
            "logo": "Group Logo",
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

        # Call the dbms to save the collected data
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
        # Pass main_content_frame.import_vcard_file as the callback for the Import button
        self.category_sidebar = CategorySidebar(self, self.on_category_selected, self.main_content_frame.import_vcard_file)


    def on_category_selected(self, category_name):
        """Callback from CategorySidebar when a category is selected."""
        self.detail_sidebar.update_content(category_name)
        # Update main content with a general message for the category
        self.main_content_frame.update_content(category_name, item_id=None) # No item selected initially for new category

    def on_item_selected(self, category_name, item_id):
        """Callback from DetailSidebar when an item is selected."""
        self.main_content_frame.update_content(category_name, item_id)


def launch():
    # Set CustomTkinter appearance mode and color theme
    ctk.set_appearance_mode("System")  # Options: "System" (default), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Options: "blue" (default), "dark-blue", "green"

    app = App()
    app.mainloop()

# if __name__ == "__main__":
#     launch()
