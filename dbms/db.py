import sqlite3

DB_PATH = 'dbms/contacts.db'

def create_tables():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact (
        contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        contact_id INTEGER,
        group_id INTEGER,
        role_id INTEGER,
        FOREIGN KEY(contact_id) REFERENCES contact(contact_id),
        FOREIGN KEY(group_id) REFERENCES groups(group_id),
        FOREIGN KEY(role_id) REFERENCES role(role_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS other (
        other_id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER,
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
        FOREIGN KEY(contact_id) REFERENCES contact(contact_id)
    )
    """)



    connection.commit()
    connection.close()
    print("Tables created successfully.")

if __name__ == "__main__":
    create_tables()
