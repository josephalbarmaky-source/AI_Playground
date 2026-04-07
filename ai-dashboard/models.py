from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Agent(db.Model):
    """AI Agent model - tracks different AI agents like Claude, GPT, etc."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., 'claude', 'gpt4', 'gemini'
    avatar_color = db.Column(db.String(20), default='#6366f1')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='agent', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'avatar_color': self.avatar_color,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Project(db.Model):
    """Project model - tracks projects being worked on by AI agents."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='planning')  # planning, in_progress, review, complete, on_hold
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    activities = db.relationship('ActivityLog', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_tasks=False):
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'agent_id': self.agent_id,
            'agent': self.agent.to_dict() if self.agent else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'task_count': len(self.tasks),
            'completed_task_count': len([t for t in self.tasks if t.status == 'completed'])
        }
        if include_tasks:
            result['tasks'] = [t.to_dict() for t in self.tasks]
        return result


class Task(db.Model):
    """Task model - subtasks within a project."""
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class ActivityLog(db.Model):
    """Activity log - tracks all activities across projects."""
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    activity_type = db.Column(db.String(50), default='update')  # update, task_complete, blocker, note, status_change
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'message': self.message,
            'activity_type': self.activity_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


# ==================== FAMILY DASHBOARD MODELS ====================

class ScheduleEvent(db.Model):
    """School schedule events."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday .. 6=Sunday
    start_time = db.Column(db.String(5), nullable=False)  # "08:30" HH:MM
    end_time = db.Column(db.String(5), nullable=False)    # "09:15"
    location = db.Column(db.String(200))
    color = db.Column(db.String(20), default='#6366f1')
    week_type = db.Column(db.String(1), default='A')  # 'A' or 'B' for rotating timetable
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'location': self.location,
            'color': self.color,
            'week_type': self.week_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CalendarEvent(db.Model):
    """One-off calendar events (tutoring, appointments, etc.)."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # "2026-04-07" YYYY-MM-DD
    start_time = db.Column(db.String(5), nullable=False)  # "16:00"
    end_time = db.Column(db.String(5))  # optional
    location = db.Column(db.String(200))
    color = db.Column(db.String(20), default='#f59e0b')
    event_type = db.Column(db.String(50), default='tutor')  # tutor, appointment, other
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'location': self.location,
            'color': self.color,
            'event_type': self.event_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class GroceryItem(db.Model):
    """Grocery list items."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='general')  # produce, dairy, meat, pantry, frozen, general
    quantity = db.Column(db.String(50))
    is_checked = db.Column(db.Boolean, default=False)
    added_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'quantity': self.quantity,
            'is_checked': self.is_checked,
            'added_by': self.added_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class HouseInfo(db.Model):
    """General household information entries."""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # wifi, emergency, utilities, codes, contacts
    label = db.Column(db.String(200), nullable=False)
    value = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(10))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'label': self.label,
            'value': self.value,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class FamilyActivity(db.Model):
    """Family activity feed."""
    id = db.Column(db.Integer, primary_key=True)
    member = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    activity_type = db.Column(db.String(50), default='general')  # general, chore, event, reminder, note
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'member': self.member,
            'message': self.message,
            'activity_type': self.activity_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
