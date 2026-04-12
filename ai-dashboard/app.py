from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
import json
import os
import requests as http_requests
from models import db, Agent, Project, Task, ActivityLog, ScheduleEvent, CalendarEvent, GroceryItem, HouseInfo, FamilyActivity

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['GO4SCHOOLS_API_KEY'] = os.environ.get('GO4SCHOOLS_API_KEY', '')
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

        # Seed Ayan's timetable if no schedule events exist
        if ScheduleEvent.query.count() == 0:
            from seed_timetable import seed
            seed()

        # Seed tutoring sessions if no calendar events exist
        if CalendarEvent.query.count() == 0:
            from seed_tutoring import seed_tutoring
            seed_tutoring()


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

@app.route('/spinner')
def spinner_game():
    """Spinner game - Joseph, Marwan, and Ayan."""
    return render_template('spinner.html')


@app.route('/tools')
def tools_page():
    """AI tools overview page."""
    return render_template('tools.html')


# ==================== DABBAR LANDING PAGE PREVIEW ====================

DABBAR_SITE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'dabbar-site')
)
DABBAR_WAITLIST_FILE = os.path.join(os.path.dirname(__file__), 'dabbar_waitlist.jsonl')


@app.route('/dabbar-preview')
@app.route('/dabbar-preview/')
def dabbar_preview():
    """Preview the dabbar.ai landing page locally."""
    return send_from_directory(DABBAR_SITE_DIR, 'index.html')


@app.route('/dabbar-preview/<path:filename>')
def dabbar_preview_static(filename):
    """Serve static assets for the dabbar landing preview."""
    return send_from_directory(DABBAR_SITE_DIR, filename)


@app.route('/api/dabbar/waitlist', methods=['POST'])
def dabbar_waitlist():
    """Append a waitlist signup to dabbar_waitlist.jsonl."""
    data = request.json or {}
    tg = (data.get('tg') or '').strip()
    email = (data.get('email') or '').strip()
    if not tg or not email:
        return jsonify({'error': 'tg and email are required'}), 400
    entry = {
        'tg': tg,
        'email': email,
        'at': datetime.utcnow().isoformat() + 'Z',
        'ua': request.headers.get('User-Agent', ''),
    }
    with open(DABBAR_WAITLIST_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    return jsonify({'ok': True})


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
        color=data.get('color', '#6366f1'),
        week_type=data.get('week_type', 'A')
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201


@app.route('/api/family/schedule/<int:event_id>', methods=['PUT'])
def update_schedule_event(event_id):
    event = ScheduleEvent.query.get_or_404(event_id)
    data = request.json
    for field in ['title', 'day_of_week', 'start_time', 'end_time', 'location', 'color', 'week_type']:
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


# --- Family Calendar (one-off events) API ---

@app.route('/api/family/calendar', methods=['GET'])
def get_calendar_events():
    events = CalendarEvent.query.order_by(CalendarEvent.date, CalendarEvent.start_time).all()
    return jsonify([e.to_dict() for e in events])


@app.route('/api/family/calendar', methods=['POST'])
def create_calendar_event():
    data = request.json
    event = CalendarEvent(
        title=data['title'],
        date=data['date'],
        start_time=data['start_time'],
        end_time=data.get('end_time'),
        location=data.get('location'),
        color=data.get('color', '#f59e0b'),
        event_type=data.get('event_type', 'tutor')
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201


@app.route('/api/family/calendar/<int:event_id>', methods=['PUT'])
def update_calendar_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    data = request.json
    for field in ['title', 'date', 'start_time', 'end_time', 'location', 'color', 'event_type']:
        if field in data:
            setattr(event, field, data[field])
    db.session.commit()
    return jsonify(event.to_dict())


@app.route('/api/family/calendar/<int:event_id>', methods=['DELETE'])
def delete_calendar_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({'message': 'Calendar event deleted'})


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
    calendar = CalendarEvent.query.order_by(CalendarEvent.date, CalendarEvent.start_time).all()
    grocery = GroceryItem.query.order_by(GroceryItem.is_checked, GroceryItem.category, GroceryItem.created_at.desc()).all()
    house_info = HouseInfo.query.order_by(HouseInfo.category, HouseInfo.sort_order).all()
    activities = FamilyActivity.query.order_by(FamilyActivity.timestamp.desc()).limit(50).all()
    return jsonify({
        'schedule': [e.to_dict() for e in schedule],
        'calendar_events': [e.to_dict() for e in calendar],
        'grocery': [i.to_dict() for i in grocery],
        'house_info': [e.to_dict() for e in house_info],
        'activities': [a.to_dict() for a in activities],
        'server_time': datetime.utcnow().isoformat()
    })


@app.route('/api/family/ping', methods=['GET'])
def family_ping():
    return jsonify({'ok': True, 'timestamp': datetime.utcnow().isoformat()})


# --- Go4Schools Integration ---

def g4s_request(endpoint):
    """Make an authenticated request to the Go4Schools API."""
    api_key = app.config.get('GO4SCHOOLS_API_KEY', '')
    if not api_key:
        return None
    try:
        resp = http_requests.get(
            f'https://api.go4schools.com/api/{endpoint}',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f'Go4Schools API error: {e}')
        return None


@app.route('/api/family/g4s/status', methods=['GET'])
def g4s_status():
    """Check if Go4Schools API key is configured."""
    key = app.config.get('GO4SCHOOLS_API_KEY', '')
    return jsonify({'connected': bool(key)})


@app.route('/api/family/g4s/setup', methods=['POST'])
def g4s_setup():
    """Save Go4Schools API key."""
    data = request.json
    key = data.get('api_key', '').strip()
    app.config['GO4SCHOOLS_API_KEY'] = key
    # Also persist to .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = [l for l in f.readlines() if not l.startswith('GO4SCHOOLS_API_KEY=')]
    lines.append(f'GO4SCHOOLS_API_KEY={key}\n')
    with open(env_path, 'w') as f:
        f.writelines(lines)
    return jsonify({'connected': bool(key)})


@app.route('/api/family/g4s/timetable', methods=['GET'])
def g4s_timetable():
    """Get student timetable from Go4Schools."""
    data = g4s_request('Timetable')
    if data is None:
        return jsonify({'error': 'Not connected or API error', 'events': []}), 200
    return jsonify(data)


@app.route('/api/family/g4s/homework', methods=['GET'])
def g4s_homework():
    """Get homework/tasks from Go4Schools."""
    data = g4s_request('Homework')
    if data is None:
        return jsonify({'error': 'Not connected or API error', 'items': []}), 200
    return jsonify(data)


@app.route('/api/family/g4s/attendance', methods=['GET'])
def g4s_attendance():
    """Get attendance summary from Go4Schools."""
    data = g4s_request('Attendance/SessionMarks')
    if data is None:
        return jsonify({'error': 'Not connected or API error', 'marks': []}), 200
    return jsonify(data)


@app.route('/api/family/g4s/grades', methods=['GET'])
def g4s_grades():
    """Get student grades/marks from Go4Schools."""
    data = g4s_request('Assessment/Marks')
    if data is None:
        return jsonify({'error': 'Not connected or API error', 'marks': []}), 200
    return jsonify(data)


# --- Google Photos Integration ---

GOOGLE_PHOTOS_SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

@app.route('/api/family/photos/status', methods=['GET'])
def photos_status():
    """Check if Google Photos is connected."""
    token_path = os.path.join(os.path.dirname(__file__), '.google_photos_token.json')
    client_id = os.environ.get('GOOGLE_CLIENT_ID', app.config.get('GOOGLE_CLIENT_ID', ''))
    return jsonify({
        'connected': os.path.exists(token_path),
        'configured': bool(client_id)
    })


@app.route('/api/family/photos/setup', methods=['POST'])
def photos_setup():
    """Save Google OAuth client credentials."""
    data = request.json
    client_id = data.get('client_id', '').strip()
    client_secret = data.get('client_secret', '').strip()
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = [l for l in f.readlines() if not l.startswith('GOOGLE_CLIENT_ID=') and not l.startswith('GOOGLE_CLIENT_SECRET=')]
    lines.append(f'GOOGLE_CLIENT_ID={client_id}\n')
    lines.append(f'GOOGLE_CLIENT_SECRET={client_secret}\n')
    with open(env_path, 'w') as f:
        f.writelines(lines)
    app.config['GOOGLE_CLIENT_ID'] = client_id
    app.config['GOOGLE_CLIENT_SECRET'] = client_secret
    return jsonify({'configured': True})


@app.route('/api/family/photos/auth-url', methods=['GET'])
def photos_auth_url():
    """Generate Google OAuth authorization URL."""
    from google_auth_oauthlib.flow import Flow
    client_id = os.environ.get('GOOGLE_CLIENT_ID', app.config.get('GOOGLE_CLIENT_ID', ''))
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', app.config.get('GOOGLE_CLIENT_SECRET', ''))
    if not client_id or not client_secret:
        return jsonify({'error': 'Google credentials not configured'}), 400
    flow = Flow.from_client_config(
        {'web': {
            'client_id': client_id,
            'client_secret': client_secret,
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
        }},
        scopes=GOOGLE_PHOTOS_SCOPES,
        redirect_uri=request.host_url.rstrip('/') + '/api/family/photos/callback'
    )
    auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
    return jsonify({'auth_url': auth_url})


@app.route('/api/family/photos/callback', methods=['GET'])
def photos_callback():
    """Handle Google OAuth callback and store tokens."""
    from google_auth_oauthlib.flow import Flow
    import json
    client_id = os.environ.get('GOOGLE_CLIENT_ID', app.config.get('GOOGLE_CLIENT_ID', ''))
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', app.config.get('GOOGLE_CLIENT_SECRET', ''))
    flow = Flow.from_client_config(
        {'web': {
            'client_id': client_id,
            'client_secret': client_secret,
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
        }},
        scopes=GOOGLE_PHOTOS_SCOPES,
        redirect_uri=request.host_url.rstrip('/') + '/api/family/photos/callback'
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': list(creds.scopes),
    }
    token_path = os.path.join(os.path.dirname(__file__), '.google_photos_token.json')
    with open(token_path, 'w') as f:
        json.dump(token_data, f)
    return '<html><body><h2>Connected! You can close this tab.</h2><script>window.close()</script></body></html>'


def get_photos_creds():
    """Load and refresh Google Photos credentials."""
    import json
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    token_path = os.path.join(os.path.dirname(__file__), '.google_photos_token.json')
    if not os.path.exists(token_path):
        return None
    with open(token_path, 'r') as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data['token'],
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret'),
        scopes=token_data.get('scopes'),
    )
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        token_data['token'] = creds.token
        with open(token_path, 'w') as f:
            json.dump(token_data, f)
    return creds


@app.route('/api/family/photos/recent', methods=['GET'])
def photos_recent():
    """Get recent photos from Google Photos."""
    creds = get_photos_creds()
    if not creds:
        return jsonify({'error': 'Not connected', 'photos': []}), 200
    count = request.args.get('count', 20, type=int)
    resp = http_requests.post(
        'https://photoslibrary.googleapis.com/v1/mediaItems:search',
        headers={'Authorization': f'Bearer {creds.token}'},
        json={'pageSize': min(count, 50), 'orderBy': 'MediaMetadata.creation_time desc'},
        timeout=10
    )
    if resp.status_code != 200:
        return jsonify({'error': 'API error', 'photos': []}), 200
    data = resp.json()
    photos = []
    for item in data.get('mediaItems', []):
        meta = item.get('mediaMetadata', {})
        photo = {
            'id': item['id'],
            'url': item.get('baseUrl', '') + '=w800-h600',
            'thumbnail': item.get('baseUrl', '') + '=w200-h200-c',
            'filename': item.get('filename', ''),
            'created': meta.get('creationTime', ''),
            'width': meta.get('width'),
            'height': meta.get('height'),
        }
        if 'photo' in meta:
            photo['camera'] = meta['photo'].get('cameraModel', '')
        if 'location' in meta:
            photo['location'] = {
                'lat': meta['location'].get('latitude'),
                'lng': meta['location'].get('longitude'),
            }
        photos.append(photo)
    return jsonify({'photos': photos})


@app.route('/api/family/photos/search', methods=['GET'])
def photos_search():
    """Search photos by date, category, or location."""
    creds = get_photos_creds()
    if not creds:
        return jsonify({'error': 'Not connected', 'photos': []}), 200
    filters = {}
    # Date filter
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    day = request.args.get('day', type=int)
    if year:
        date_filter = {'dates': [{'year': year, 'month': month or 0, 'day': day or 0}]}
        filters['dateFilter'] = date_filter
    # Category filter (e.g. LANDSCAPES, SELFIES, PEOPLE, PETS, FOOD, TRAVEL, etc.)
    category = request.args.get('category')
    if category:
        filters['contentFilter'] = {'includedContentCategories': [category.upper()]}
    body = {'pageSize': 25}
    if filters:
        body['filters'] = filters
    resp = http_requests.post(
        'https://photoslibrary.googleapis.com/v1/mediaItems:search',
        headers={'Authorization': f'Bearer {creds.token}'},
        json=body,
        timeout=10
    )
    if resp.status_code != 200:
        return jsonify({'error': 'API error', 'photos': []}), 200
    data = resp.json()
    photos = []
    for item in data.get('mediaItems', []):
        meta = item.get('mediaMetadata', {})
        photo = {
            'id': item['id'],
            'url': item.get('baseUrl', '') + '=w800-h600',
            'thumbnail': item.get('baseUrl', '') + '=w200-h200-c',
            'filename': item.get('filename', ''),
            'created': meta.get('creationTime', ''),
        }
        if 'location' in meta:
            photo['location'] = {
                'lat': meta['location'].get('latitude'),
                'lng': meta['location'].get('longitude'),
            }
        photos.append(photo)
    return jsonify({'photos': photos})


@app.route('/api/family/photos/albums', methods=['GET'])
def photos_albums():
    """List all albums."""
    creds = get_photos_creds()
    if not creds:
        return jsonify({'error': 'Not connected', 'albums': []}), 200
    resp = http_requests.get(
        'https://photoslibrary.googleapis.com/v1/albums',
        headers={'Authorization': f'Bearer {creds.token}'},
        params={'pageSize': 50},
        timeout=10
    )
    if resp.status_code != 200:
        return jsonify({'error': 'API error', 'albums': []}), 200
    data = resp.json()
    albums = []
    for a in data.get('albums', []):
        albums.append({
            'id': a['id'],
            'title': a.get('title', 'Untitled'),
            'count': a.get('mediaItemsCount', 0),
            'cover_url': a.get('coverPhotoBaseUrl', '') + '=w200-h200-c',
        })
    return jsonify({'albums': albums})


init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
