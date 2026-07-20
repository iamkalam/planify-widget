import sqlite3
import os
import json
import uuid
from datetime import datetime
from config import DATABASE

class Database:
    def __init__(self):
        self.db_path = str(DATABASE)
    
    def connect(self):
        """Create database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_tasks(self, filter_type=None, search_query=None, project_id=None):
        """Get tasks with Python-side filtering"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get all active tasks with project names
        query = """
            SELECT 
                i.id, i.content, i.description, i.due, i.priority, 
                i.checked, i.labels, i.project_id, i.pinned,
                p.name as project_name
            FROM Items i
            LEFT JOIN Projects p ON i.project_id = p.id
            WHERE i.is_deleted = 0
        """
        
        params = []
        
        # Apply search filter
        if search_query:
            query += " AND (i.content LIKE ? OR i.description LIKE ? OR i.labels LIKE ?)"
            search_param = f"%{search_query}%"
            params.extend([search_param, search_param, search_param])
        
        # Apply project filter
        if project_id:
            query += " AND i.project_id = ?"
            params.append(project_id)
        
        query += " ORDER BY i.pinned DESC, i.priority DESC, i.due ASC"
        
        cursor.execute(query, params)
        all_tasks = cursor.fetchall()
        conn.close()
        
        # Apply filters in Python instead of SQL
        if filter_type is None or filter_type == "all":
            return all_tasks
        
        filtered_tasks = []
        today = datetime.now().date()
        
        for task in all_tasks:
            due_date = self._extract_date(task[3])  # task[3] is due
            
            if filter_type == "today":
                if due_date and due_date == today:
                    filtered_tasks.append(task)
            elif filter_type == "upcoming":
                if due_date and due_date > today:
                    filtered_tasks.append(task)
            elif filter_type == "overdue":
                checked = task[5]  # task[5] is checked
                if due_date and due_date < today and not checked:
                    filtered_tasks.append(task)
            elif filter_type == "completed":
                if task[5]:  # checked
                    filtered_tasks.append(task)
            elif filter_type == "active":
                if not task[5]:  # not checked
                    filtered_tasks.append(task)
            elif filter_type == "high_priority":
                if task[4] == 3:  # priority
                    filtered_tasks.append(task)
            elif filter_type == "pinned":
                if task[8]:  # pinned
                    filtered_tasks.append(task)
        
        return filtered_tasks
    
    def _extract_date(self, due_raw):
        """Extract date from due field (JSON or plain string)"""
        if not due_raw:
            return None
        
        if isinstance(due_raw, bytes):
            due_raw = due_raw.decode('utf-8', errors='ignore')
        
        if not isinstance(due_raw, str) or not due_raw.strip():
            return None
        
        due_raw = due_raw.strip()
        
        # Try JSON format
        if due_raw.startswith('{'):
            try:
                due_data = json.loads(due_raw)
                if isinstance(due_data, dict) and 'date' in due_data:
                    date_str = due_data['date']
                    if date_str and date_str.strip():
                        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
            except:
                pass
        
        # Try plain date formats
        for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
            try:
                return datetime.strptime(due_raw, fmt).date()
            except:
                continue
        
        return None
    
    def add_task(self, content, description="", due=None, priority=1, labels="", project_id=None):
        """Add a new task to the database"""
        conn = self.connect()
        cursor = conn.cursor()
        
        task_id = str(uuid.uuid4())
        
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
        
        self._touch_db()
    
    def delete_task(self, task_id):
        """Soft delete a task"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE Items SET is_deleted = 1 WHERE id = ?", (task_id,))
        
        conn.commit()
        conn.close()
        
        self._touch_db()
    
    def get_statistics(self):
        """Get task statistics"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get all tasks and calculate stats in Python
        cursor.execute("""
            SELECT checked, due
            FROM Items 
            WHERE is_deleted = 0
        """)
        
        all_tasks = cursor.fetchall()
        conn.close()
        
        total = len(all_tasks)
        completed = 0
        overdue = 0
        today = 0
        
        today_date = datetime.now().date()
        
        for checked, due_raw in all_tasks:
            if checked:
                completed += 1
            else:
                due_date = self._extract_date(due_raw)
                if due_date:
                    if due_date < today_date:
                        overdue += 1
                    elif due_date == today_date:
                        today += 1
        
        return {
            'total': total,
            'completed': completed,
            'overdue': overdue,
            'today': today
        }
    
    def get_projects(self):
        """Get list of projects with task counts"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.id, 
                p.name,
                COUNT(i.id) as task_count
            FROM Projects p
            LEFT JOIN Items i ON p.id = i.project_id AND i.is_deleted = 0
            WHERE p.is_deleted = 0
            GROUP BY p.id, p.name
            ORDER BY p.name
        """)
        projects = cursor.fetchall()
        conn.close()
        
        return projects
    
    def _touch_db(self):
        """Touch the database file to trigger file monitors"""
        try:
            if os.path.exists(self.db_path):
                os.utime(self.db_path, None)
        except Exception as e:
            print(f"Error touching database file: {e}")