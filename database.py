import sqlite3
from config import DATABASE   # database path from config.py

def connect():   # connect to the database
    return sqlite3.connect(DATABASE)



def get_tasks():
    conn = connect()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            content,
            checked,
            priority
        FROM Items
        WHERE is_deleted = 0
        ORDER BY priority DESC;
    """)
    
    rows = cursor.fetchall()

    conn.close()
    
    return rows

def update_task(task_id, checked):

    conn = connect()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE Items
        SET checked = ?
        WHERE id = ?
        """,
        (int(checked), task_id),
    )

    conn.commit()

    conn.close()
