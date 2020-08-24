"""
Sqlite3 interaction.
"""
import sqlite3
from sqlite3 import Error

def create_connection(path='db.sqlite'):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print('Connection to SQLite DB successful')
    except Error as e:
        print(f'The error {e} occured')
    
    return connection


def execute_query(connection, query, *args):
    cursor = connection.cursor()
    try:
        cursor.execute(query, args)
        connection.commit()
        print('Query executed successfully')
    except Error as e:
        print(f'The error {e} occured')

def execute_read_query(connection, query, *args):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query, args)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f'The error {e} occured')


# Initial creation of db
def create_db():
    """Initial creation of db."""
    connection = create_connection()
    create_entries_table = """
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        description TEXT
    );
    """
    execute_query(connection, create_entries_table)


# Managing entries
def save_entry(subject, user_id, description):
    """Saves entry to Database."""
    connection = create_connection()
    save_query = f"""
    INSERT INTO entries (user_id, subject, description)
    VALUES (?, ?, ?);
    """
    execute_query(connection, save_query, user_id, subject, description)


def delete_entry_from_db(subject, user_id):
    """Deletes entry from database."""
    connection = create_connection()
    delete_query = """
    DELETE FROM entries WHERE subject = (?) AND user_id = (?)
    """
    execute_query(connection, delete_query, subject, user_id)


def get_all_entries(user_id):
    """Returns list of all users's entries."""
    connection = create_connection()
    all_entries_query = """
    SELECT subject FROM entries WHERE user_id = (?);
    """
    all_entries = execute_read_query(connection, all_entries_query, user_id)

    for i in range(len(all_entries)):
        all_entries[i] = all_entries[i][0]
    
    return all_entries
    

def get_entry_to_remind(subject, user_id):
    """Returns subject and description of entry"""

    connection = create_connection()
    get_description_query = f"""
    SELECT description FROM entries WHERE subject = (?)
    AND user_id = (?);
    """
    description = execute_read_query(connection, get_description_query,
                                     subject, user_id)[0][0]
                                     
    return (subject, description)