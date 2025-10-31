import sqlite3

def init_db(db_path='multimedia.db'):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            path TEXT,
            type TEXT,
            added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS extracted_text (
            id INTEGER PRIMARY KEY,
            file_id INTEGER,
            content TEXT,
            FOREIGN KEY(file_id) REFERENCES files(id)
        )
    ''')
    con.commit()
    con.close()

def insert_file(path, ftype, db_path='multimedia.db'):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("INSERT INTO files(path, type) VALUES (?, ?)", (path, ftype))
    file_id = cur.lastrowid
    con.commit()
    con.close()
    return file_id

def insert_text(file_id, content, db_path='multimedia.db'):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("INSERT INTO extracted_text(file_id, content) VALUES (?, ?)", (file_id, content))
    con.commit()
    con.close()

def search_text(query, db_path='multimedia.db'):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT f.path, e.content FROM files AS f JOIN extracted_text AS e ON f.id = e.file_id WHERE e.content LIKE ?", ('%'+query+'%',))
    results = cur.fetchall()
    con.close()
    return results

def get_recent_contents(limit=1, db_path='multimedia.db'):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT f.path, e.content FROM files AS f JOIN extracted_text AS e ON f.id = e.file_id ORDER BY f.added DESC LIMIT ?",
        (limit,)
    )
    results = cur.fetchall()
    con.close()
    return results
