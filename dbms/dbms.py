import sqlite3
import os

DB_DIR = 'dbms'
DB_PATH = os.path.join(DB_DIR, 'contacts.db')

def create_tables():
    """Create the necessary tables in the SQLite database."""
    # Ensure the directory for the database exists
    os.makedirs(DB_DIR, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS persons (
        person_id INTEGER PRIMARY KEY AUTOINCREMENT,
        fn TEXT,
        n TEXT,
        nickname TEXT,
        photo BLOB,
        bday TEXT,
        anniversary TEXT,
        gender TEXT,
        adr TEXT,
        tel TEXT,
        email TEXT,
        impp TEXT,
        lang TEXT,
        tz TEXT,
        geo TEXT,
        note TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        group_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        logo BLOB,
        org TEXT,
        related TEXT,
        url TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS role (
        role_id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT,
        member TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS is_in (
        is_in_id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER,
        group_id INTEGER,
        role_id INTEGER,
        FOREIGN KEY(person_id) REFERENCES persons(person_id),
        FOREIGN KEY(group_id) REFERENCES groups(group_id),
        FOREIGN KEY(role_id) REFERENCES role(role_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS other (
        other_id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER,
        categories TEXT,
        prodid TEXT,
        rev TEXT,
        sound TEXT,
        uid TEXT,
        clientpidmap TEXT,
        version TEXT,
        key TEXT,
        fburl TEXT,
        caladruri TEXT,
        caluri TEXT,
        FOREIGN KEY(person_id) REFERENCES persons(person_id)
    )
    """)

    connection.commit()
    connection.close()
    print("Tables created successfully.")


def get_all_items_ids_and_names(category):
    """
    Fetch IDs and names from the database based on the category.
    Returns a dictionary where keys are IDs and values are names.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    category = category.lower() # Ensure category matches table names ('persons', 'groups')

    if category == "persons":
        cursor.execute("SELECT person_id, fn FROM persons")
    elif category == "groups":
        cursor.execute("SELECT group_id, title FROM groups")
    else:
        print(f"Warning: Unknown category '{category}' in get_all_items_ids_and_names.")
        conn.close()
        return {}

    results = {}
    for row in cursor.fetchall():
        results[row[0]] = row[1]

    conn.close()
    return results

def get_item_data(category, item_id):
    """
    Fetch a single item from the database based on category and item ID.
    Returns the item as a dictionary where keys are column names.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    category = category.lower() # Ensure category matches table names

    if category == "persons":
        cursor.execute(f"SELECT * FROM persons WHERE person_id = ?", (item_id,))
    elif category == "groups":
        cursor.execute(f"SELECT * FROM groups WHERE group_id = ?", (item_id,))
    else:
        print(f"Unknown category: {category} in get_item_data")
        conn.close()
        return None
    
    result = cursor.fetchone()

    if result:
        column_names = [description[0] for description in cursor.description]
        item_dict = dict(zip(column_names, result))
        conn.close()
        return item_dict
    else:
        conn.close()
        return None # Item not found

def get_attributes(category):
    """
    Fetch all attributes for a given category.
    Returns a list of tuples where each tuple contains the attribute name and its type.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    category = category.lower() # Ensure category matches table names

    if category == "persons":
        cursor.execute("PRAGMA table_info(persons)")
    elif category == "groups":
        cursor.execute("PRAGMA table_info(groups)")
    else:
        print(f"Unknown category: {category} in get_attributes")
        conn.close()
        return []

    attributes = cursor.fetchall()
    conn.close()

    # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
    # We want (name, type)
    return [(attr[1], attr[2]) for attr in attributes]

def save_item_data(category, item_id, data):
    """
    Saves or updates item data in the database for a given category.
    Handles both adding new items (item_id is None) and editing existing ones.

    Args:
        category (str): The table name (e.g., "persons", "groups").
        item_id (int or None): The ID of the item if editing, or None if adding a new item.
        data (dict): A dictionary of column_name: value pairs to save.
    """
    conn = None # Initialize connection to None for finally block
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        category = category.lower() # Ensure category matches table names

        if category == "persons":
            table_name = "persons"
            id_column = "person_id"
        elif category == "groups":
            table_name = "groups"
            id_column = "group_id"
        else:
            print(f"Error: Unknown category '{category}'. Data not saved.")
            return

        # Prepare columns and values from the incoming data
        # We need to filter out the primary key if it's passed in the data dict,
        # because for INSERT it's AUTOINCREMENT, and for UPDATE it's used in the WHERE clause.
        query_columns = []
        query_values = []
        for col, val in data.items():
            if col != id_column: # Exclude the primary key column from the INSERT/UPDATE lists
                query_columns.append(col)
                query_values.append(val)

        if item_id is None: # Add new item (INSERT operation)
            # Ensure there's actual data to insert (excluding the auto-incremented ID)
            if not query_columns:
                print(f"No non-ID data provided for new {category[:-1]}. Skipping insert.")
                return

            placeholders = ', '.join(['?'] * len(query_columns))
            cols_str = ', '.join(query_columns)
            
            sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
            print(f"Executing INSERT for {category}: SQL='{sql}' with values={query_values}")
            cursor.execute(sql, tuple(query_values))
            print(f"New {category[:-1]} added with ID: {cursor.lastrowid}")

        else: # Edit existing item (UPDATE operation)
            # Ensure there are fields to update
            if not query_columns:
                print(f"No data fields to update for {category[:-1]} ID {item_id}. Skipping update.")
                return

            set_clauses = [f"{col} = ?" for col in query_columns]
            set_str = ', '.join(set_clauses)
            
            # Add the item_id to the end of the values list for the WHERE clause
            update_values = query_values + [item_id]
            sql = f"UPDATE {table_name} SET {set_str} WHERE {id_column} = ?"
            print(f"Executing UPDATE for {category[:-1]} ID {item_id}: SQL='{sql}' with values={update_values}")
            cursor.execute(sql, tuple(update_values))
            
            if cursor.rowcount == 0:
                print(f"Warning: No {category[:-1]} found with ID {item_id} to update.")
            else:
                print(f"{category[:-1]} ID {item_id} updated successfully.")

        conn.commit()
        print(f"Data for {category[:-1]} {'added' if item_id is None else 'updated'} successfully in DB.")

    except sqlite3.Error as e:
        print(f"Database error during save_item_data: {e}")
        if conn:
            conn.rollback() # Rollback changes in case of error
    except Exception as e:
        print(f"An unexpected error occurred during save_item_data: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

def delete_item(category, item_id):
    """
    Deletes an item from the database based on category and item ID.
    
    Args:
        category (str): The table name (e.g., "persons", "groups").
        item_id (int): The ID of the item to delete.
    """
    conn = None # Initialize connection to None for finally block
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        category = category.lower() # Ensure category matches table names

        if category == "persons":
            table_name = "persons"
            id_column = "person_id"
        elif category == "groups":
            table_name = "groups"
            id_column = "group_id"
        else:
            print(f"Error: Unknown category '{category}'. Item not deleted.")
            return

        sql = f"DELETE FROM {table_name} WHERE {id_column} = ?"
        cursor.execute(sql, (item_id,))
        
        if cursor.rowcount == 0:
            print(f"Warning: No {category[:-1]} found with ID {item_id} to delete.")
        else:
            print(f"{category[:-1]} ID {item_id} deleted successfully.")

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error during delete_item: {e}")
        if conn:
            conn.rollback() # Rollback changes in case of error
    except Exception as e:
        print(f"An unexpected error occurred during delete_item: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

def clear_tables():
    """Clear all data from the persons and groups tables."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM persons")
    cursor.execute("DELETE FROM groups")
    cursor.execute("DELETE FROM role")
    cursor.execute("DELETE FROM is_in")
    cursor.execute("DELETE FROM other")

    connection.commit()
    connection.close()
    print("Tables cleared successfully.")

def generate_test_data():
    """Generates test data for persons and groups using the Tests class."""
    test = Tests()
    Tests().generate_data(num_persons=5, num_groups=2)
    print("\n--- Fetched Persons ---")
    persons = get_all_items_ids_and_names("Persons")
    for person_id, fn in persons.items():
        print(f"ID: {person_id}, Name: {fn}")

    print("\n--- Fetched Groups ---")
    groups = get_all_items_ids_and_names("Groups")
    for group_id, title in groups.items():
        print(f"ID: {group_id}, Title: {title}")


class Tests:
    """Class containing test functions for generating random data and inserting it into the database."""
    def __init__(self):
        try:
            import faker
            self.Faker = faker.Faker
        except ImportError:
            # Automatically install Faker if not available
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Faker"])
            import faker
            self.Faker = faker.Faker

    def insert_person_data(self, fake_data):
        """Inserts a single randomly generated person into the persons table."""
        import random
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        fn = fake_data.name()
        n = fake_data.last_name() + ";" + fake_data.first_name() + ";;"
        nickname = fake_data.first_name()
        bday = fake_data.date_of_birth(minimum_age=18, maximum_age=90).strftime('%Y-%m-%d')
        anniversary = fake_data.date_this_century().strftime('%Y-%m-%d')
        gender = random.choice(['Male', 'Female', 'Other'])
        adr = fake_data.address().replace('\n', ', ') # Flatten address
        tel = fake_data.phone_number()
        email = fake_data.email()
        impp = fake_data.uri()
        lang = fake_data.language_code()
        tz = fake_data.timezone()
        geo = f"{fake_data.latitude()}, {fake_data.longitude()}"
        note = fake_data.sentence(nb_words=10)

        # photo BLOB is not generated for simplicity, it would require converting an image to bytes
        # For now, it will be NULL

        cursor.execute("""
        INSERT INTO persons (fn, n, nickname, bday, anniversary, gender, adr, tel, email, impp, lang, tz, geo, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (fn, n, nickname, bday, anniversary, gender, adr, tel, email, impp, lang, tz, geo, note))

        connection.commit()
        connection.close()

    def insert_group_data(self, fake_data):
        """Inserts a single randomly generated group into the groups table."""
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        title = fake_data.catch_phrase() + " Group"
        org = fake_data.company()
        related = fake_data.word()
        url = fake_data.url()

        # logo BLOB is not generated for simplicity
        # For now, it will be NULL

        cursor.execute("""
        INSERT INTO groups (title, org, related, url)
        VALUES (?, ?, ?, ?)
        """, (title, org, related, url))

        connection.commit()
        connection.close()

    def generate_data(self, num_persons=10, num_groups=5):
        """
        Test function to generate random Person and Group data and insert it into the database.
        Args:
            num_persons (int): Number of random persons to generate.
            num_groups (int): Number of random groups to generate.
        """
        self.faker = self.Faker()
        print(f"Generating and inserting {num_persons} random persons...")
        for _ in range(num_persons):
            self.insert_person_data(self.faker)
        print(f"{num_persons} persons inserted.")

        print(f"Generating and inserting {num_groups} random groups...")
        for _ in range(num_groups):
            self.insert_group_data(self.faker)
        print(f"{num_groups} groups inserted.")
        print("Data generation complete!")



if __name__ == "__main__":
    print(f"Attempting to create tables at: {DB_PATH}")
    create_tables()
    print("Database setup complete.")

