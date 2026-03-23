from flask import Flask, render_template, request, jsonify
from datetime import datetime
from models import db, Agent, Project, Task, ActivityLog

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def log_activity(project_id, message, activity_type='update'):
    """Helper function to log activities."""
    activity = ActivityLog(project_id=project_id, message=message, activity_type=activity_type)
    db.session.add(activity)
    db.session.commit()


# Initialize database and add default agents
def init_db():
    with app.app_context():
        db.create_all()
        
        # Add default AI agents if none exist
        if Agent.query.count() == 0:
            default_agents = [
                Agent(name='Claude Code', type='claude', avatar_color='#d97706'),
                Agent(name='GPT-4', type='openai', avatar_color='#10b981'),
                Agent(name='Gemini', type='google', avatar_color='#6366f1'),
                Agent(name='Cursor', type='cursor', avatar_color='#ec4899'),
                Agent(name='Windsurf', type='windsurf', avatar_color='#8b5cf6'),
            ]
            for agent in default_agents:
                db.session.add(agent)
            db.session.commit()
            print("Default agents created!")


# ==================== ROUTES ====================

@app.route('/')
def dashboard():
    """Main dashboard view."""
    return render_template('dashboard.html')


@app.route('/kanban')
def kanban():
    """Kanban board view."""
    return render_template('kanban.html')


@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Project detail view."""
    project = Project.query.get_or_404(project_id)
    activities = ActivityLog.query.filter_by(project_id=project_id).order_by(ActivityLog.timestamp.desc()).limit(20).all()
    return render_template('project.html', project=project, activities=activities)


# ==================== API ENDPOINTS ====================

# --- Agents API ---

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get all agents."""
    agents = Agent.query.all()
    return jsonify([a.to_dict() for a in agents])


@app.route('/api/agents', methods=['POST'])
def create_agent():
    """Create a new agent."""
    data = request.json
    agent = Agent(
        name=data['name'],
        type=data.get('type', 'custom'),
        avatar_color=data.get('avatar_color', '#6366f1')
    )
    db.session.add(agent)
    db.session.commit()
    return jsonify(agent.to_dict()), 201


# --- Projects API ---

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects with optional filtering."""
    status = request.args.get('status')
    agent_id = request.args.get('agent_id')
    
    query = Project.query
    if status:
        query = query.filter_by(status=status)
    if agent_id:
        query = query.filter_by(agent_id=agent_id)
    
    projects = query.order_by(Project.updated_at.desc()).all()
    return jsonify([p.to_dict() for p in projects])


@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project."""
    data = request.json
    project = Project(
        name=data['name'],
        description=data.get('description', ''),
        status=data.get('status', 'planning'),
        agent_id=data.get('agent_id'),
        notes=data.get('notes', '')
    )
    db.session.add(project)
    db.session.commit()
    
    log_activity(project.id, f"Project '{project.name}' created", 'update')
    return jsonify(project.to_dict()), 201


@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get a single project with tasks."""
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict(include_tasks=True))


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update a project."""
    project = Project.query.get_or_404(project_id)
    data = request.json
    
    old_status = project.status
    old_agent_id = project.agent_id
    
    if 'name' in data:
        project.name = data['name']
    if 'description' in data:
        project.description = data['description']
    if 'status' in data:
        project.status = data['status']
    if 'agent_id' in data:
        project.agent_id = data['agent_id']
    if 'notes' in data:
        project.notes = data['notes']
    
    project.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Log status changes
    if 'status' in data and old_status != data['status']:
        log_activity(project.id, f"Status changed from {old_status} to {data['status']}", 'status_change')
    
    # Log agent changes
    if 'agent_id' in data and old_agent_id != data['agent_id']:
        agent = Agent.query.get(data['agent_id'])
        if agent:
            log_activity(project.id, f"Assigned to {agent.name}", 'update')
    
    return jsonify(project.to_dict())


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project."""
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'})


# --- Tasks API ---

@app.route('/api/projects/<int:project_id>/tasks', methods=['GET'])
def get_tasks(project_id):
    """Get all tasks for a project."""
    tasks = Task.query.filter_by(project_id=project_id).order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks])


@app.route('/api/projects/<int:project_id>/tasks', methods=['POST'])
def create_task(project_id):
    """Create a new task."""
    project = Project.query.get_or_404(project_id)
    data = request.json
    
    task = Task(
        project_id=project_id,
        title=data['title'],
        description=data.get('description', ''),
        status=data.get('status', 'pending'),
        priority=data.get('priority', 'medium')
    )
    db.session.add(task)
    db.session.commit()
    
    log_activity(project_id, f"Task '{task.title}' created", 'update')
    return jsonify(task.to_dict()), 201


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task."""
    task = Task.query.get_or_404(task_id)
    data = request.json
    
    old_status = task.status
    
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = data['status']
    if 'priority' in data:
        task.priority = data['priority']
    
    if 'status' in data and old_status != data['status'] and data['status'] == 'completed':
        task.completed_at = datetime.utcnow()
        log_activity(task.project_id, f"Task '{task.title}' completed", 'task_complete')
    
    db.session.commit()
    return jsonify(task.to_dict())


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task."""
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully'})


# --- Activity Log API ---

@app.route('/api/projects/<int:project_id>/activities', methods=['GET'])
def get_activities(project_id):
    """Get activity log for a project."""
    activities = ActivityLog.query.filter_by(project_id=project_id).order_by(ActivityLog.timestamp.desc()).limit(50).all()
    return jsonify([a.to_dict() for a in activities])


@app.route('/api/projects/<int:project_id>/activities', methods=['POST'])
def create_activity(project_id):
    """Manually add an activity."""
    project = Project.query.get_or_404(project_id)
    data = request.json
    
    activity = ActivityLog(
        project_id=project_id,
        message=data['message'],
        activity_type=data.get('activity_type', 'note')
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify(activity.to_dict()), 201


# --- Dashboard Stats API ---

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics."""
    total_projects = Project.query.count()
    projects_by_status = {}
    for status in ['planning', 'in_progress', 'review', 'complete', 'on_hold']:
        count = Project.query.filter_by(status=status).count()
        projects_by_status[status] = count
    
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='completed').count()
    
    recent_activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    return jsonify({
        'total_projects': total_projects,
        'projects_by_status': projects_by_status,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'recent_activities': [a.to_dict() for a in recent_activities]
    })


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
