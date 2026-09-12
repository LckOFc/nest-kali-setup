"""Update web/app.py with all new UI elements"""
import re

with open('web/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add new tabs
old_tabs = "<div class=\"tab\" onclick=\"showPanel('issues')\">⚠️ Issues</div>"
new_tabs = """<div class="tab" onclick="showPanel('issues')">⚠️ Issues</div>
        <div class="tab" onclick="showPanel('alerts')">🔔 Alerts</div>
        <div class="tab" onclick="showPanel('organizer')">📁 Organizer</div>
        <div class="tab" onclick="showPanel('target')">🎯 Target</div>
        <div class="tab" onclick="showPanel('session')">🔑 Session</div>
        <div class="tab" onclick="showPanel('comparer')">📊 Comparer</div>
        <div class="tab" onclick="showPanel('sequencer')">🧬 Sequencer</div>
        <div class="tab" onclick="showPanel('collaborator')">🌐 Collaborator</div>
        <div class="tab" onclick="showPanel('projects')">💾 Projects</div>
        <div class="tab" onclick="showPanel('extender')">🧩 Extender</div>
        <div class="tab" onclick="showPanel('browser')">🌍 Browser</div>
        <div class="tab" onclick="showPanel('payload')">⚙️ Payload</div>"""

content = content.replace(old_tabs, new_tabs)

# 2. Add new panels before ISSUES
old_issues = '<!-- ISSUES PANEL -->\n        <div id="panel-issues" class="panel">'
new_panels = """<!-- ALERTS PANEL -->
        <div id="panel-alerts" class="panel">
            <div class="btn-row">
                <select id="alert-filter" onchange="loadAlerts()" style="background:#0d1117;color:#eee;border:1px solid #30363d;padding:5px;border-radius:4px;">
                    <option value="">All Severities</option>
                    <option value="Critical">Critical</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                </select>
                <button onclick="loadAlerts()">Refresh</button>
                <button onclick="clearAlerts()">Clear All</button>
            </div>
            <table id="alerts-table" style="margin-top:10px;">
                <tr><th>Time</th><th>Severity</th><th>Type</th><th>Description</th><th>Evidence</th><th>Actions</th></tr>
            </table>
        </div>
        
        <!-- ORGANIZER PANEL -->
        <div id="panel-organizer" class="panel">
            <div class="btn-row">
                <input id="org-search" placeholder="Search..." style="flex:1;padding:6px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#eee;">
                <button onclick="loadOrganizer()">Search</button>
                <button onclick="exportOrganizer()">Export</button>
            </div>
            <table id="organizer-table" style="margin-top:10px;">
                <tr><th>Time</th><th>Method</th><th>Path</th><th>Folder</th><th>Tags</th><th>Notes</th><th>Actions</th></tr>
            </table>
        </div>
        
        <!-- TARGET PANEL -->
        <div id="panel-target" class="panel">
            <div class="proxy-info">
                <h3>Target Scope</h3>
                <p style="font-size:0.85em;color:#8b949e;margin-top:5px;">Add hosts to include in your tests</p>
            </div>
            <div class="btn-row">
                <input id="target-host" placeholder="example.com" style="flex:1;padding:6px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#eee;">
                <button class="success" onclick="addTarget()">Add to Scope</button>
                <button onclick="removeTarget()">Exclude</button>
            </div>
            <div style="margin-top:15px;">
                <h4 style="color:#e94560;margin-bottom:10px;">Included Hosts</h4>
                <div id="target-included" style="background:#161b22;padding:10px;border-radius:6px;min-height:50px;"></div>
            </div>
            <div style="margin-top:15px;">
                <h4 style="color:#e94560;margin-bottom:10px;">Sitemap</h4>
                <div id="target-sitemap" style="background:#161b22;padding:10px;border-radius:6px;min-height:50px;font-family:monospace;font-size:0.85em;"></div>
            </div>
        </div>
        
        <!-- SESSION PANEL -->
        <div id="panel-session" class="panel">
            <div class="btn-row">
                <button class="success" onclick="createSession()">Create Session</button>
                <button onclick="loadSessions()">Refresh</button>
            </div>
            <table id="session-table" style="margin-top:10px;">
                <tr><th>Session ID</th><th>Created</th><th>Cookies</th><th>Actions</th></tr>
            </table>
            <div id="session-detail" style="margin-top:15px;display:none;">
                <h4 style="color:#e94560;">Session Details</h4>
                <textarea id="session-data" style="min-height:150px;"></textarea>
                <div class="btn-row">
                    <button onclick="copySession()">Copy JSON</button>
                </div>
            </div>
        </div>
        
        <!-- COMPARER PANEL -->
        <div id="panel-comparer" class="panel">
            <div class="two-pane">
                <div class="pane">
                    <div class="pane-header">Left Response (JSON)</div>
                    <textarea id="comparer-left" placeholder='{"status_code": 200, "body": "...", "headers": {}}'></textarea>
                </div>
                <div class="pane">
                    <div class="pane-header">Right Response (JSON)</div>
                    <textarea id="comparer-right" placeholder='{"status_code": 200, "body": "...", "headers": {}}'></textarea>
                </div>
            </div>
            <div class="btn-row">
                <button class="primary" onclick="compareResponses()">Compare</button>
                <button onclick="clearComparer()">Clear</button>
            </div>
            <div id="comparer-result" style="margin-top:15px;background:#161b22;padding:15px;border-radius:6px;min-height:100px;"></div>
        </div>
        
        <!-- SEQUENCER PANEL -->
        <div id="panel-sequencer" class="panel">
            <div class="intruder-config">
                <h3>Token Entropy Analysis</h3>
                <label>Paste tokens (one per line):</label>
                <textarea id="sequencer-tokens" style="min-height:100px;" placeholder="eyJhbGciOiJIUzI1NiJ9...&#10;dGhpc0lzQVRlc3RUb2tlbg==&#10;abc123def456"></textarea>
                <label>Name (optional):</label>
                <input id="sequencer-name" placeholder="Session Tokens" style="width:100%;padding:6px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#eee;">
                <div class="btn-row">
                    <button class="primary" onclick="analyzeTokens()">Analyze Entropy</button>
                </div>
            </div>
            <div id="sequencer-result" style="margin-top:15px;background:#161b22;padding:15px;border-radius:6px;"></div>
        </div>
        
        <!-- COLLABORATOR PANEL -->
        <div id="panel-collaborator" class="panel">
            <div class="proxy-info">
                <h3>OAST - Out-of-Band Testing</h3>
                <p style="font-size:0.85em;color:#8b949e;margin-top:5px;">Detect blind SQLi, SSRF, XXE via external callbacks</p>
            </div>
            <div class="btn-row">
                <button class="success" onclick="startCollaborator()">Start Server</button>
                <button onclick="stopCollaborator()">Stop</button>
                <button onclick="generatePayloads()">Generate Payloads</button>
                <button onclick="loadInteractions()">Refresh Interactions</button>
            </div>
            <div id="collab-status" style="margin:10px 0;padding:10px;background:#161b22;border-radius:6px;"></div>
            <div id="collab-payloads" style="margin:10px 0;padding:10px;background:#161b22;border-radius:6px;font-family:monospace;font-size:0.85em;"></div>
            <h4 style="color:#e94560;margin:15px 0 10px;">Interactions</h4>
            <div id="collab-interactions" style="background:#161b22;padding:10px;border-radius:6px;min-height:100px;font-family:monospace;font-size:0.8em;"></div>
        </div>
        
        <!-- PROJECTS PANEL -->
        <div id="panel-projects" class="panel">
            <div class="btn-row">
                <input id="project-name" placeholder="Project Name" style="flex:1;padding:6px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#eee;">
                <button class="success" onclick="createProject()">Create Project</button>
            </div>
            <table id="projects-table" style="margin-top:10px;">
                <tr><th>Name</th><th>Created</th><th>Updated</th><th>Actions</th></tr>
            </table>
        </div>
        
        <!-- EXTENDER PANEL -->
        <div id="panel-extender" class="panel">
            <div class="btn-row">
                <button class="primary" onclick="loadPlugins()">Load Plugins</button>
                <button onclick="loadBAppStore()">BApp Store</button>
            </div>
            <h4 style="color:#e94560;margin:15px 0 10px;">Installed Plugins</h4>
            <table id="plugin-table" style="margin-bottom:20px;">
                <tr><th>Name</th><th>Version</th><th>Author</th><th>Status</th><th>Actions</th></tr>
            </table>
            <h4 style="color:#e94560;margin:15px 0 10px;">BApp Store</h4>
            <table id="store-table">
                <tr><th>Name</th><th>Category</th><th>Rating</th><th>Downloads</th><th>Status</th><th>Actions</th></tr>
            </table>
        </div>
        
        <!-- BROWSER PANEL -->
        <div id="panel-browser" class="panel">
            <div class="proxy-info">
                <h3>Burp Browser</h3>
                <p style="font-size:0.85em;color:#8b949e;margin-top:5px;">Chromium browser with proxy pre-configured</p>
            </div>
            <div class="btn-row">
                <button class="success" onclick="startBrowser()">Start Browser</button>
                <button onclick="stopBrowser()">Stop</button>
                <button onclick="browserStatus()">Status</button>
            </div>
            <div id="browser-status" style="margin:10px 0;padding:10px;background:#161b22;border-radius:6px;">Click Status to check</div>
            <div class="btn-row" style="margin-top:10px;">
                <input id="browser-url" placeholder="https://example.com" style="flex:1;padding:6px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#eee;">
                <button onclick="openInBrowser()">Open in Browser</button>
            </div>
        </div>
        
        <!-- PAYLOAD PROCESSOR PANEL -->
        <div id="panel-payload" class="panel">
            <div class="intruder-config">
                <h3>Payload Processor</h3>
                <label>Input:</label>
                <textarea id="payload-input" style="min-height:80px;" placeholder="Hello World"></textarea>
                <label>Operation:</label>
                <select id="payload-operation" style="width:100%;padding:6px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#eee;">
                    <option value="url_encode">URL Encode</option>
                    <option value="url_decode">URL Decode</option>
                    <option value="base64_encode">Base64 Encode</option>
                    <option value="base64_decode">Base64 Decode</option>
                    <option value="md5">MD5 Hash</option>
                    <option value="sha256">SHA256 Hash</option>
                    <option value="upper">Uppercase</option>
                    <option value="lower">Lowercase</option>
                    <option value="rot13">ROT13</option>
                </select>
                <div class="btn-row">
                    <button class="primary" onclick="processPayload()">Process</button>
                </div>
            </div>
            <div id="payload-result" style="margin-top:15px;background:#161b22;padding:15px;border-radius:6px;font-family:monospace;"></div>
        </div>
        
        <!-- ISSUES PANEL -->
        <div id="panel-issues" class="panel">"""

content = content.replace(old_issues, new_panels)

# 3. Add JavaScript functions before auto-refresh
old_js = "        // Auto-refresh"
new_js = """
        // ALERTS FUNCTIONS
        async function loadAlerts() {
            const severity = document.getElementById('alert-filter').value;
            const res = await fetch('/api/alerts' + (severity ? '?severity=' + severity : ''));
            const data = await res.json();
            const tbody = document.querySelector('#alerts-table');
            tbody.innerHTML = '<tr><th>Time</th><th>Severity</th><th>Type</th><th>Description</th><th>Evidence</th><th>Actions</th></tr>';
            (data.alerts || []).forEach(a => {
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + new Date(a.timestamp * 1000).toLocaleString() + '</td>' +
                    '<td><span class="badge badge-' + a.severity.toLowerCase() + '">' + a.severity + '</span></td>' +
                    '<td>' + a.alert_type + '</td><td>' + a.description + '</td>' +
                    '<td style="font-size:0.9em;">' + String(a.evidence || '').substring(0, 50) + '</td>' +
                    '<td><button onclick="ackAlert(\\'' + a.alert_id + '\\')">Ack</button></td>';
            });
        }
        async function ackAlert(id) {
            await fetch('/api/alerts/acknowledge/' + id, {method: 'POST'});
            loadAlerts();
        }
        async function clearAlerts() {
            await fetch('/api/alerts/clear', {method: 'POST'});
            loadAlerts();
        }
        
        // ORGANIZER FUNCTIONS
        async function loadOrganizer(folder) {
            const res = await fetch('/api/organizer/items' + (folder ? '?folder=' + folder : ''));
            const data = await res.json();
            const tbody = document.querySelector('#organizer-table');
            tbody.innerHTML = '<tr><th>Time</th><th>Method</th><th>Path</th><th>Folder</th><th>Tags</th><th>Notes</th><th>Actions</th></tr>';
            (data.items || []).forEach(i => {
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + new Date(i.timestamp * 1000).toLocaleTimeString() + '</td>' +
                    '<td>' + i.request.method + '</td><td>' + i.request.path + '</td>' +
                    '<td>' + i.folder + '</td><td>' + (i.tags || []).join(',') + '</td>' +
                    '<td>' + String(i.notes || '').substring(0, 30) + '</td>' +
                    '<td><button onclick="starItem(\\'' + i.id + '\\')">' + (i.starred ? '★' : '☆') + '</button></td>';
            });
        }
        async function starItem(id) { loadOrganizer(); }
        async function exportOrganizer() {
            const res = await fetch('/api/organizer/items');
            const data = await res.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'organizer-export.json';
            a.click();
        }
        
        // TARGET FUNCTIONS
        async function addTarget() {
            const host = document.getElementById('target-host').value;
            if (!host) return;
            await fetch('/api/target/add', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({host: host, include: true})});
            loadTarget();
        }
        async function removeTarget() {
            const host = document.getElementById('target-host').value;
            if (!host) return;
            await fetch('/api/target/add', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({host: host, include: false})});
            loadTarget();
        }
        async function loadTarget() {
            const res = await fetch('/api/target/scope');
            const data = await res.json();
            document.getElementById('target-included').textContent = (data.scope.included_hosts || []).join(', ') || 'None';
            document.getElementById('target-sitemap').textContent = JSON.stringify(data.sitemap || {}, null, 2) || 'Empty';
        }
        
        // SESSION FUNCTIONS
        async function createSession() {
            const res = await fetch('/api/session/create', {method: 'POST'});
            const session = await res.json();
            alert('Session created: ' + session.session_id);
            loadSessions();
        }
        async function loadSessions() {
            const res = await fetch('/api/session/list');
            const sessions = await res.json();
            const tbody = document.querySelector('#session-table');
            tbody.innerHTML = '<tr><th>Session ID</th><th>Created</th><th>Cookies</th><th>Actions</th></tr>';
            (sessions.sessions || []).forEach(s => {
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + s.session_id + '</td><td>' + new Date((s.created_at || 0) * 1000).toLocaleString() + '</td>' +
                    '<td>' + Object.keys(s.cookies || {}).length + '</td>' +
                    '<td><button onclick="showSession(\\'' + s.session_id + '\\')">View</button></td>';
            });
        }
        async function showSession(id) {
            const res = await fetch('/api/session/' + id);
            const session = await res.json();
            document.getElementById('session-detail').style.display = 'block';
            document.getElementById('session-data').value = JSON.stringify(session, null, 2);
        }
        function copySession() { navigator.clipboard.writeText(document.getElementById('session-data').value); }
        
        // COMPARER FUNCTIONS
        async function compareResponses() {
            let left, right;
            try {
                left = JSON.parse(document.getElementById('comparer-left').value);
                right = JSON.parse(document.getElementById('comparer-right').value);
            } catch(e) { alert('Invalid JSON'); return; }
            const res = await fetch('/api/comparer/compare', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({left, right})});
            const result = await res.json();
            let html = '<strong>Summary:</strong><br>';
            html += 'Total diffs: ' + result.summary.total_diffs + '<br>';
            html += 'Status diff: ' + result.summary.status_diff + '<br>';
            html += 'Header diffs: ' + result.summary.header_diffs + '<br>';
            html += 'Body length diff: ' + result.summary.length_diff + '<br><br>';
            html += '<strong>Differences:</strong><br>';
            (result.differences || []).forEach(d => {
                html += '<span style="color:#f85149;">' + d.field + ': ' + d.left + ' → ' + d.right + '</span><br>';
            });
            document.getElementById('comparer-result').innerHTML = html;
        }
        function clearComparer() {
            document.getElementById('comparer-left').value = '';
            document.getElementById('comparer-right').value = '';
            document.getElementById('comparer-result').innerHTML = '';
        }
        
        // SEQUENCER FUNCTIONS
        async function analyzeTokens() {
            const tokensText = document.getElementById('sequencer-tokens').value;
            const tokens = tokensText.split('\\n').filter(t => t.trim());
            const name = document.getElementById('sequencer-name').value;
            if (tokens.length === 0) { alert('Enter at least one token'); return; }
            const res = await fetch('/api/sequencer/analyze', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({tokens, name})});
            const result = await res.json();
            let html = '<strong>Results for: ' + (name || 'Untitled') + '</strong><br><br>';
            html += '<strong>Severity:</strong> <span class="badge badge-' + result.severity.toLowerCase() + '">' + result.severity + '</span><br>';
            html += '<strong>Entropy (Shannon avg):</strong> ' + result.entropy.shannon_avg + '<br>';
            html += '<strong>Unique ratio:</strong> ' + result.uniqueness.unique_ratio + '<br>';
            html += '<strong>Token count:</strong> ' + result.count + '<br><br>';
            if (result.predictability.predictable) {
                html += '<strong>Predictability Issues:</strong><br>';
                result.predictability.issues.forEach(i => { html += '<span style="color:#f85149;">• ' + i.detail + '</span><br>'; });
            }
            if (result.patterns && result.patterns.length > 0) {
                html += '<strong>Detected Patterns:</strong><br>';
                result.patterns.forEach(p => { html += '• ' + p.type + ' at index ' + p.index + '<br>'; });
            }
            html += '<br><strong>Recommendation:</strong> ' + result.recommendation;
            document.getElementById('sequencer-result').innerHTML = html;
        }
        
        // COLLABORATOR FUNCTIONS
        async function startCollaborator() {
            const res = await fetch('/api/collaborator/start', {method: 'POST'});
            const info = await res.json();
            document.getElementById('collab-status').innerHTML = '<strong>Running:</strong> Yes<br><strong>Subdomain:</strong> ' + info.subdomain + '<br><strong>Port:</strong> ' + info.port;
            generatePayloads();
        }
        async function stopCollaborator() {
            await fetch('/api/collaborator/stop', {method: 'POST'});
            document.getElementById('collab-status').innerHTML = '<strong>Running:</strong> No';
        }
        async function generatePayloads() {
            const res = await fetch('/api/collaborator/payloads');
            const payloads = await res.json();
            document.getElementById('collab-payloads').innerHTML = '<strong>DNS:</strong> ' + payloads.dns.full_domain + '<br><strong>HTTP:</strong> ' + payloads.http.url + '<br><strong>XXE:</strong> ' + payloads.xxe.entity + '<br><strong>SSRF:</strong> ' + payloads.ssrf.url;
        }
        async function loadInteractions() {
            const res = await fetch('/api/collaborator/interactions');
            const data = await res.json();
            const interactions = data.interactions || [];
            let html = 'Total: ' + interactions.length + ' interactions<br><br>';
            interactions.forEach(i => {
                html += '<span class="badge badge-info">' + i.type + '</span> ' + i.source_ip + ' - ' + new Date(i.timestamp * 1000).toLocaleTimeString() + '<br>';
                html += '<span style="color:#8b949e;font-size:0.9em;">' + String(i.data || '').substring(0, 100) + '</span><br><br>';
            });
            document.getElementById('collab-interactions').innerHTML = html || 'No interactions yet';
        }
        
        // PROJECTS FUNCTIONS
        async function createProject() {
            const name = document.getElementById('project-name').value;
            if (!name) { alert('Enter project name'); return; }
            await fetch('/api/projects/create', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name})});
            loadProjects();
        }
        async function loadProjects() {
            const res = await fetch('/api/projects/list');
            const projects = await res.json();
            const tbody = document.querySelector('#projects-table');
            tbody.innerHTML = '<tr><th>Name</th><th>Created</th><th>Updated</th><th>Actions</th></tr>';
            (projects.projects || []).forEach(p => {
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + p.name + '</td><td>' + p.created_at + '</td><td>' + p.updated_at + '</td><td><button onclick="loadProject(\\'' + p.id + '\\')">Load</button></td>';
            });
        }
        async function loadProject(id) { alert('Project loaded: ' + id); }
        
        // EXTENDER FUNCTIONS
        async function loadPlugins() {
            const res = await fetch('/api/extender/plugins');
            const data = await res.json();
            const tbody = document.querySelector('#plugin-table');
            tbody.innerHTML = '<tr><th>Name</th><th>Version</th><th>Author</th><th>Status</th><th>Actions</th></tr>';
            (data.plugins || []).forEach(p => {
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + p.name + '</td><td>' + p.version + '</td><td>' + p.author + '</td>' +
                    '<td><span class="badge badge-' + (p.enabled ? 'green' : 'red') + '">' + (p.enabled ? 'Enabled' : 'Disabled') + '</span></td>' +
                    '<td><button onclick="togglePlugin(\\'' + p.name + '\\')">Toggle</button></td>';
            });
        }
        async function loadBAppStore() {
            const res = await fetch('/api/extender/store');
            const data = await res.json();
            const tbody = document.querySelector('#store-table');
            tbody.innerHTML = '<tr><th>Name</th><th>Category</th><th>Rating</th><th>Downloads</th><th>Status</th><th>Actions</th></tr>';
            (data.plugins || []).forEach(p => {
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + p.name + '</td><td>' + p.category + '</td><td>' + p.rating + '</td>' +
                    '<td>' + p.downloads + '</td>' +
                    '<td><span class="badge badge-' + (p.installed ? 'green' : 'yellow') + '">' + (p.installed ? 'Installed' : 'Available') + '</span></td>' +
                    '<td><button onclick="installPlugin(\\'' + p.name + '\\')">' + (p.installed ? 'Installed' : 'Install') + '</button></td>';
            });
        }
        async function installPlugin(name) { alert('Plugin "' + name + '" installed! (Demo)'); loadPlugins(); }
        async function togglePlugin(name) { alert('Plugin "' + name + '" toggled! (Demo)'); loadPlugins(); }
        
        // BROWSER FUNCTIONS
        async function browserStatus() {
            const res = await fetch('/api/browser/status');
            const data = await res.json();
            document.getElementById('browser-status').textContent = 'Running: ' + data.running + ' | Chromium: ' + (data.chromium_found ? 'Found' : 'Not Found');
        }
        async function startBrowser(url) {
            await fetch('/api/browser/start', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: url || ''})});
            browserStatus();
        }
        async function stopBrowser() {
            await fetch('/api/browser/stop', {method: 'POST'});
            browserStatus();
        }
        async function openInBrowser() {
            const url = document.getElementById('browser-url').value;
            if (!url) { alert('Enter URL'); return; }
            await fetch('/api/browser/open', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url})});
        }
        
        // PAYLOAD PROCESSOR FUNCTIONS
        async function processPayload() {
            const payload = document.getElementById('payload-input').value;
            const operation = document.getElementById('payload-operation').value;
            const res = await fetch('/api/payload-processor/process', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({payload, operation})});
            const data = await res.json();
            document.getElementById('payload-result').textContent = data.result;
        }
        
        // Auto-refresh"""

content = content.replace(old_js, new_js)

# 4. Update showPanel to load data for new panels
old_showpanel = """        function showPanel(name) {
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById('panel-' + name).classList.add('active');
            event.target.classList.add('active');
            
            if (name === 'logger') loadLogger();
            if (name === 'scanner') loadScanResults();
            if (name === 'issues') loadIssues();
            if (name === 'proxy') refreshStatus();
        }"""

new_showpanel = """        function showPanel(name) {
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById('panel-' + name).classList.add('active');
            event.target.classList.add('active');
            
            if (name === 'logger') loadLogger();
            if (name === 'scanner') loadScanResults();
            if (name === 'issues') loadIssues();
            if (name === 'proxy') refreshStatus();
            if (name === 'alerts') loadAlerts();
            if (name === 'organizer') loadOrganizer();
            if (name === 'target') loadTarget();
            if (name === 'session') loadSessions();
            if (name === 'extender') loadPlugins();
            if (name === 'browser') browserStatus();
        }"""

content = content.replace(old_showpanel, new_showpanel)

with open('web/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Web UI updated with all new tabs, panels, and JavaScript!')
