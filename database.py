import sqlite3
import os
import json
import uuid
from config import DATABASE

class Database:
    def __init__(self):
        self.db_path = str(DATABASE)
    
    def connect(self):
        """Create database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_tasks(self, filter_type=None):
        """Get tasks with optional filtering"""
        conn = self.connect()
        cursor = conn.cursor()
        
        base_query = """
            SELECT id, content, description, due, priority, 
                   checked, labels, project_id, pinned
            FROM Items 
            WHERE is_deleted = 0
        """
        
        if filter_type == "today":
            base_query += " AND date(json_extract(due, '$.date')) = date('now')"
        elif filter_type == "upcoming":
            base_query += " AND date(json_extract(due, '$.date')) > date('now')"
        elif filter_type == "overdue":
            base_query += " AND date(json_extract(due, '$.date')) < date('now') AND checked = 0"
        elif filter_type == "completed":
            base_query += " AND checked = 1"
        elif filter_type == "high_priority":
            base_query += " AND priority = 3"
        
        base_query += " ORDER BY pinned DESC, priority DESC, due ASC"
        
        cursor.execute(base_query)
        tasks = cursor.fetchall()
        conn.close()
        
        return tasks
    
    def add_task(self, content, description="", due=None, priority=1, labels="", project_id=None):
        """Add a new task to the database"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Generate a UUID for the task
        task_id = str(uuid.uuid4())
        
        # Format due date as JSON
        due_json = None
        if due:
            due_json = json.dumps({
                "date": due,
                "recurrence_string": "",
                "timezone": "",
                "is_recurring": False,
                "recurrency_type": "6",
                "recurrency_interval": "0",
                "recurrency_weeks": "",
                "recurrency_count": "0",
                "recurrency_end": "",
                "recurrency_last_day_of_month": "false"
            })
        
        cursor.execute("""
            INSERT INTO Items (id, content, description, due, priority, labels, project_id, checked, is_deleted, pinned)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0)
        """, (task_id, content, description, due_json, priority, labels, project_id))
        
        conn.commit()
        conn.close()
        
        # Touch the file to trigger file monitors
        self._touch_db()
        
        return task_id
    
    def update_task(self, task_id, **kwargs):
        """Update task fields dynamically"""
        allowed_fields = ['content', 'description', 'due', 'priority', 'checked', 'labels', 'project_id', 'pinned']
        
        updates = []
        params = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                params.append(value)
        
        if not updates:
            return
        
        params.append(task_id)
        
        conn = self.connect()
        cursor = conn.cursor()
        
        query = f"UPDATE Items SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        
        conn.commit()
        conn.close()
        
        # Touch the file to trigger file monitors
        self._touch_db()
    
    def delete_task(self, task_id):
        """Soft delete a task"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE Items SET is_deleted = 1 WHERE id = ?", (task_id,))
        
        conn.commit()
        conn.close()
        
        # Touch the file to trigger file monitors
        self._touch_db()
    
    def get_statistics(self):
        """Get task statistics"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN checked = 1 THEN 1 ELSE 0 END) as completed
            FROM Items 
            WHERE is_deleted = 0
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total': result[0] or 0,
            'completed': result[1] or 0
        }
    
    def get_projects(self):
        """Get list of projects"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM Projects WHERE is_deleted = 0")
        projects = cursor.fetchall()
        conn.close()
        
        return projects
    
    def _touch_db(self):
        """Touch the database file to trigger file monitors"""
        try:
            if os.path.exists(self.db_path):
                # Update access and modification times
                os.utime(self.db_path, None)
        except Exception as e:
            print(f"Error touching database file: {e}")