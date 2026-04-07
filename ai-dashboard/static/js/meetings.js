// ==================== MEETINGS DASHBOARD & DETAIL ====================

let allMeetings = [];
let currentFilter = 'all';
let meetingId = null; // Set on detail page

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    const detailPage = document.querySelector('.meeting-detail-page');
    if (detailPage) {
        meetingId = parseInt(detailPage.dataset.meetingId);
        initDetailPage();
    } else {
        initDashboard();
    }
});

// ==================== DASHBOARD ====================

function initDashboard() {
    loadMeetings();
    loadServicesStatus();
    setupFilters();
    setupSearch();
}

async function loadMeetings() {
    try {
        const resp = await fetch('/api/meetings');
        allMeetings = await resp.json();
        renderMeetings();
        updateStats();
    } catch (err) {
        console.error('Failed to load meetings:', err);
        document.getElementById('meetingsGrid').innerHTML =
            '<div class="empty-state"><div class="empty-state-icon">!</div><div class="empty-state-text">Failed to load meetings</div></div>';
    }
}

function renderMeetings() {
    const grid = document.getElementById('meetingsGrid');
    const search = (document.getElementById('meetingSearch')?.value || '').toLowerCase();

    let filtered = allMeetings;

    // Apply filter
    if (currentFilter === 'school') filtered = filtered.filter(m => m.meeting_type === 'school');
    else if (currentFilter === 'work') filtered = filtered.filter(m => m.meeting_type === 'work');
    else if (currentFilter === 'live') filtered = filtered.filter(m => m.status === 'live');

    // Apply search
    if (search) {
        filtered = filtered.filter(m => m.title.toLowerCase().includes(search));
    }

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🎓</div>
                <div class="empty-state-text">No meetings found</div>
            </div>`;
        return;
    }

    grid.innerHTML = filtered.map(m => {
        const date = m.started_at ? new Date(m.started_at).toLocaleDateString('en-GB', {
            day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
        }) : '';
        const duration = m.duration_minutes ? `${m.duration_minutes} min` : 'In progress';
        const isLive = m.status === 'live';

        return `
            <div class="meeting-card ${isLive ? 'live' : ''}" onclick="window.location.href='/meetings/${m.id}'">
                <div class="meeting-card-title">${escapeHtml(m.title)}</div>
                <div class="meeting-card-meta">
                    <span class="badge badge-${m.meeting_type}">${m.meeting_type}</span>
                    <span class="badge badge-${m.status}">${m.status}</span>
                    <span>${date}</span>
                </div>
                <div class="meeting-card-stats">
                    <span>&#x1f4dd; ${m.transcript_count} segments</span>
                    <span>&#x1f4f8; ${m.screenshot_count} screenshots</span>
                    <span>&#x23f1; ${duration}</span>
                    ${m.has_notes ? '<span>&#x2705; Notes</span>' : ''}
                </div>
            </div>`;
    }).join('');
}

function updateStats() {
    document.getElementById('totalMeetings').textContent = allMeetings.length;
    document.getElementById('liveMeetings').textContent = allMeetings.filter(m => m.status === 'live').length;
    document.getElementById('schoolMeetings').textContent = allMeetings.filter(m => m.meeting_type === 'school').length;
    document.getElementById('workMeetings').textContent = allMeetings.filter(m => m.meeting_type === 'work').length;
}

function setupFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderMeetings();
        });
    });
}

function setupSearch() {
    const input = document.getElementById('meetingSearch');
    if (input) {
        input.addEventListener('input', () => renderMeetings());
    }
}

function showNewMeetingModal() {
    document.getElementById('newMeetingModal').classList.add('active');
    document.getElementById('newMeetingModal').style.display = 'flex';
}

function closeModal(id) {
    const modal = document.getElementById(id);
    modal.classList.remove('active');
    modal.style.display = 'none';
}

async function createMeeting(e) {
    e.preventDefault();
    const title = document.getElementById('meetingTitle').value;
    const type = document.getElementById('meetingType').value;

    try {
        const resp = await fetch('/api/meetings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, meeting_type: type })
        });
        const meeting = await resp.json();
        closeModal('newMeetingModal');
        window.location.href = `/meetings/${meeting.id}`;
    } catch (err) {
        alert('Failed to create meeting');
    }
}

async function loadServicesStatus() {
    try {
        const resp = await fetch('/api/settings/services-status');
        const data = await resp.json();
        const el = document.getElementById('servicesStatus');
        el.innerHTML = `
            <div class="service-indicator">
                <span class="service-dot ${data.whisper ? 'ok' : 'err'}"></span>
                Whisper (Transcription): ${data.whisper ? 'Ready' : 'Not loaded'}
            </div>
            <div class="service-indicator">
                <span class="service-dot ${data.ollama ? 'ok' : 'err'}"></span>
                Ollama (AI Notes): ${data.ollama ? 'Running' : 'Not running'}
            </div>`;
    } catch {
        // Silently fail
    }
}

// Global chat
function toggleGlobalChat() {
    const body = document.getElementById('globalChatBody');
    const toggle = document.getElementById('chatToggle');
    const isOpen = body.style.display !== 'none';
    body.style.display = isOpen ? 'none' : 'block';
    toggle.classList.toggle('open', !isOpen);
}

async function sendGlobalChat() {
    const input = document.getElementById('globalChatInput');
    const question = input.value.trim();
    if (!question) return;

    const messages = document.getElementById('globalChatMessages');
    messages.innerHTML += `<div class="chat-bubble question">${escapeHtml(question)}</div>`;
    input.value = '';
    messages.innerHTML += `<div class="chat-bubble answer" id="globalThinking">Thinking...</div>`;
    messages.scrollTop = messages.scrollHeight;

    try {
        const resp = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        const data = await resp.json();
        document.getElementById('globalThinking').textContent = data.answer;
    } catch {
        document.getElementById('globalThinking').textContent = 'Failed to get answer.';
    }
    messages.scrollTop = messages.scrollHeight;
}


// ==================== DETAIL PAGE ====================

async function initDetailPage() {
    loadMeetingData();
    loadChatHistory();
    setupTabs();
}

async function loadMeetingData() {
    try {
        const resp = await fetch(`/api/meetings/${meetingId}`);
        const data = await resp.json();
        renderTranscript(data.transcripts || []);
        renderScreenshots(data.screenshots || []);
        renderNotes(data.notes);
        document.getElementById('meetingStatus').textContent = data.status;
        document.getElementById('meetingStatus').className = `badge badge-${data.status}`;
    } catch (err) {
        console.error('Failed to load meeting:', err);
    }
}

function renderTranscript(segments) {
    const viewer = document.getElementById('transcriptViewer');
    const count = document.getElementById('transcriptCount');
    count.textContent = `${segments.length} segments`;

    if (segments.length === 0) {
        viewer.innerHTML = '<div class="empty-state"><div class="empty-state-text">No transcript yet</div></div>';
        return;
    }

    viewer.innerHTML = segments.map(s => `
        <div class="transcript-segment">
            <span class="transcript-time">${formatTime(s.timestamp_sec)}</span>
            <span class="transcript-text">${escapeHtml(s.text)}</span>
        </div>`).join('');

    // Transcript search
    const searchInput = document.getElementById('transcriptSearch');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const q = searchInput.value.toLowerCase();
            document.querySelectorAll('.transcript-segment').forEach(el => {
                const text = el.querySelector('.transcript-text').textContent.toLowerCase();
                el.classList.toggle('highlight', q && text.includes(q));
            });
        });
    }
}

function renderScreenshots(screenshots) {
    const grid = document.getElementById('screenshotsGrid');
    if (screenshots.length === 0) {
        grid.innerHTML = '<div class="empty-state"><div class="empty-state-text">No screenshots yet</div></div>';
        return;
    }

    grid.innerHTML = screenshots.map(s => `
        <div class="screenshot-card" onclick="openLightbox('/static/${s.file_path}')">
            <img src="/static/${s.file_path}" alt="Screenshot at ${formatTime(s.timestamp_sec)}" loading="lazy">
            <div class="screenshot-time">${formatTime(s.timestamp_sec)}</div>
        </div>`).join('');
}

function renderNotes(notes) {
    const container = document.getElementById('notesContainer');

    if (!notes) {
        const statusEl = document.getElementById('meetingStatus');
        const status = statusEl ? statusEl.textContent : '';
        if (status === 'processing') {
            container.innerHTML = `
                <div class="processing-state">
                    <div class="processing-spinner"></div>
                    <p>Generating notes...</p>
                </div>`;
        } else {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-text">No notes generated yet</div></div>';
        }
        return;
    }

    let html = '';

    if (notes.summary) {
        html += `
            <div class="notes-section">
                <h3>Summary</h3>
                <p>${escapeHtml(notes.summary)}</p>
            </div>`;
    }

    if (notes.topics && notes.topics.length) {
        html += `
            <div class="notes-section">
                <h3>Topics Discussed</h3>
                <ul class="notes-list">${notes.topics.map(t =>
                    `<li>${escapeHtml(typeof t === 'string' ? t : t.topic || JSON.stringify(t))}</li>`
                ).join('')}</ul>
            </div>`;
    }

    if (notes.action_items && notes.action_items.length) {
        html += `
            <div class="notes-section">
                <h3>Action Items</h3>
                <ul class="notes-list action-items">${notes.action_items.map(a => {
                    const text = typeof a === 'string' ? a : `${a.task || a}${a.owner ? ' — ' + a.owner : ''}`;
                    return `<li>${escapeHtml(text)}</li>`;
                }).join('')}</ul>
            </div>`;
    }

    if (notes.upcoming_tasks && notes.upcoming_tasks.length) {
        html += `
            <div class="notes-section">
                <h3>Upcoming Tasks & Deadlines</h3>
                <ul class="notes-list upcoming">${notes.upcoming_tasks.map(t => {
                    const text = typeof t === 'string' ? t : `${t.task || t}${t.date ? ' — ' + t.date : ''}`;
                    return `<li>${escapeHtml(text)}</li>`;
                }).join('')}</ul>
            </div>`;
    }

    if (notes.key_decisions && notes.key_decisions.length) {
        html += `
            <div class="notes-section">
                <h3>Key Decisions</h3>
                <ul class="notes-list decisions">${notes.key_decisions.map(d =>
                    `<li>${escapeHtml(typeof d === 'string' ? d : JSON.stringify(d))}</li>`
                ).join('')}</ul>
            </div>`;
    }

    container.innerHTML = html || '<div class="empty-state"><div class="empty-state-text">Notes are empty</div></div>';
}

function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(tc => tc.style.display = 'none');
            document.getElementById(`${btn.dataset.tab}Tab`).style.display = 'block';
        });
    });
}

// Chat
async function loadChatHistory() {
    try {
        const resp = await fetch(`/api/meetings/${meetingId}/chat/history`);
        const messages = await resp.json();
        const container = document.getElementById('chatMessages');
        messages.forEach(m => {
            container.innerHTML += `<div class="chat-bubble question">${escapeHtml(m.question)}</div>`;
            container.innerHTML += `<div class="chat-bubble answer">${escapeHtml(m.answer)}</div>`;
        });
    } catch { /* ignore */ }
}

async function sendChat() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();
    if (!question) return;

    const messages = document.getElementById('chatMessages');
    messages.innerHTML += `<div class="chat-bubble question">${escapeHtml(question)}</div>`;
    input.value = '';

    const thinkingId = 'thinking_' + Date.now();
    messages.innerHTML += `<div class="chat-bubble answer" id="${thinkingId}">Thinking...</div>`;
    messages.scrollTop = messages.scrollHeight;

    try {
        const resp = await fetch(`/api/meetings/${meetingId}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        const data = await resp.json();
        document.getElementById(thinkingId).textContent = data.answer;
    } catch {
        document.getElementById(thinkingId).textContent = 'Failed to get answer.';
    }
    messages.scrollTop = messages.scrollHeight;
}

// Meeting actions
async function regenerateNotes() {
    if (!confirm('Regenerate notes? This will overwrite existing notes.')) return;
    try {
        const resp = await fetch(`/api/meetings/${meetingId}/regenerate-notes`, { method: 'POST' });
        const data = await resp.json();
        if (data.notes) renderNotes(data.notes);
        else alert(data.error || 'Failed');
    } catch { alert('Failed to regenerate notes'); }
}

function exportNotes() {
    fetch(`/api/meetings/${meetingId}`)
        .then(r => r.json())
        .then(data => {
            if (!data.notes) { alert('No notes to export'); return; }
            const n = data.notes;
            let text = `# ${data.title}\n`;
            text += `Date: ${new Date(data.started_at).toLocaleString()}\n`;
            text += `Type: ${data.meeting_type} | Duration: ${data.duration_minutes || '?'} min\n\n`;
            text += `## Summary\n${n.summary}\n\n`;
            if (n.topics.length) text += `## Topics\n${n.topics.map(t => `- ${typeof t === 'string' ? t : t.topic || JSON.stringify(t)}`).join('\n')}\n\n`;
            if (n.action_items.length) text += `## Action Items\n${n.action_items.map(a => `- ${typeof a === 'string' ? a : `${a.task}${a.owner ? ' (' + a.owner + ')' : ''}`}`).join('\n')}\n\n`;
            if (n.upcoming_tasks.length) text += `## Upcoming Tasks\n${n.upcoming_tasks.map(t => `- ${typeof t === 'string' ? t : `${t.task}${t.date ? ' — ' + t.date : ''}`}`).join('\n')}\n\n`;
            if (n.key_decisions.length) text += `## Key Decisions\n${n.key_decisions.map(d => `- ${typeof d === 'string' ? d : JSON.stringify(d)}`).join('\n')}\n`;

            const blob = new Blob([text], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${data.title.replace(/[^a-z0-9]/gi, '_')}_notes.md`;
            a.click();
            URL.revokeObjectURL(url);
        });
}

async function deleteMeeting() {
    if (!confirm('Delete this meeting and all its data? This cannot be undone.')) return;
    try {
        await fetch(`/api/meetings/${meetingId}`, { method: 'DELETE' });
        window.location.href = '/meetings';
    } catch { alert('Failed to delete meeting'); }
}

// Lightbox
function openLightbox(src) {
    const lb = document.getElementById('lightbox');
    document.getElementById('lightboxImg').src = src;
    lb.classList.add('active');
}

function closeLightbox() {
    document.getElementById('lightbox').classList.remove('active');
}

// ==================== UTILITIES ====================

function formatTime(seconds) {
    if (!seconds && seconds !== 0) return '00:00';
    const s = Math.round(seconds);
    const m = Math.floor(s / 60);
    const sec = s % 60;
    const h = Math.floor(m / 60);
    const min = m % 60;
    if (h > 0) return `${h}:${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
    return `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
