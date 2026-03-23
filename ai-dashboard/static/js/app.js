// ==================== Modal Functions ====================

function showModal(modalId) {
    document.getElementById(modalId).classList.add('show');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('show');
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.show').forEach(modal => {
            modal.classList.remove('show');
        });
    }
});

// ==================== Project Modal ====================

function showAddProjectModal() {
    document.getElementById('modalTitle').textContent = 'Add New Project';
    document.getElementById('projectForm').reset();
    delete document.getElementById('projectModal').dataset.editId;
    showModal('projectModal');
}

function showEditProjectModal() {
    showModal('editProjectModal');
}

// ==================== Task Modal ====================

function showAddTaskModal(projectId) {
    document.getElementById('taskProjectId').value = projectId;
    document.getElementById('taskForm').reset();
    showModal('taskModal');
}

function showAddActivityModal() {
    document.getElementById('addActivityForm').reset();
    showModal('addActivityModal');
}

// ==================== Utility Functions ====================

function getStatusLabel(status) {
    const labels = {
        'planning': '📝 Planning',
        'in_progress': '🚀 In Progress',
        'review': '👀 Review',
        'complete': '✅ Complete',
        'on_hold': '⏸️ On Hold'
    };
    return labels[status] || status;
}

function getActivityIcon(type) {
    const icons = {
        'update': '📌',
        'task_complete': '✅',
        'blocker': '🚫',
        'note': '💬',
        'status_change': '🔄'
    };
    return icons[type] || '📌';
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;
    
    return date.toLocaleDateString();
}

function formatDateTime(dateStr) {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    return date.toLocaleString();
}

// ==================== API Functions ====================

async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// ==================== Initialize ====================

// Load agents on page load
async function loadAgentsForSelect(selectId) {
    try {
        const agents = await apiRequest('/api/agents');
        const select = document.getElementById(selectId);
        
        if (select) {
            agents.forEach(agent => {
                const option = document.createElement('option');
                option.value = agent.id;
                option.textContent = agent.name;
                select.appendChild(option);
            });
        }
        
        return agents;
    } catch (error) {
        console.error('Failed to load agents:', error);
        return [];
    }
}

// Auto-dismiss alerts after 3 seconds
document.addEventListener('DOMContentLoaded', function() {
    // Add fade-out animation to alerts
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s';
            setTimeout(() => alert.remove(), 500);
        });
    }, 3000);
});

// Handle form submissions with Enter key
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        if (e.target.classList.contains('no-submit')) {
            e.preventDefault();
        }
    });
});

// Add confirmation for delete actions
function confirmDelete(message = 'Are you sure?') {
    return confirm(message);
}

// Export functions for use in templates
window.showModal = showModal;
window.closeModal = closeModal;
window.showAddProjectModal = showAddProjectModal;
window.showEditProjectModal = showEditProjectModal;
window.showAddTaskModal = showAddTaskModal;
window.showAddActivityModal = showAddActivityModal;
window.getStatusLabel = getStatusLabel;
window.getActivityIcon = getActivityIcon;
window.formatDate = formatDate;
window.formatDateTime = formatDateTime;
window.confirmDelete = confirmDelete;
window.apiRequest = apiRequest;