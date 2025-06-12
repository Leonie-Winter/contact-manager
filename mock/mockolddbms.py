import sqlite3


DB_PATH = 'dbms/contacts.db'

def create_tables():
    """Create the necessary tables in the SQLite database."""
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

    if category == "Persons":
        cursor.execute("SELECT person_id, fn FROM persons")
    elif category == "Groups":
        cursor.execute("SELECT group_id, title FROM groups")

    # Convert the results into a dictionary
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

    # Execute the query to fetch the item
    if category == "Persons":
        cursor.execute(f"SELECT * FROM persons WHERE person_id = ?", (item_id,))
    elif category == "Groups":
        cursor.execute(f"SELECT * FROM groups WHERE group_id = ?", (item_id,))
    else:
        print(f"Unknown category: {category}")
        conn.close()
        return None
    
    # Fetch the result
    result = cursor.fetchone()

    if result:
        # Get column names from cursor description
        # cursor.description returns a list of tuples, where each tuple contains
        # (column_name, type_code, display_size, internal_size, precision, scale, null_ok)
        column_names = [description[0] for description in cursor.description]

        # Combine column names with row values into a dictionary
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

    if category == "Persons":
        cursor.execute("PRAGMA table_info(persons)")
    elif category == "Groups":
        cursor.execute("PRAGMA table_info(groups)")
    else:
        print(f"Unknown category: {category}")
        conn.close()
        return []

    # Fetch the results
    attributes = cursor.fetchall()
    conn.close()

    # Return a list of (name, type) tuples
    return [(attr[1], attr[2]) for attr in attributes]

def save_item_data(category, item_id, data):
    raise NotImplementedError("This function is not implemented yet.")


# def add_character(category,new_data):
#     conn = sqlite3.connect('datenbank.db')
#     cursor = conn.cursor()
#     if category == 'persons':
#         cursor.execute("INSERT INTO persons (person_id ,name,birthday,gender,since,photo,number,email,timezone,note) VALUES (new_data[0],new_data[1],new_data[2],new_data[3],new_data[4],new_data[5],new_data[6],new_data[7],new_data[8],new_data[9],)")
#     else:
#         cursor.execute("INSERT INTO groups (group_id,mem_amount,name,logo,organisation) VALUES (new_data[0],new_data[1],new_data[2],new_data[3],new_data[4])")
#     conn.close()
    
# def delete_character(category,id):
#     conn = sqlite3.connect('datenbank.db')
#     cursor = conn.cursor()
    
#     if category == "Persons":
#         cursor.execute("DELETE FROM persons WHERE person_id =: person_id",{'person_id':id})
#     elif category == "Groups":
#         cursor.execute("DELETE FROM group WHERE group_id =: group_id",{'group_id':id})
#     conn.close()


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
    create_tables()


    # --- Test the database functions ---

    clear_tables()  # Clear existing data before running tests
    test = Tests()
    Tests().generate_data(num_persons=20, num_groups=10) # Generate 20 persons and 10 groups
    print("\n--- Fetched Persons ---")
    persons = get_all_items_ids_and_names("Persons")
    for person_id, fn in persons.items():
        print(f"ID: {person_id}, Name: {fn}")

    print("\n--- Fetched Groups ---")
    groups = get_all_items_ids_and_names("Groups")
    for group_id, title in groups.items():
        print(f"ID: {group_id}, Title: {title}")
