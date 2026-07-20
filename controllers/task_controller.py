from database import Database
import json
from datetime import datetime

class TaskController:
    def __init__(self):
        self.db = Database()
        self.current_filter = None
        self.current_search = None
        self.current_project = None
    
    def get_tasks(self, filter_type=None, search_query=None, project_id=None):
        """Get tasks with optional filtering"""
        self.current_filter = filter_type
        self.current_search = search_query
        self.current_project = project_id
        return self.db.get_tasks(filter_type, search_query, project_id)
    
    def get_statistics(self):
        """Get task statistics"""
        return self.db.get_statistics()
    
    def toggle_task(self, task_id, checked):
        """Toggle task completion status"""
        self.db.update_task(task_id, checked=checked)
    
    def add_task(self, content, description="", due_date=None, priority=1, labels="", project_id=None):
        """Add a new task"""
        return self.db.add_task(
            content=content,
            description=description,
            due=due_date,
            priority=priority,
            labels=labels,
            project_id=project_id
        )
    
    def update_task(self, task_id, **kwargs):
        """Update task properties"""
        if 'due_date' in kwargs:
            due_date = kwargs.pop('due_date')
            if due_date:
                kwargs['due'] = json.dumps({
                    "date": due_date,
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
            else:
                kwargs['due'] = None
        
        self.db.update_task(task_id, **kwargs)
    
    def delete_task(self, task_id):
        """Delete a task (soft delete)"""
        self.db.delete_task(task_id)
    
    def get_projects(self):
        """Get available projects"""
        return self.db.get_projects()