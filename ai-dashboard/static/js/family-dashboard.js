/* ==================== FAMILY DASHBOARD ==================== */

const FamilyDashboard = {
    REFRESH_INTERVAL: 30000,
    WEATHER_INTERVAL: 900000, // 15 min
    refreshTimer: null,
    weatherTimer: null,
    lastData: null,

    init() {
        this.Clock.init();
        this.Weather.init();
        this.WiFi.init();
        this.G4S.init();
        this.loadAll();
        this.startAutoRefresh();

        // Pause refresh when tab hidden
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) this.stopAutoRefresh();
            else this.startAutoRefresh();
        });
    },

    async loadAll() {
        try {
            const data = await apiRequest('/api/family/dashboard-data');
            this.renderAll(data);
            this.lastData = JSON.stringify(data);
        } catch (e) {
            console.error('Failed to load dashboard data:', e);
        }
    },

    renderAll(data) {
        this.Schedule.render(data.schedule);
        this.Grocery.render(data.grocery);
        this.HouseInfo.render(data.house_info);
        this.Activity.render(data.activities);
    },

    startAutoRefresh() {
        this.stopAutoRefresh();
        this.refreshTimer = setInterval(() => this.refreshAll(), this.REFRESH_INTERVAL);
    },

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    },

    async refreshAll() {
        try {
            const data = await apiRequest('/api/family/dashboard-data');
            const newData = JSON.stringify(data);
            if (newData !== this.lastData) {
                // Determine which widgets changed
                const old = this.lastData ? JSON.parse(this.lastData) : {};
                if (JSON.stringify(data.schedule) !== JSON.stringify(old.schedule)) {
                    this.pulseCard('scheduleWidget');
                    this.Schedule.render(data.schedule);
                }
                if (JSON.stringify(data.grocery) !== JSON.stringify(old.grocery)) {
                    this.pulseCard('groceryWidget');
                    this.Grocery.render(data.grocery);
                }
                if (JSON.stringify(data.house_info) !== JSON.stringify(old.house_info)) {
                    this.pulseCard('houseInfoWidget');
                    this.HouseInfo.render(data.house_info);
                }
                if (JSON.stringify(data.activities) !== JSON.stringify(old.activities)) {
                    this.pulseCard('activityWidget');
                    this.Activity.render(data.activities);
                }
                this.lastData = newData;
            }
        } catch (e) {
            console.error('Refresh failed:', e);
        }
    },

    pulseCard(id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.remove('fd-card--updating');
        void el.offsetWidth; // force reflow
        el.classList.add('fd-card--updating');
        setTimeout(() => el.classList.remove('fd-card--updating'), 600);
    },

    // ==================== CLOCK ====================
    Clock: {
        init() {
            this.update();
            setInterval(() => this.update(), 1000);
        },

        update() {
            const now = new Date();
            const h = now.getHours();
            const m = String(now.getMinutes()).padStart(2, '0');
            const s = String(now.getSeconds()).padStart(2, '0');
            const h12 = h % 12 || 12;
            const ampm = h >= 12 ? 'PM' : 'AM';

            document.getElementById('fdTime').textContent = `${h12}:${m} ${ampm}`;
            document.getElementById('fdSeconds').textContent = s;

            const dateStr = now.toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
                year: 'numeric'
            });
            document.getElementById('fdDate').textContent = dateStr;
        }
    },

    // ==================== WEATHER ====================
    Weather: {
        init() {
            this.fetch();
            FamilyDashboard.weatherTimer = setInterval(() => this.fetch(), FamilyDashboard.WEATHER_INTERVAL);
        },

        async fetch() {
            try {
                // Try cached coordinates first
                let lat = localStorage.getItem('fd_lat');
                let lon = localStorage.getItem('fd_lon');

                if (!lat || !lon) {
                    const pos = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 10000 });
                    });
                    lat = pos.coords.latitude;
                    lon = pos.coords.longitude;
                    localStorage.setItem('fd_lat', lat);
                    localStorage.setItem('fd_lon', lon);
                }

                const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&temperature_unit=celsius`;
                const resp = await fetch(url);
                const data = await resp.json();
                this.render(data.current_weather);
            } catch (e) {
                console.warn('Weather fetch failed:', e);
                document.getElementById('fdWeatherDesc').textContent = 'Unavailable';
            }
        },

        render(weather) {
            if (!weather) return;
            const icon = this.getIcon(weather.weathercode);
            const temp = Math.round(weather.temperature);
            document.querySelector('.fd-weather__icon').textContent = icon;
            document.getElementById('fdTemp').textContent = `${temp}\u00B0C`;
            document.getElementById('fdWeatherDesc').textContent = this.getDesc(weather.weathercode);
        },

        getIcon(code) {
            const icons = {
                0: '\u2600\uFE0F', 1: '\uD83C\uDF24\uFE0F', 2: '\u26C5', 3: '\u2601\uFE0F',
                45: '\uD83C\uDF2B\uFE0F', 48: '\uD83C\uDF2B\uFE0F',
                51: '\uD83C\uDF26\uFE0F', 53: '\uD83C\uDF26\uFE0F', 55: '\uD83C\uDF27\uFE0F',
                61: '\uD83C\uDF27\uFE0F', 63: '\uD83C\uDF27\uFE0F', 65: '\uD83C\uDF27\uFE0F',
                71: '\uD83C\uDF28\uFE0F', 73: '\uD83C\uDF28\uFE0F', 75: '\uD83C\uDF28\uFE0F',
                80: '\uD83C\uDF26\uFE0F', 81: '\uD83C\uDF27\uFE0F', 82: '\u26C8\uFE0F',
                95: '\u26A1', 96: '\u26A1', 99: '\u26A1'
            };
            return icons[code] || '\uD83C\uDF24\uFE0F';
        },

        getDesc(code) {
            const desc = {
                0: 'Clear', 1: 'Mostly Clear', 2: 'Partly Cloudy', 3: 'Overcast',
                45: 'Foggy', 48: 'Fog', 51: 'Light Drizzle', 53: 'Drizzle', 55: 'Heavy Drizzle',
                61: 'Light Rain', 63: 'Rain', 65: 'Heavy Rain',
                71: 'Light Snow', 73: 'Snow', 75: 'Heavy Snow',
                80: 'Light Showers', 81: 'Showers', 82: 'Heavy Showers',
                95: 'Thunderstorm', 96: 'Hail Storm', 99: 'Severe Storm'
            };
            return desc[code] || 'Unknown';
        }
    },

    // ==================== SCHEDULE ====================
    Schedule: {
        data: [],

        render(events) {
            this.data = events || [];
            const body = document.getElementById('scheduleBody');
            const now = new Date();
            // JS getDay: 0=Sun, we need 0=Mon
            const today = (now.getDay() + 6) % 7;
            const currentTime = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');

            const todayEvents = this.data.filter(e => e.day_of_week === today);

            if (todayEvents.length === 0) {
                // Check next day with classes
                const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
                let nextDay = -1;
                for (let i = 1; i <= 7; i++) {
                    const d = (today + i) % 7;
                    if (this.data.some(e => e.day_of_week === d)) { nextDay = d; break; }
                }
                if (nextDay >= 0) {
                    const nextEvents = this.data.filter(e => e.day_of_week === nextDay);
                    body.innerHTML = `
                        <div class="fd-empty" style="flex-direction:column;gap:8px;">
                            <span>No classes today</span>
                            <span style="font-size:0.75rem;color:var(--text-muted)">
                                Next: ${dayNames[nextDay]} (${nextEvents.length} class${nextEvents.length > 1 ? 'es' : ''})
                            </span>
                        </div>`;
                } else {
                    body.innerHTML = '<div class="fd-empty">No classes scheduled</div>';
                }
                return;
            }

            body.innerHTML = '<div class="fd-schedule-timeline">' + todayEvents.map(e => {
                const isCurrent = currentTime >= e.start_time && currentTime <= e.end_time;
                return `
                    <div class="fd-schedule-item ${isCurrent ? 'fd-schedule-item--current' : ''}"
                         style="--item-color: ${e.color}"
                         onclick="FamilyDashboard.Schedule.editItem(${e.id})">
                        <span class="fd-schedule-time">${this.formatTime(e.start_time)}</span>
                        <div class="fd-schedule-info">
                            <div class="fd-schedule-name">${this.escHtml(e.title)}</div>
                            ${e.location ? `<div class="fd-schedule-loc">${this.escHtml(e.location)}</div>` : ''}
                        </div>
                        <span class="fd-schedule-time" style="min-width:auto">${this.formatTime(e.end_time)}</span>
                        <button class="fd-schedule-delete" onclick="event.stopPropagation();FamilyDashboard.Schedule.delete(${e.id})">&times;</button>
                    </div>`;
            }).join('') + '</div>';
        },

        formatTime(t) {
            const [h, m] = t.split(':');
            const hr = parseInt(h);
            const ampm = hr >= 12 ? 'PM' : 'AM';
            return `${hr % 12 || 12}:${m} ${ampm}`;
        },

        escHtml(s) {
            const d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        },

        showModal(id) {
            document.getElementById('scheduleEditId').value = id || '';
            document.getElementById('scheduleModalTitle').textContent = id ? 'Edit Class' : 'Add Class';
            if (id) {
                const e = this.data.find(x => x.id === id);
                if (e) {
                    document.getElementById('scheduleTitle').value = e.title;
                    document.getElementById('scheduleDay').value = e.day_of_week;
                    document.getElementById('scheduleStart').value = e.start_time;
                    document.getElementById('scheduleEnd').value = e.end_time;
                    document.getElementById('scheduleLocation').value = e.location || '';
                    document.getElementById('scheduleColor').value = e.color || '#6366f1';
                }
            } else {
                document.getElementById('scheduleForm').reset();
            }
            showModal('fdScheduleModal');
        },

        editItem(id) {
            this.showModal(id);
        },

        async save(e) {
            e.preventDefault();
            const id = document.getElementById('scheduleEditId').value;
            const data = {
                title: document.getElementById('scheduleTitle').value,
                day_of_week: parseInt(document.getElementById('scheduleDay').value),
                start_time: document.getElementById('scheduleStart').value,
                end_time: document.getElementById('scheduleEnd').value,
                location: document.getElementById('scheduleLocation').value,
                color: document.getElementById('scheduleColor').value
            };

            if (id) {
                await apiRequest(`/api/family/schedule/${id}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) });
            } else {
                await apiRequest('/api/family/schedule', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) });
            }
            closeModal('fdScheduleModal');
            FamilyDashboard.loadAll();
        },

        async delete(id) {
            if (!confirm('Delete this class?')) return;
            await apiRequest(`/api/family/schedule/${id}`, { method: 'DELETE' });
            FamilyDashboard.loadAll();
        }
    },

    // ==================== GROCERY ====================
    Grocery: {
        data: [],

        render(items) {
            this.data = items || [];
            const body = document.getElementById('groceryBody');
            const unchecked = this.data.filter(i => !i.is_checked);
            const checked = this.data.filter(i => i.is_checked);

            document.getElementById('groceryCount').textContent = unchecked.length;
            document.getElementById('groceryFooter').style.display = checked.length > 0 ? '' : 'none';

            if (this.data.length === 0) {
                body.innerHTML = '<div class="fd-empty">No items yet</div>';
                return;
            }

            // Group unchecked by category
            const categories = {};
            unchecked.forEach(i => {
                const cat = i.category || 'general';
                if (!categories[cat]) categories[cat] = [];
                categories[cat].push(i);
            });

            let html = '<div class="fd-grocery-list">';

            for (const [cat, items] of Object.entries(categories)) {
                html += `<div class="fd-grocery-category">${this.escHtml(cat)}</div>`;
                items.forEach(i => { html += this.renderItem(i); });
            }

            if (checked.length > 0) {
                html += `<div class="fd-grocery-category" style="margin-top:8px">Completed (${checked.length})</div>`;
                checked.forEach(i => { html += this.renderItem(i); });
            }

            html += '</div>';
            body.innerHTML = html;
        },

        renderItem(i) {
            return `
                <div class="fd-grocery-item ${i.is_checked ? 'fd-grocery-item--checked' : ''}"
                     onclick="FamilyDashboard.Grocery.toggle(${i.id}, ${!i.is_checked})">
                    <div class="fd-grocery-check"></div>
                    <span class="fd-grocery-name">${this.escHtml(i.name)}</span>
                    ${i.quantity ? `<span class="fd-grocery-qty">${this.escHtml(i.quantity)}</span>` : ''}
                    <button class="fd-grocery-del" onclick="event.stopPropagation();FamilyDashboard.Grocery.delete(${i.id})">&times;</button>
                </div>`;
        },

        escHtml(s) {
            const d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        },

        async toggle(id, checked) {
            // Optimistic UI
            const item = this.data.find(i => i.id === id);
            if (item) item.is_checked = checked;
            this.render(this.data);

            await apiRequest(`/api/family/grocery/${id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ is_checked: checked })
            });
        },

        async quickAdd() {
            const input = document.getElementById('groceryQuickAdd');
            const name = input.value.trim();
            if (!name) return;

            input.value = '';
            await apiRequest('/api/family/grocery', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name })
            });
            FamilyDashboard.loadAll();
        },

        async delete(id) {
            await apiRequest(`/api/family/grocery/${id}`, { method: 'DELETE' });
            FamilyDashboard.loadAll();
        },

        async clearChecked() {
            if (!confirm('Clear all checked items?')) return;
            await apiRequest('/api/family/grocery/checked', { method: 'DELETE' });
            FamilyDashboard.loadAll();
        }
    },

    // ==================== HOUSE INFO ====================
    HouseInfo: {
        data: [],
        revealTimers: {},

        render(entries) {
            this.data = entries || [];
            const body = document.getElementById('houseInfoBody');

            if (this.data.length === 0) {
                body.innerHTML = '<div class="fd-empty">No info added</div>';
                return;
            }

            // Group by category
            const groups = {};
            this.data.forEach(e => {
                const cat = e.category || 'general';
                if (!groups[cat]) groups[cat] = [];
                groups[cat].push(e);
            });

            const sensitiveCategories = ['wifi', 'codes'];
            let html = '<div class="fd-house-list">';

            for (const [cat, items] of Object.entries(groups)) {
                html += `<div class="fd-house-category-label">${this.escHtml(cat)}</div>`;
                items.forEach(e => {
                    const isSensitive = sensitiveCategories.includes(cat);
                    html += `
                        <div class="fd-house-item">
                            <span class="fd-house-icon">${e.icon || '📌'}</span>
                            <span class="fd-house-label">${this.escHtml(e.label)}</span>
                            <span class="fd-house-value ${isSensitive ? 'fd-house-value--hidden' : ''}"
                                  id="houseVal${e.id}"
                                  data-value="${this.escAttr(e.value)}"
                                  ${isSensitive ? `onclick="FamilyDashboard.HouseInfo.reveal(${e.id})"` : ''}>
                                ${isSensitive ? '••••••••' : this.escHtml(e.value)}
                            </span>
                            <button class="fd-house-delete" onclick="FamilyDashboard.HouseInfo.delete(${e.id})">&times;</button>
                        </div>`;
                });
            }

            html += '</div>';
            body.innerHTML = html;
        },

        reveal(id) {
            const el = document.getElementById(`houseVal${id}`);
            if (!el) return;
            const val = el.dataset.value;
            el.textContent = val;
            el.classList.remove('fd-house-value--hidden');

            // Clear previous timer
            if (this.revealTimers[id]) clearTimeout(this.revealTimers[id]);
            this.revealTimers[id] = setTimeout(() => {
                el.textContent = '••••••••';
                el.classList.add('fd-house-value--hidden');
            }, 5000);
        },

        escHtml(s) {
            const d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        },

        escAttr(s) {
            return s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        },

        showModal(id) {
            document.getElementById('houseInfoEditId').value = id || '';
            document.getElementById('houseInfoModalTitle').textContent = id ? 'Edit Info' : 'Add Info';
            if (id) {
                const e = this.data.find(x => x.id === id);
                if (e) {
                    document.getElementById('houseInfoCategory').value = e.category;
                    document.getElementById('houseInfoIcon').value = e.icon || '';
                    document.getElementById('houseInfoLabel').value = e.label;
                    document.getElementById('houseInfoValue').value = e.value;
                }
            } else {
                document.getElementById('houseInfoForm').reset();
            }
            showModal('fdHouseInfoModal');
        },

        async save(e) {
            e.preventDefault();
            const id = document.getElementById('houseInfoEditId').value;
            const data = {
                category: document.getElementById('houseInfoCategory').value,
                icon: document.getElementById('houseInfoIcon').value,
                label: document.getElementById('houseInfoLabel').value,
                value: document.getElementById('houseInfoValue').value
            };

            if (id) {
                await apiRequest(`/api/family/house-info/${id}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) });
            } else {
                await apiRequest('/api/family/house-info', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) });
            }
            closeModal('fdHouseInfoModal');
            FamilyDashboard.loadAll();
        },

        async delete(id) {
            if (!confirm('Delete this entry?')) return;
            await apiRequest(`/api/family/house-info/${id}`, { method: 'DELETE' });
            FamilyDashboard.loadAll();
        }
    },

    // ==================== WIFI ====================
    WiFi: {
        init() {
            this.check();
            setInterval(() => this.check(), 30000);
        },

        async check() {
            let quality = 0;
            let speed = '';
            let status = 'Checking...';

            // Try Network Information API
            const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
            if (conn) {
                const dl = conn.downlink || 0;
                const type = conn.effectiveType || '';
                if (type === '4g' || dl >= 10) { quality = 4; status = 'Excellent'; }
                else if (type === '3g' || dl >= 3) { quality = 3; status = 'Good'; }
                else if (type === '2g' || dl >= 1) { quality = 2; status = 'Fair'; }
                else { quality = 1; status = 'Poor'; }
                speed = dl > 0 ? `${dl} Mbps` : '';
            } else {
                // Fallback: ping latency
                try {
                    const start = performance.now();
                    await fetch('/api/family/ping', { cache: 'no-store' });
                    const latency = Math.round(performance.now() - start);
                    if (latency < 100) { quality = 4; status = 'Excellent'; }
                    else if (latency < 300) { quality = 3; status = 'Good'; }
                    else if (latency < 600) { quality = 2; status = 'Fair'; }
                    else { quality = 1; status = 'Poor'; }
                    speed = `${latency}ms latency`;
                } catch {
                    quality = 0;
                    status = 'Offline';
                    speed = '';
                }
            }

            this.render(quality, status, speed);
        },

        render(quality, status, speed) {
            const bars = document.querySelectorAll('.fd-wifi-bar');
            bars.forEach(bar => {
                const level = parseInt(bar.dataset.bar);
                bar.className = 'fd-wifi-bar';
                if (level <= quality) {
                    if (quality >= 3) bar.classList.add('fd-wifi-bar--active');
                    else if (quality === 2) bar.classList.add('fd-wifi-bar--warning');
                    else bar.classList.add('fd-wifi-bar--poor');
                }
            });

            document.getElementById('wifiStatus').textContent = status;
            document.getElementById('wifiSpeed').textContent = speed;
        }
    },

    // ==================== GO4SCHOOLS ====================
    G4S: {
        connected: false,
        activeTab: 'timetable',
        timetableData: null,
        homeworkData: null,
        gradesData: null,

        async init() {
            try {
                const status = await apiRequest('/api/family/g4s/status');
                this.connected = status.connected;
                if (this.connected) {
                    document.getElementById('g4sSetupPrompt').style.display = 'none';
                    document.getElementById('g4sContent').style.display = '';
                    this.loadAll();
                }
            } catch (e) {
                console.warn('G4S status check failed:', e);
            }
        },

        async loadAll() {
            if (!this.connected) return;
            await Promise.all([
                this.loadTimetable(),
                this.loadHomework(),
                this.loadGrades()
            ]);
        },

        async loadTimetable() {
            try {
                const data = await apiRequest('/api/family/g4s/timetable');
                this.timetableData = data;
                this.renderTimetable(data);
            } catch (e) {
                document.getElementById('g4sTimetable').innerHTML = '<div class="fd-empty">Could not load timetable</div>';
            }
        },

        async loadHomework() {
            try {
                const data = await apiRequest('/api/family/g4s/homework');
                this.homeworkData = data;
                this.renderHomework(data);
            } catch (e) {
                document.getElementById('g4sHomework').innerHTML = '<div class="fd-empty">Could not load homework</div>';
            }
        },

        async loadGrades() {
            try {
                const data = await apiRequest('/api/family/g4s/grades');
                this.gradesData = data;
                this.renderGrades(data);
            } catch (e) {
                document.getElementById('g4sGrades').innerHTML = '<div class="fd-empty">Could not load grades</div>';
            }
        },

        renderTimetable(data) {
            const el = document.getElementById('g4sTimetable');
            const events = data.events || data.Results || data || [];
            if (!Array.isArray(events) || events.length === 0) {
                el.innerHTML = `<div class="fd-g4s-status"><span class="fd-g4s-status-dot"></span> Connected to Go4Schools</div>
                    <div class="fd-empty">No timetable data available</div>`;
                return;
            }
            el.innerHTML = `<div class="fd-g4s-status"><span class="fd-g4s-status-dot"></span> Live from Go4Schools</div>` +
                events.slice(0, 10).map(e => `
                    <div class="fd-g4s-item">
                        <span class="fd-g4s-item__time">${this.escHtml(e.Period || e.start_time || '')}</span>
                        <div class="fd-g4s-item__info">
                            <div class="fd-g4s-item__name">${this.escHtml(e.Subject || e.title || e.Name || 'Class')}</div>
                            <div class="fd-g4s-item__sub">${this.escHtml(e.Room || e.Teacher || e.location || '')}</div>
                        </div>
                    </div>`).join('');
        },

        renderHomework(data) {
            const el = document.getElementById('g4sHomework');
            const items = data.items || data.Results || data || [];
            if (!Array.isArray(items) || items.length === 0) {
                el.innerHTML = `<div class="fd-g4s-status"><span class="fd-g4s-status-dot"></span> Connected to Go4Schools</div>
                    <div class="fd-empty">No homework right now</div>`;
                return;
            }
            const now = new Date();
            el.innerHTML = `<div class="fd-g4s-status"><span class="fd-g4s-status-dot"></span> Live from Go4Schools</div>` +
                items.slice(0, 10).map(h => {
                    const due = h.DueDate || h.due_date;
                    let badgeClass = 'fd-g4s-item__badge--due';
                    let badgeText = 'Due';
                    if (due) {
                        const dueDate = new Date(due);
                        if (dueDate < now) { badgeClass = 'fd-g4s-item__badge--overdue'; badgeText = 'Overdue'; }
                    }
                    if (h.Completed || h.is_completed) { badgeClass = 'fd-g4s-item__badge--done'; badgeText = 'Done'; }
                    return `
                        <div class="fd-g4s-item">
                            <div class="fd-g4s-item__info">
                                <div class="fd-g4s-item__name">${this.escHtml(h.Title || h.Subject || h.title || 'Task')}</div>
                                <div class="fd-g4s-item__sub">${this.escHtml(h.Subject || h.Description || '')}${due ? ' \u2022 Due ' + new Date(due).toLocaleDateString() : ''}</div>
                            </div>
                            <span class="fd-g4s-item__badge ${badgeClass}">${badgeText}</span>
                        </div>`;
                }).join('');
        },

        renderGrades(data) {
            const el = document.getElementById('g4sGrades');
            const marks = data.marks || data.Results || data || [];
            if (!Array.isArray(marks) || marks.length === 0) {
                el.innerHTML = `<div class="fd-g4s-status"><span class="fd-g4s-status-dot"></span> Connected to Go4Schools</div>
                    <div class="fd-empty">No grades available</div>`;
                return;
            }
            el.innerHTML = `<div class="fd-g4s-status"><span class="fd-g4s-status-dot"></span> Live from Go4Schools</div>` +
                marks.slice(0, 10).map(m => `
                    <div class="fd-g4s-item">
                        <div class="fd-g4s-item__info">
                            <div class="fd-g4s-item__name">${this.escHtml(m.Subject || m.Assessment || m.title || 'Subject')}</div>
                            <div class="fd-g4s-item__sub">${this.escHtml(m.Assessment || m.Description || '')}</div>
                        </div>
                        <span class="fd-g4s-item__badge fd-g4s-item__badge--done">${this.escHtml(m.Grade || m.Mark || m.grade || '--')}</span>
                    </div>`).join('');
        },

        switchTab(tab) {
            this.activeTab = tab;
            document.querySelectorAll('.fd-g4s-tab').forEach(t => {
                t.classList.toggle('fd-g4s-tab--active', t.dataset.tab === tab);
            });
            document.getElementById('g4sTimetable').style.display = tab === 'timetable' ? '' : 'none';
            document.getElementById('g4sHomework').style.display = tab === 'homework' ? '' : 'none';
            document.getElementById('g4sGrades').style.display = tab === 'grades' ? '' : 'none';
        },

        showSetup() {
            document.getElementById('g4sForm').reset();
            showModal('fdG4SModal');
        },

        async saveKey(e) {
            e.preventDefault();
            const key = document.getElementById('g4sApiKey').value.trim();
            if (!key) return;
            try {
                const result = await apiRequest('/api/family/g4s/setup', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ api_key: key })
                });
                this.connected = result.connected;
                if (this.connected) {
                    document.getElementById('g4sSetupPrompt').style.display = 'none';
                    document.getElementById('g4sContent').style.display = '';
                    this.loadAll();
                    FamilyDashboard.pulseCard('g4sWidget');
                }
            } catch (err) {
                alert('Failed to save API key');
            }
            closeModal('fdG4SModal');
        },

        escHtml(s) {
            if (!s) return '';
            const d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        }
    },

    // ==================== ACTIVITY ====================
    Activity: {
        data: [],

        render(activities) {
            this.data = activities || [];
            const body = document.getElementById('activityBody');

            if (this.data.length === 0) {
                body.innerHTML = '<div class="fd-empty">No activity yet</div>';
                return;
            }

            const typeIcons = {
                general: '📝', chore: '🧹', event: '📅', reminder: '🔔', note: '💬'
            };

            body.innerHTML = '<div class="fd-activity-list">' + this.data.slice(0, 15).map(a => `
                <div class="fd-activity-item">
                    <span class="fd-activity-icon">${typeIcons[a.activity_type] || '📝'}</span>
                    <div class="fd-activity-content">
                        <span class="fd-activity-member">${this.escHtml(a.member)}</span>
                        <div class="fd-activity-msg">${this.escHtml(a.message)}</div>
                    </div>
                    <span class="fd-activity-time">${formatDate(a.timestamp)}</span>
                </div>
            `).join('') + '</div>';
        },

        escHtml(s) {
            const d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        },

        showModal() {
            document.getElementById('activityForm').reset();
            showModal('fdActivityModal');
        },

        async save(e) {
            e.preventDefault();
            const data = {
                member: document.getElementById('activityMember').value,
                message: document.getElementById('activityMessage').value,
                activity_type: document.getElementById('activityType').value
            };
            await apiRequest('/api/family/activities', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            closeModal('fdActivityModal');
            FamilyDashboard.loadAll();
        }
    }
};

document.addEventListener('DOMContentLoaded', () => FamilyDashboard.init());
