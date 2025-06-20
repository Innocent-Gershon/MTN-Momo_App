import sqlite3

def get_db_connection():
    conn = sqlite3.connect('backend/data/momo.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with open('backend/schema.sql') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()