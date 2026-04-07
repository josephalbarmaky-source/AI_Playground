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


# ==================== MEETING ASSISTANT MODELS ====================

class Meeting(db.Model):
    """A recorded meeting session."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    meeting_type = db.Column(db.String(20), default='work')  # 'school' or 'work'
    platform = db.Column(db.String(50), default='teams')
    status = db.Column(db.String(20), default='live')  # 'live', 'processing', 'complete'
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)

    transcripts = db.relationship('TranscriptSegment', backref='meeting', lazy=True, cascade='all, delete-orphan')
    screenshots = db.relationship('Screenshot', backref='meeting', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('MeetingNotes', backref='meeting', uselist=False, cascade='all, delete-orphan')
    chats = db.relationship('ChatMessage', backref='meeting', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, include_details=False):
        result = {
            'id': self.id,
            'title': self.title,
            'meeting_type': self.meeting_type,
            'platform': self.platform,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'duration_minutes': self.duration_minutes,
            'transcript_count': len(self.transcripts),
            'screenshot_count': len(self.screenshots),
            'has_notes': self.notes is not None
        }
        if include_details:
            result['transcripts'] = [t.to_dict() for t in self.transcripts]
            result['screenshots'] = [s.to_dict() for s in self.screenshots]
            result['notes'] = self.notes.to_dict() if self.notes else None
        return result


class TranscriptSegment(db.Model):
    """A segment of transcribed speech from a meeting."""
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp_sec = db.Column(db.Float)  # seconds from meeting start
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'text': self.text,
            'timestamp_sec': self.timestamp_sec,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Screenshot(db.Model):
    """A screenshot captured during a meeting."""
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    timestamp_sec = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'file_path': self.file_path,
            'timestamp_sec': self.timestamp_sec,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


import json

class MeetingNotes(db.Model):
    """AI-generated notes for a meeting."""
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False, unique=True)
    summary = db.Column(db.Text)
    topics = db.Column(db.Text)           # JSON array
    action_items = db.Column(db.Text)     # JSON array
    upcoming_tasks = db.Column(db.Text)   # JSON array (exams, deadlines, homework)
    key_decisions = db.Column(db.Text)    # JSON array
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'summary': self.summary,
            'topics': json.loads(self.topics) if self.topics else [],
            'action_items': json.loads(self.action_items) if self.action_items else [],
            'upcoming_tasks': json.loads(self.upcoming_tasks) if self.upcoming_tasks else [],
            'key_decisions': json.loads(self.key_decisions) if self.key_decisions else [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ChatMessage(db.Model):
    """A chatbot Q&A interaction about meeting content."""
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=True)  # null = cross-meeting query
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'question': self.question,
            'answer': self.answer,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
