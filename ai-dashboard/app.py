from flask import Flask, render_template, request, jsonify
from datetime import datetime
from models import db, Agent, Project, Task, ActivityLog, ScheduleEvent, GroceryItem, HouseInfo, FamilyActivity

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


# ==================== FAMILY DASHBOARD ====================

@app.route('/family')
def family_dashboard():
    """Family home dashboard - standalone full-screen view."""
    return render_template('family-dashboard.html')


# --- Family Schedule API ---

@app.route('/api/family/schedule', methods=['GET'])
def get_schedule():
    events = ScheduleEvent.query.order_by(ScheduleEvent.day_of_week, ScheduleEvent.start_time).all()
    return jsonify([e.to_dict() for e in events])


@app.route('/api/family/schedule', methods=['POST'])
def create_schedule_event():
    data = request.json
    event = ScheduleEvent(
        title=data['title'],
        day_of_week=data['day_of_week'],
        start_time=data['start_time'],
        end_time=data['end_time'],
        location=data.get('location'),
        color=data.get('color', '#6366f1')
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201


@app.route('/api/family/schedule/<int:event_id>', methods=['PUT'])
def update_schedule_event(event_id):
    event = ScheduleEvent.query.get_or_404(event_id)
    data = request.json
    for field in ['title', 'day_of_week', 'start_time', 'end_time', 'location', 'color']:
        if field in data:
            setattr(event, field, data[field])
    db.session.commit()
    return jsonify(event.to_dict())


@app.route('/api/family/schedule/<int:event_id>', methods=['DELETE'])
def delete_schedule_event(event_id):
    event = ScheduleEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({'message': 'Event deleted'})


# --- Family Grocery API ---

@app.route('/api/family/grocery', methods=['GET'])
def get_grocery():
    query = GroceryItem.query
    checked = request.args.get('checked')
    if checked == 'false':
        query = query.filter_by(is_checked=False)
    items = query.order_by(GroceryItem.is_checked, GroceryItem.category, GroceryItem.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])


@app.route('/api/family/grocery', methods=['POST'])
def create_grocery_item():
    data = request.json
    item = GroceryItem(
        name=data['name'],
        category=data.get('category', 'general'),
        quantity=data.get('quantity'),
        added_by=data.get('added_by')
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@app.route('/api/family/grocery/<int:item_id>', methods=['PUT'])
def update_grocery_item(item_id):
    item = GroceryItem.query.get_or_404(item_id)
    data = request.json
    for field in ['name', 'category', 'quantity', 'is_checked', 'added_by']:
        if field in data:
            setattr(item, field, data[field])
    db.session.commit()
    return jsonify(item.to_dict())


@app.route('/api/family/grocery/<int:item_id>', methods=['DELETE'])
def delete_grocery_item(item_id):
    item = GroceryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted'})


@app.route('/api/family/grocery/checked', methods=['DELETE'])
def clear_checked_grocery():
    GroceryItem.query.filter_by(is_checked=True).delete()
    db.session.commit()
    return jsonify({'message': 'Checked items cleared'})


# --- Family House Info API ---

@app.route('/api/family/house-info', methods=['GET'])
def get_house_info():
    entries = HouseInfo.query.order_by(HouseInfo.category, HouseInfo.sort_order).all()
    return jsonify([e.to_dict() for e in entries])


@app.route('/api/family/house-info', methods=['POST'])
def create_house_info():
    data = request.json
    entry = HouseInfo(
        category=data['category'],
        label=data['label'],
        value=data['value'],
        icon=data.get('icon'),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201


@app.route('/api/family/house-info/<int:entry_id>', methods=['PUT'])
def update_house_info(entry_id):
    entry = HouseInfo.query.get_or_404(entry_id)
    data = request.json
    for field in ['category', 'label', 'value', 'icon', 'sort_order']:
        if field in data:
            setattr(entry, field, data[field])
    db.session.commit()
    return jsonify(entry.to_dict())


@app.route('/api/family/house-info/<int:entry_id>', methods=['DELETE'])
def delete_house_info(entry_id):
    entry = HouseInfo.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'message': 'Entry deleted'})


# --- Family Activity API ---

@app.route('/api/family/activities', methods=['GET'])
def get_family_activities():
    activities = FamilyActivity.query.order_by(FamilyActivity.timestamp.desc()).limit(50).all()
    return jsonify([a.to_dict() for a in activities])


@app.route('/api/family/activities', methods=['POST'])
def create_family_activity():
    data = request.json
    activity = FamilyActivity(
        member=data['member'],
        message=data['message'],
        activity_type=data.get('activity_type', 'general')
    )
    db.session.add(activity)
    db.session.commit()
    return jsonify(activity.to_dict()), 201


@app.route('/api/family/activities/<int:activity_id>', methods=['DELETE'])
def delete_family_activity(activity_id):
    activity = FamilyActivity.query.get_or_404(activity_id)
    db.session.delete(activity)
    db.session.commit()
    return jsonify({'message': 'Activity deleted'})


# --- Family Dashboard Aggregate + Utility ---

@app.route('/api/family/dashboard-data', methods=['GET'])
def get_family_dashboard_data():
    schedule = ScheduleEvent.query.order_by(ScheduleEvent.day_of_week, ScheduleEvent.start_time).all()
    grocery = GroceryItem.query.order_by(GroceryItem.is_checked, GroceryItem.category, GroceryItem.created_at.desc()).all()
    house_info = HouseInfo.query.order_by(HouseInfo.category, HouseInfo.sort_order).all()
    activities = FamilyActivity.query.order_by(FamilyActivity.timestamp.desc()).limit(50).all()
    return jsonify({
        'schedule': [e.to_dict() for e in schedule],
        'grocery': [i.to_dict() for i in grocery],
        'house_info': [e.to_dict() for e in house_info],
        'activities': [a.to_dict() for a in activities],
        'server_time': datetime.utcnow().isoformat()
    })


@app.route('/api/family/ping', methods=['GET'])
def family_ping():
    return jsonify({'ok': True, 'timestamp': datetime.utcnow().isoformat()})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
