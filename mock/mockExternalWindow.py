
# # --- ExternalWindow Class ---
# class ExternalWindow(ctk.CTkToplevel):
#     def __init__(self, master, mode="Add", category=None):
#         super().__init__(master)
#         title = f"Add new {category[:-1]}" if mode == "Add" else f"Edit {category[:-1]}"
#         self.title(title)
#         window_size_factor = 0.3
#         window_width = int(self.winfo_screenwidth() * window_size_factor)
#         window_height = int(self.winfo_screenheight() * window_size_factor)
#         self.geometry(f"{window_width}x{window_height}")
#         self.minsize(350, 200)
        
#         # Add a label
#         self.label = ctk.CTkLabel(self, text=title)
#         self.label.pack(pady=20)

#         # # Add an entry field for editing
#         # self.entry = ctk.CTkEntry(self)
#         # self.entry.pack(pady=10, padx=20, fill="x")
#         # self.entry.insert(0, "Nothing here...")  # Pre-fill with current item name

#         # Add every attribute as an entry field (Frame with Label and Entry)
#         self.attributes_frames = []
#         self.attributes = dbms.get_attributes(category) if category else []
#         for attr_name, attr_type in self.attributes:
#             frame = ctk.CTkFrame(self)
#             frame.pack(pady=5, padx=20, fill="x")

#             label = ctk.CTkLabel(frame, text=attr_name)
#             label.pack(side="left", padx=(0, 10))

#             entry = ctk.CTkEntry(frame)
#             entry.pack(side="left", expand=True, fill="x")
#             self.attributes_frames.append((label, entry))

#         # Add a save button
#         self.save_button = ctk.CTkButton(self, text="Save", command=self._save_changes)
#         self.save_button.pack(pady=10)

#     def _save_changes(self):
#         new_name = self.entry.get()
#         print(f"Changes saved: {new_name}")
#         self.destroy()  # Close the edit window

