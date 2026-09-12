"""
CustomBurp - Web UI Completa
Interface web profissional para o CustomBurp
"""

from flask import Flask, render_template_string, jsonify, request, send_file
import json
import time
import threading
import os
from core.engine import CustomBurp, HTTPMessage
from core.repeater import Repeater
from core.decoder import Decoder as DecoderUtils
from core.intruder import Intruder
from core.comparer import Comparer
from core.sequencer import Sequencer
from core.target import Target
from core.session_handler import SessionManager
from core.match_replace import MatchReplace
from core.payload_processor import PayloadProcessor
from core.collaborator import Collaborator
from core.logger import BurpLogger
from core.alerts import Alerts
from core.organizer import Organizer
from core.project import ProjectManager
from core.extender import Extender
from core.browser import BurpBrowser


app = Flask(__name__)
burp: CustomBurp = None
repeater = Repeater()
decoder = DecoderUtils()
intruder = Intruder()
comparer = Comparer()
sequencer = Sequencer()
target = Target()
session_mgr = SessionManager()
match_replace = MatchReplace()
payload_processor = PayloadProcessor()
collaborator = Collaborator()
alerts = Alerts()
organizer = Organizer()
project_mgr = ProjectManager()
extender = Extender()
browser = BurpBrowser()


def init_app(burp_instance: CustomBurp):
    global burp
    burp = burp_instance


MAIN_TEMPLATE = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CustomBurp Suite</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Segoe UI, Tahoma, Geneva, Verdana, sans-serif; background: #0d1117; color: #c9d1d9; height: 100vh; overflow: hidden; }
        .header { background: linear-gradient(90deg, #161b22, #21262d); padding: 8px 16px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #30363d; }
        .header h1 { color: #58a6ff; font-size: 1.2em; }
        .header .status { display: flex; gap: 15px; font-size: 0.8em; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 5px; }
        .status-dot.green { background: #3fb950; }
        .status-dot.red { background: #f85149; }
        .tabs { display: flex; background: #161b22; border-bottom: 1px solid #30363d; overflow-x: auto; }
        .tab { padding: 10px 16px; cursor: pointer; color: #8b949e; border-bottom: 2px solid transparent; font-size: 0.85em; white-space: nowrap; }
        .tab:hover { color: #c9d1d9; background: #21262d; }
        .tab.active { color: #58a6ff; border-bottom-color: #58a6ff; }
        .content { display: flex; height: calc(100vh - 85px); }
        .panel { flex: 1; padding: 12px; overflow: auto; display: none; }
        .panel.active { display: block; }
        .two-pane { display: flex; gap: 10px; height: 100%; }
        .pane { flex: 1; display: flex; flex-direction: column; background: #161b22; border: 1px solid #30363d; border-radius: 6px; overflow: hidden; }
        .pane-header { background: #21262d; padding: 8px 12px; font-weight: 600; font-size: 0.85em; color: #8b949e; border-bottom: 1px solid #30363d; }
        .pane-body { flex: 1; padding: 10px; overflow: auto; font-family: Consolas, monospace; font-size: 0.82em; white-space: pre-wrap; word-break: break-all; }
        textarea { width: 100%; flex: 1; background: #0d1117; color: #c9d1d9; border: 1px solid #30363d; border-radius: 4px; padding: 10px; font-family: Consolas, monospace; font-size: 0.82em; resize: none; }
        button { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 6px 14px; border-radius: 5px; cursor: pointer; font-size: 0.82em; }
        button:hover { background: #30363d; }
        button.primary { background: #1f6feb; border-color: #1f6feb; }
        button.primary:hover { background: #388bfd; }
        button.success { background: #238636; border-color: #238636; }
        button.danger { background: #da3633; border-color: #da3633; }
        .btn-row { display: flex; gap: 8px; margin: 10px 0; flex-wrap: wrap; }
        table { width: 100%; border-collapse: collapse; font-size: 0.8em; }
        th, td { padding: 6px 10px; text-align: left; border-bottom: 1px solid #21262d; }
        th { background: #161b22; color: #8b949e; }
        tr:hover { background: #161b22; }
        .badge { padding: 2px 8px; border-radius: 12px; font-size: 0.72em; font-weight: 600; }
        .badge-critical { background: #da3633; color: white; }
        .badge-high { background: #f85149; color: white; }
        .badge-medium { background: #d29922; color: #0d1117; }
        .badge-low { background: #388bfd; color: white; }
        .badge-info { background: #1f6feb; color: white; }
        .badge-green { background: #238636; color: white; }
        .badge-yellow { background: #d29922; color: #0d1117; }
        .badge-red { background: #da3633; color: white; }
        .proxy-info { background: #161b22; padding: 12px; border-radius: 6px; margin-bottom: 12px; border: 1px solid #30363d; }
        .proxy-info code { background: #21262d; padding: 2px 6px; border-radius: 4px; color: #79c0ff; }
        .intruder-config { background: #161b22; padding: 12px; border-radius: 6px; margin-bottom: 12px; border: 1px solid #30363d; }
        .intruder-config label { display: block; margin: 8px 0 4px; color: #8b949e; font-size: 0.85em; }
        .intruder-config input, .intruder-config select, .intruder-config textarea { width: 100%; padding: 6px 10px; background: #0d1117; border: 1px solid #30363d; border-radius: 4px; color: #c9d1d9; font-size: 0.85em; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 10px; margin-bottom: 15px; }
        .stat-card { background: #161b22; padding: 12px; border-radius: 6px; border: 1px solid #30363d; text-align: center; }
        .stat-card .number { font-size: 1.4em; font-weight: 700; }
        .stat-card .number.red { color: #f85149; }
        .stat-card .number.yellow { color: #d29922; }
        .stat-card .number.green { color: #3fb950; }
        .stat-card .number.blue { color: #58a6ff; }
        .stat-card .label { font-size: 0.72em; color: #8b949e; margin-top: 4px; }
        input, select { background: #0d1117; color: #c9d1d9; border: 1px solid #30363d; padding: 6px 10px; border-radius: 4px; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #0d1117; }
        ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>CustomBurp Suite</h1>
        <div class="status">
            <span><span class="status-dot" id="proxy-dot"></span><span id="proxy-label">Proxy: Off</span></span>
            <span><span class="status-dot green"></span>Web: On</span>
        </div>
    </div>
    
    <div class="tabs">
        <div class="tab active" onclick="showPanel('proxy')">Proxy</div>
        <div class="tab" onclick="showPanel('repeater')">Repeater</div>
        <div class="tab" onclick="showPanel('intruder')">Intruder</div>
        <div class="tab" onclick="showPanel('scanner')">Scanner</div>
        <div class="tab" onclick="showPanel('logger')">Logger</div>
        <div class="tab" onclick="showPanel('decoder')">Decoder</div>
        <div class="tab" onclick="showPanel('issues')">Issues</div>
        <div class="tab" onclick="showPanel('alerts')">Alerts</div>
        <div class="tab" onclick="showPanel('organizer')">Organizer</div>
        <div class="tab" onclick="showPanel('target')">Target</div>
        <div class="tab" onclick="showPanel('session')">Session</div>
        <div class="tab" onclick="showPanel('comparer')">Comparer</div>
        <div class="tab" onclick="showPanel('sequencer')">Sequencer</div>
        <div class="tab" onclick="showPanel('collaborator')">Collab</div>
        <div class="tab" onclick="showPanel('projects')">Projects</div>
        <div class="tab" onclick="showPanel('extender')">Extender</div>
        <div class="tab" onclick="showPanel('browser')">Browser</div>
        <div class="tab" onclick="showPanel('payload')">Payload</div>
    </div>
    
    <div class="content">
        <!-- PROXY -->
        <div id="panel-proxy" class="panel active">
            <div class="proxy-info">
                <strong>Proxy HTTP/HTTPS</strong>
                <p style="margin-top:8px;font-size:0.85em;color:#8b949e;">Configure seu navegador/proxy para usar:</p>
                <p style="margin-top:4px;">Host: <code>127.0.0.1</code> | Porta: <code id="proxy-port-display">8080</code></p>
                <p style="margin-top:8px;font-size:0.8em;color:#8b949e;">Para HTTPS, instale o CA cert:</p>
                <button onclick="exportCA()" style="margin-top:5px;font-size:0.8em;">Baixar CA Certificate</button>
            </div>
            <div class="btn-row">
                <button class="success" id="btn-proxy" onclick="toggleProxy()">Iniciar Proxy</button>
                <button onclick="refreshStatus()">Atualizar</button>
            </div>
            <div class="two-pane" style="margin-top:12px;">
                <div class="pane">
                    <div class="pane-header">Requisicoes Capturadas</div>
                    <div class="pane-body" id="proxy-log">Nenhuma requisicao...</div>
                </div>
                <div class="pane">
                    <div class="pane-header">Estatisticas</div>
                    <div class="pane-body" id="proxy-stats">Carregando...</div>
                </div>
            </div>
        </div>
        
        <!-- REPEATER -->
        <div id="panel-repeater" class="panel">
            <div class="two-pane">
                <div class="pane">
                    <div class="pane-header">Request</div>
                    <div style="display:flex;gap:8px;padding:8px;background:#21262d;">
                        <select id="req-method" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:5px 10px;border-radius:4px;">
                            <option>GET</option><option>POST</option><option>PUT</option><option>DELETE</option>
                        </select>
                        <input id="req-url" style="flex:1;background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:5px 10px;border-radius:4px;" placeholder="http://exemplo.com/path">
                    </div>
                    <div style="padding:5px 10px;background:#21262d;font-size:0.78em;color:#8b949e;border-bottom:1px solid #30363d;">Headers</div>
                    <textarea id="req-headers" placeholder="Authorization: Bearer token"></textarea>
                    <div style="padding:5px 10px;background:#21262d;font-size:0.78em;color:#8b949e;border-bottom:1px solid #30363d;">Body</div>
                    <textarea id="req-body" style="min-height:80px;"></textarea>
                    <div class="btn-row">
                        <button class="primary" onclick="sendRepeater()">Send</button>
                        <button onclick="sendRepeaterGet()">Send GET</button>
                    </div>
                </div>
                <div class="pane">
                    <div class="pane-header">Response <span id="resp-time" style="color:#3fb950;font-size:0.8em;margin-left:10px;"></span></div>
                    <div class="pane-body" id="resp-display">Envie uma requisicao...</div>
                </div>
            </div>
        </div>
        
        <!-- INTRUDER -->
        <div id="panel-intruder" class="panel">
            <div class="intruder-config">
                <h3 style="font-size:1em;margin-bottom:10px;">Configuracao do Intruder</h3>
                <label>Request (marque posicoes com !@):</label>
                <textarea id="intruder-request" style="min-height:80px;"></textarea>
                <label>Payloads (um por linha):</label>
                <textarea id="intruder-payloads" style="min-height:80px;"></textarea>
                <div style="display:flex;gap:12px;margin-top:10px;flex-wrap:wrap;">
                    <label>Modo:
                        <select id="intruder-mode" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:5px;border-radius:4px;">
                            <option value="sniper">Sniper</option>
                            <option value="battering_ram">Battering Ram</option>
                            <option value="pitchfork">Pitchfork</option>
                            <option value="cluster_bomb">Cluster Bomb</option>
                        </select>
                    </label>
                    <label>Threads:
                        <input type="number" id="intruder-threads" value="5" min="1" max="20" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:5px;width:60px;border-radius:4px;">
                    </label>
                </div>
                <div class="btn-row">
                    <button class="danger" onclick="startIntruder()">Start Attack</button>
                    <button onclick="clearIntruder()">Clear</button>
                </div>
            </div>
            <div class="two-pane">
                <div class="pane">
                    <div class="pane-header">Resultados</div>
                    <div class="pane-body" id="intruder-results"><div style="color:#484f58;text-align:center;padding:40px;">Nenhum ataque executado</div></div>
                </div>
                <div class="pane">
                    <div class="pane-header">Análise</div>
                    <div class="pane-body" id="intruder-analysis"><div style="color:#484f58;text-align:center;padding:40px;">Execute um ataque</div></div>
                </div>
            </div>
        </div>
        
        <!-- SCANNER -->
        <div id="panel-scanner" class="panel">
            <div class="stats-grid">
                <div class="stat-card"><div class="number red" id="scan-critical">0</div><div class="label">Critical</div></div>
                <div class="stat-card"><div class="number red" id="scan-high">0</div><div class="label">High</div></div>
                <div class="stat-card"><div class="number yellow" id="scan-medium">0</div><div class="label">Medium</div></div>
                <div class="stat-card"><div class="number blue" id="scan-low">0</div><div class="label">Low</div></div>
            </div>
            <div class="btn-row">
                <button class="primary" onclick="runScan()">Run Scan</button>
                <button onclick="clearIssues()">Clear Issues</button>
            </div>
            <div style="margin-top:12px;">
                <table id="scan-results">
                    <tr><th>Severity</th><th>Type</th><th>Description</th><th>Evidence</th></tr>
                </table>
            </div>
        </div>
        
        <!-- LOGGER -->
        <div id="panel-logger" class="panel">
            <div class="btn-row">
                <input id="logger-search" placeholder="Buscar..." style="flex:1;">
                <button onclick="filterLogger()">Search</button>
                <button onclick="clearLogger()">Clear</button>
                <button onclick="exportLogger()">Export</button>
            </div>
            <div style="margin-top:8px;">
                <table id="logger-table">
                    <tr><th>Time</th><th>Method</th><th>Host</th><th>Path</th><th>Status</th><th>Size</th><th>Actions</th></tr>
                </table>
            </div>
        </div>
        
        <!-- DECODER -->
        <div id="panel-decoder" class="panel">
            <div class="two-pane">
                <div class="pane">
                    <div class="pane-header">Input</div>
                    <textarea id="decoder-input" style="min-height:150px;"></textarea>
                    <div class="btn-row" style="flex-wrap:wrap;">
                        <button onclick="decodeAction('url_decode')">URL Decode</button>
                        <button onclick="decodeAction('url_encode')">URL Encode</button>
                        <button onclick="decodeAction('base64_decode')">B64 Decode</button>
                        <button onclick="decodeAction('base64_encode')">B64 Encode</button>
                        <button onclick="decodeAction('md5')">MD5</button>
                        <button onclick="decodeAction('sha256')">SHA256</button>
                        <button onclick="decodeAction('json_format')">JSON</button>
                        <button onclick="decodeAction('rot13')">ROT13</button>
                    </div>
                </div>
                <div class="pane">
                    <div class="pane-header">Output <button onclick="copyDecoderOutput()" style="margin-left:auto;padding:2px 8px;font-size:0.75em;">Copy</button></div>
                    <div class="pane-body" id="decoder-output">Resultado...</div>
                    <div style="padding:8px;background:#21262d;font-size:0.78em;color:#8b949e;">Encoding: <span id="decoder-detect" style="color:#79c0ff;">-</span></div>
                </div>
            </div>
        </div>
        
        <!-- ISSUES -->
        <div id="panel-issues" class="panel">
            <div class="btn-row">
                <select id="issue-filter" onchange="loadIssues()" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:5px;border-radius:4px;">
                    <option value="">All</option>
                    <option value="Critical">Critical</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                </select>
                <button onclick="loadIssues()">Refresh</button>
            </div>
            <table id="issues-table" style="margin-top:10px;">
                <tr><th>Time</th><th>Severity</th><th>Type</th><th>Description</th><th>Evidence</th></tr>
            </table>
        </div>
        
        <!-- ALERTS -->
        <div id="panel-alerts" class="panel">
            <div class="btn-row">
                <select id="alert-filter" onchange="loadAlerts()" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:5px;border-radius:4px;">
                    <option value="">All</option>
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
        
        <!-- ORGANIZER -->
        <div id="panel-organizer" class="panel">
            <div class="btn-row">
                <input id="org-search" placeholder="Search..." style="flex:1;">
                <button onclick="loadOrganizer()">Search</button>
                <button onclick="exportOrganizer()">Export</button>
            </div>
            <table id="organizer-table" style="margin-top:10px;">
                <tr><th>Time</th><th>Method</th><th>Path</th><th>Folder</th><th>Tags</th><th>Notes</th></tr>
            </table>
        </div>
        
        <!-- TARGET -->
        <div id="panel-target" class="panel">
            <div class="proxy-info">
                <h3>Target Scope</h3>
                <p style="font-size:0.85em;color:#8b949e;margin-top:5px;">Add hosts to include in your tests</p>
            </div>
            <div class="btn-row">
                <input id="target-host" placeholder="example.com" style="flex:1;">
                <button class="success" onclick="addTarget()">Add</button>
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
        
        <!-- SESSION -->
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
                <div class="btn-row"><button onclick="copySession()">Copy JSON</button></div>
            </div>
        </div>
        
        <!-- COMPARER -->
        <div id="panel-comparer" class="panel">
            <div class="two-pane">
                <div class="pane">
                    <div class="pane-header">Left Response (JSON)</div>
                    <textarea id="comparer-left" placeholder="{\\"status_code\\": 200, \\"body\\": \\"...\\", \\"headers\\": {}}"></textarea>
                </div>
                <div class="pane">
                    <div class="pane-header">Right Response (JSON)</div>
                    <textarea id="comparer-right" placeholder="{\\"status_code\\": 200, \\"body\\": \\"...\\", \\"headers\\": {}}"></textarea>
                </div>
            </div>
            <div class="btn-row">
                <button class="primary" onclick="compareResponses()">Compare</button>
                <button onclick="clearComparer()">Clear</button>
            </div>
            <div id="comparer-result" style="margin-top:15px;background:#161b22;padding:15px;border-radius:6px;min-height:100px;"></div>
        </div>
        
        <!-- SEQUENCER -->
        <div id="panel-sequencer" class="panel">
            <div class="intruder-config">
                <h3>Token Entropy Analysis</h3>
                <label>Paste tokens (one per line):</label>
                <textarea id="sequencer-tokens" style="min-height:100px;" placeholder="eyJhbGciOiJIUzI1NiJ9...&#10;dGhpc0lzQVRlc3RUb2tlbg==&#10;abc123def456"></textarea>
                <label>Name (optional):</label>
                <input id="sequencer-name" placeholder="Session Tokens" style="width:100%;padding:6px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#eee;">
                <div class="btn-row"><button class="primary" onclick="analyzeTokens()">Analyze Entropy</button></div>
            </div>
            <div id="sequencer-result" style="margin-top:15px;background:#161b22;padding:15px;border-radius:6px;"></div>
        </div>
        
        <!-- COLLABORATOR -->
        <div id="panel-collaborator" class="panel">
            <div class="proxy-info">
                <h3>OAST - Out-of-Band Testing</h3>
                <p style="font-size:0.85em;color:#8b949e;margin-top:5px;">Detect blind SQLi, SSRF, XXE via external callbacks</p>
            </div>
            <div class="btn-row">
                <button class="success" onclick="startCollaborator()">Start Server</button>
                <button onclick="stopCollaborator()">Stop</button>
                <button onclick="generatePayloads()">Generate Payloads</button>
                <button onclick="loadInteractions()">Refresh</button>
            </div>
            <div id="collab-status" style="margin:10px 0;padding:10px;background:#161b22;border-radius:6px;"></div>
            <div id="collab-payloads" style="margin:10px 0;padding:10px;background:#161b22;border-radius:6px;font-family:monospace;font-size:0.85em;"></div>
            <h4 style="color:#e94560;margin:15px 0 10px;">Interactions</h4>
            <div id="collab-interactions" style="background:#161b22;padding:10px;border-radius:6px;min-height:100px;font-family:monospace;font-size:0.8em;"></div>
        </div>
        
        <!-- PROJECTS -->
        <div id="panel-projects" class="panel">
            <div class="btn-row">
                <input id="project-name" placeholder="Project Name" style="flex:1;">
                <button class="success" onclick="createProject()">Create Project</button>
            </div>
            <table id="projects-table" style="margin-top:10px;">
                <tr><th>Name</th><th>Created</th><th>Updated</th><th>Actions</th></tr>
            </table>
        </div>
        
        <!-- EXTENDER -->
        <div id="panel-extender" class="panel">
            <div class="btn-row">
                <button class="primary" onclick="loadPlugins()">Load Plugins</button>
                <button onclick="loadBAppStore()">BApp Store</button>
            </div>
            <h4 style="color:#e94560;margin:15px 0 10px;">Installed Plugins</h4>
            <table id="plugin-table" style="margin-bottom:20px;">
                <tr><th>Name</th><th>Version</th><th>Author</th><th>Status</th></tr>
            </table>
            <h4 style="color:#e94560;margin:15px 0 10px;">BApp Store</h4>
            <table id="store-table">
                <tr><th>Name</th><th>Category</th><th>Rating</th><th>Downloads</th><th>Status</th></tr>
            </table>
        </div>
        
        <!-- BROWSER -->
        <div id="panel-browser" class="panel">
            <div class="proxy-info">
                <h3>Burp Browser</h3>
                <p style="font-size:0.85em;color:#8b949e;margin-top:5px;">Chromium browser with proxy pre-configured</p>
            </div>
            <div class="btn-row">
                <button class="success" onclick="startBrowser()">Start</button>
                <button onclick="stopBrowser()">Stop</button>
                <button onclick="browserStatus()">Status</button>
            </div>
            <div id="browser-status" style="margin:10px 0;padding:10px;background:#161b22;border-radius:6px;">Click Status to check</div>
            <div class="btn-row" style="margin-top:10px;">
                <input id="browser-url" placeholder="https://example.com" style="flex:1;">
                <button onclick="openInBrowser()">Open</button>
            </div>
        </div>
        
        <!-- PAYLOAD -->
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
                <div class="btn-row"><button class="primary" onclick="processPayload()">Process</button></div>
            </div>
            <div id="payload-result" style="margin-top:15px;background:#161b22;padding:15px;border-radius:6px;font-family:monospace;"></div>
        </div>
    </div>
    
    <script>
        function showPanel(name) {
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
        }
        
        async function toggleProxy() {
            const btn = document.getElementById('btn-proxy');
            const dot = document.getElementById('proxy-dot');
            const label = document.getElementById('proxy-label');
            const res = await fetch('/api/proxy/toggle', {method: 'POST'});
            const status = await res.json();
            if (status.running) {
                btn.textContent = 'Parar Proxy';
                btn.className = 'danger';
                dot.className = 'status-dot green';
                label.textContent = 'Proxy: On';
            } else {
                btn.textContent = 'Iniciar Proxy';
                btn.className = 'success';
                dot.className = 'status-dot red';
                label.textContent = 'Proxy: Off';
            }
        }
        
        async function refreshStatus() {
            const res = await fetch('/api/status');
            const status = await res.json();
            document.getElementById('proxy-stats').innerHTML = 
                '<b>Requests:</b> ' + status.stats.total_requests + '<br>' +
                '<b>Hosts:</b> ' + status.stats.unique_hosts + '<br>' +
                '<b>Issues:</b> ' + status.stats.total_issues;
        }
        
        async function sendRepeater() {
            const method = document.getElementById('req-method').value;
            const url = document.getElementById('req-url').value;
            const headersText = document.getElementById('req-headers').value;
            const body = document.getElementById('req-body').value;
            const headers = {};
            headersText.split('\\n').forEach(line => {
                if (line.includes(':')) {
                    const [k, ...v] = line.split(':');
                    headers[k.trim()] = v.join(':').trim();
                }
            });
            const res = await fetch('/api/repeater/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({method, url, headers, body})
            });
            const result = await res.json();
            const respText = 'HTTP/1.1 ' + result.status_code + ' ' + (result.reason || '') + '\\n';
            Object.entries(result.headers || {}).forEach(([k,v]) => {
                document.getElementById('resp-display').textContent += k + ': ' + v + '\\n';
            });
            document.getElementById('resp-display').textContent += '\\n' + result.body;
            document.getElementById('resp-time').textContent = result.time_ms + 'ms';
        }
        
        function sendRepeaterGet() {
            document.getElementById('req-method').value = 'GET';
            sendRepeater();
        }
        
        async function startIntruder() {
            const requestText = document.getElementById('intruder-request').value;
            const payloadsText = document.getElementById('intruder-payloads').value;
            const mode = document.getElementById('intruder-mode').value;
            const threads = parseInt(document.getElementById('intruder-threads').value);
            if (!requestText || !payloadsText) { alert('Preencha request e payloads!'); return; }
            const payloads = payloadsText.split('\\n').filter(p => p.trim());
            const res = await fetch('/api/intruder/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({request: requestText, payloads, mode, threads})
            });
            const result = await res.json();
            if (result.error) { alert('Error: ' + result.error); return; }
            const results = result.results || [];
            let html = '<table style="width:100%;font-size:0.8em;">';
            html += '<tr><th>#</th><th>Payload</th><th>Status</th><th>Length</th><th>Time</th></tr>';
            results.forEach((r, i) => {
                html += '<tr><td>' + (i+1) + '</td><td>' + r.payload + '</td><td>' + r.status_code + '</td><td>' + r.response_length + '</td><td>' + r.time_ms.toFixed(0) + 'ms</td></tr>';
            });
            html += '</table>';
            document.getElementById('intruder-results').innerHTML = html;
            document.getElementById('intruder-analysis').innerHTML = '<strong>Total:</strong> ' + results.length + ' requests<br><strong>Avg time:</strong> ' + (results.reduce((a,r) => a + r.time_ms, 0) / results.length).toFixed(0) + 'ms';
        }
        
        function clearIntruder() {
            document.getElementById('intruder-request').value = '';
            document.getElementById('intruder-payloads').value = '';
            document.getElementById('intruder-results').innerHTML = '<div style="color:#484f58;text-align:center;padding:40px;">Nenhum ataque executado</div>';
            document.getElementById('intruder-analysis').innerHTML = '<div style="color:#484f58;text-align:center;padding:40px;">Execute um ataque</div>';
        }
        
        async function runScan() {
            const res = await fetch('/api/scan/run', {method: 'POST'});
            const result = await res.json();
            alert('Scan completo! ' + result.issues_found + ' issues encontradas.');
            loadScanResults();
        }
        
        async function loadScanResults() {
            const res = await fetch('/api/issues');
            const issues = await res.json();
            const tbody = document.querySelector('#scan-results');
            tbody.innerHTML = '<tr><th>Severity</th><th>Type</th><th>Description</th><th>Evidence</th></tr>';
            let c=0,h=0,m=0,l=0;
            issues.forEach(i => {
                if (i.severity==='Critical') c++;
                else if (i.severity==='High') h++;
                else if (i.severity==='Medium') m++;
                else l++;
                const row = tbody.insertRow();
                row.innerHTML = '<td><span class="badge badge-' + i.severity.toLowerCase() + '">' + i.severity + '</span></td><td>' + i.issue_type + '</td><td>' + i.description + '</td><td style="font-size:0.9em;">' + i.evidence + '</td>';
            });
            document.getElementById('scan-critical').textContent = c;
            document.getElementById('scan-high').textContent = h;
            document.getElementById('scan-medium').textContent = m;
            document.getElementById('scan-low').textContent = l;
        }
        
        async function loadIssues() {
            const severity = document.getElementById('issue-filter').value;
            const res = await fetch('/api/issues' + (severity ? '?severity=' + severity : ''));
            const issues = await res.json();
            const tbody = document.querySelector('#issues-table');
            tbody.innerHTML = '<tr><th>Time</th><th>Severity</th><th>Type</th><th>Description</th><th>Evidence</th></tr>';
            issues.forEach(i => {
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + new Date(i.timestamp * 1000).toLocaleString() + '</td><td><span class="badge badge-' + i.severity.toLowerCase() + '">' + i.severity + '</span></td><td>' + i.issue_type + '</td><td>' + i.description + '</td><td style="font-size:0.9em;">' + i.evidence + '</td>';
            });
        }
        
        async function clearIssues() {
            await fetch('/api/issues/clear', {method: 'POST'});
            loadIssues();
            loadScanResults();
        }
        
        async function loadLogger() {
            const res = await fetch('/api/requests?limit=200');
            const requests = await res.json();
            const tbody = document.querySelector('#logger-table');
            tbody.innerHTML = '<tr><th>Time</th><th>Method</th><th>Host</th><th>Path</th><th>Status</th><th>Size</th><th>Actions</th></tr>';
            requests.forEach(r => {
                const resp = r.response || {};
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + new Date(r.timestamp * 1000).toLocaleTimeString() + '</td><td>' + r.method + '</td><td>' + r.host + '</td><td style="max-width:150px;overflow:hidden;text-overflow:ellipsis;">' + r.path + '</td><td>' + (resp.status_code || '-') + '</td><td>' + (resp.content_length || 0).toLocaleString() + '</td><td><button onclick="sendToRepeater(\\'' + r.id + '\\')">Repeater</button></td>';
            });
        }
        
        async function sendToRepeater(requestId) {
            const res = await fetch('/api/requests/' + requestId);
            const r = await res.json();
            document.getElementById('req-method').value = r.method;
            document.getElementById('req-url').value = 'http://' + r.host + r.path;
            const headers = Object.entries(r.headers || {}).map(([k,v]) => k + ': ' + v).join('\\n');
            document.getElementById('req-headers').value = headers;
            document.getElementById('req-body').value = r.body || '';
            showPanel('repeater');
            document.querySelector('.tab:nth-child(2)').click();
        }
        
        function exportLogger() {
            fetch('/api/requests?limit=1000').then(r => r.json()).then(data => {
                const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = 'burp-exports-' + new Date().toISOString().slice(0,10) + '.json';
                a.click();
            });
        }
        
        function clearLogger() {
            if (confirm('Limpar todo o historico?')) {
                fetch('/api/requests/clear', {method: 'POST'});
                loadLogger();
            }
        }
        
        function decodeAction(action) {
            const input = document.getElementById('decoder-input').value;
            if (!input) return;
            fetch('/api/decoder/transform', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action, input})
            }).then(r => r.json()).then(result => {
                document.getElementById('decoder-output').textContent = result.output;
                document.getElementById('decoder-detect').textContent = result.encoding || '-';
            });
        }
        
        function copyDecoderOutput() {
            navigator.clipboard.writeText(document.getElementById('decoder-output').textContent);
        }
        
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
            tbody.innerHTML = '<tr><th>Time</th><th>Method</th><th>Path</th><th>Folder</th><th>Tags</th><th>Notes</th></tr>';
            (data.items || []).forEach(i => {
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + new Date(i.timestamp * 1000).toLocaleTimeString() + '</td>' +
                    '<td>' + i.request.method + '</td><td>' + i.request.path + '</td>' +
                    '<td>' + i.folder + '</td><td>' + (i.tags || []).join(',') + '</td>' +
                    '<td>' + String(i.notes || '').substring(0, 30) + '</td>';
            });
        }
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
            tbody.innerHTML = '<tr><th>Session ID</th><th>Created</th><th>Cookies</th></tr>';
            (sessions.sessions || []).forEach(s => {
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + s.session_id + '</td><td>' + new Date((s.created_at || 0) * 1000).toLocaleString() + '</td><td>' + Object.keys(s.cookies || {}).length + '</td>';
            });
        }
        function copySession() {
            navigator.clipboard.writeText(document.getElementById('session-data').value);
        }
        
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
            tbody.innerHTML = '<tr><th>Name</th><th>Created</th><th>Updated</th></tr>';
            (projects.projects || []).forEach(p => {
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + p.name + '</td><td>' + p.created_at + '</td><td>' + p.updated_at + '</td>';
            });
        }
        
        // EXTENDER FUNCTIONS
        async function loadPlugins() {
            const res = await fetch('/api/extender/plugins');
            const data = await res.json();
            const tbody = document.querySelector('#plugin-table');
            tbody.innerHTML = '<tr><th>Name</th><th>Version</th><th>Author</th><th>Status</th></tr>';
            (data.plugins || []).forEach(p => {
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + p.name + '</td><td>' + p.version + '</td><td>' + p.author + '</td>' +
                    '<td><span class="badge badge-' + (p.enabled ? 'green' : 'red') + '">' + (p.enabled ? 'Enabled' : 'Disabled') + '</span></td>';
            });
        }
        async function loadBAppStore() {
            const res = await fetch('/api/extender/store');
            const data = await res.json();
            const tbody = document.querySelector('#store-table');
            tbody.innerHTML = '<tr><th>Name</th><th>Category</th><th>Rating</th><th>Status</th></tr>';
            (data.plugins || []).forEach(p => {
                const row = tbody.insertRow();
                row.innerHTML = '<td>' + p.name + '</td><td>' + p.category + '</td><td>' + p.rating + '</td>' +
                    '<td><span class="badge badge-' + (p.installed ? 'green' : 'yellow') + '">' + (p.installed ? 'Installed' : 'Available') + '</span></td>';
            });
        }
        
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
        
        // PAYLOAD FUNCTIONS
        async function processPayload() {
            const payload = document.getElementById('payload-input').value;
            const operation = document.getElementById('payload-operation').value;
            const res = await fetch('/api/payload-processor/process', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({payload, operation})});
            const data = await res.json();
            document.getElementById('payload-result').textContent = data.result;
        }
        
        async function exportCA() {
            window.open('/api/config/export_ca', '_blank');
        }
        
        // Auto-refresh
        setInterval(() => {
            if (document.getElementById('panel-proxy').classList.contains('active')) {
                refreshStatus();
            }
        }, 5000);
        
        // Init
        refreshStatus();
    </script>
</body>
</html>'''


# ========================================================================
# API ROUTES
# ========================================================================

@app.route('/')
def index():
    return render_template_string(MAIN_TEMPLATE)


@app.route('/api/status')
def get_status():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify(burp.get_status())


@app.route('/api/proxy/toggle', methods=['POST'])
def toggle_proxy():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    if burp.running:
        burp.stop_proxy()
        return jsonify({'running': False})
    else:
        burp.start_proxy()
        return jsonify({'running': True, 'port': burp.proxy.port})


@app.route('/api/requests')
def get_requests():
    if not burp:
        return jsonify([])
    host = request.args.get('host')
    limit = int(request.args.get('limit', 100))
    search = request.args.get('search')
    requests = burp.db.get_requests(host=host, limit=limit, search=search)
    return jsonify(requests)


@app.route('/api/requests/<request_id>')
def get_request(request_id):
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    requests = burp.db.get_requests(limit=1000)
    for r in requests:
        if r['id'] == request_id:
            return jsonify(r)
    return jsonify({'error': 'Request not found'}), 404


@app.route('/api/requests/clear', methods=['POST'])
def clear_requests():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    burp.db.clear_data()
    return jsonify({'status': 'cleared'})


@app.route('/api/issues')
def get_issues():
    if not burp:
        return jsonify([])
    severity = request.args.get('severity')
    issues = burp.db.get_issues(severity=severity)
    return jsonify(issues)


@app.route('/api/issues/clear', methods=['POST'])
def clear_issues():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    import sqlite3
    conn = sqlite3.connect(burp.db.db_path)
    conn.execute("DELETE FROM issues")
    conn.commit()
    conn.close()
    return jsonify({'status': 'cleared'})


@app.route('/api/scan/run', methods=['POST'])
def run_scan():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    hosts = set()
    requests = burp.db.get_requests(limit=1000)
    for r in requests:
        if r.get('host'):
            hosts.add(r['host'])
    all_issues = []
    for host in hosts:
        issues = burp.scanner.scan_host(host)
        all_issues.extend(issues)
    return jsonify({'scanned_hosts': list(hosts), 'issues_found': len(all_issues), 'issues': all_issues})


@app.route('/api/repeater/send', methods=['POST'])
def repeater_send():
    data = request.json
    result = repeater.send(data.get('method', 'GET'), data.get('url', ''), data.get('headers', {}), data.get('body', ''))
    return jsonify(result)


@app.route('/api/intruder/start', methods=['POST'])
def intruder_start():
    data = request.json
    try:
        results = intruder.attack(request_text=data.get('request', ''), payloads=data.get('payloads', []), mode=data.get('mode', 'sniper'), thread_count=data.get('threads', 5), timeout=data.get('timeout', 30))
        return jsonify({'results': results, 'count': len(results)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/intruder/results')
def intruder_results():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'results': burp.intruder.get_results(), 'count': len(burp.intruder.get_results())})


@app.route('/api/decoder/transform', methods=['POST'])
def decoder_transform():
    data = request.json
    result = decoder.transform(data.get('action', ''), data.get('input', ''))
    return jsonify(result)


@app.route('/api/config/export_ca')
def export_ca():
    if not burp or not burp.proxy._ca_cert_path:
        return jsonify({'error': 'CA cert not generated'}), 404
    cert_path = burp.proxy._ca_cert_path
    if os.path.exists(cert_path):
        return send_file(cert_path, as_attachment=True, download_name='CustomBurp-CA.crt')
    return jsonify({'error': 'CA file not found'}), 404


# ========================================================================
# NEW API ROUTES
# ========================================================================

@app.route('/api/alerts')
def get_alerts():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    severity = request.args.get('severity')
    alerts_data = burp.alerts.get_alerts(severity=severity)
    return jsonify({'alerts': alerts_data, 'total': len(alerts_data)})


@app.route('/api/alerts/unread')
def get_unread_alerts():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'unread': burp.alerts.get_unread_count()})


@app.route('/api/alerts/acknowledge/<alert_id>', methods=['POST'])
def acknowledge_alert(alert_id):
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'acknowledged': burp.alerts.acknowledge_alert(alert_id)})


@app.route('/api/alerts/clear', methods=['POST'])
def clear_alerts():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    burp.alerts.clear_all()
    return jsonify({'cleared': True})


@app.route('/api/organizer/items')
def get_organizer_items():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    folder = request.args.get('folder')
    tag = request.args.get('tag')
    items = burp.organizer.list_items(folder=folder, tag=tag)
    return jsonify({'items': items, 'total': len(items)})


@app.route('/api/organizer/add', methods=['POST'])
def add_organizer_item():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json
    item = burp.organizer.add(request=data.get('request', {}), response=data.get('response'), notes=data.get('notes', ''), tags=data.get('tags', []), folder=data.get('folder', 'Geral'))
    return jsonify({'item': item})


@app.route('/api/organizer/stats')
def get_organizer_stats():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify(burp.organizer.get_stats())


@app.route('/api/target/scope')
def get_target_scope():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'scope': burp.target.scope, 'sitemap': burp.target.get_sitemap()})


@app.route('/api/target/add', methods=['POST'])
def target_add():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json
    burp.target.add_scope(data.get('host', ''), data.get('include', True))
    return jsonify({'host': data.get('host'), 'in_scope': True})


@app.route('/api/session/create', methods=['POST'])
def session_create():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify(burp.session_mgr.create_session().to_dict())


@app.route('/api/session/list')
def session_list():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'sessions': burp.session_mgr.list_sessions()})


@app.route('/api/session/<session_id>')
def session_get(session_id):
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    session = burp.session_mgr.get_session(session_id)
    return jsonify(session.to_dict()) if session else jsonify({'error': 'Not found'}), 404


@app.route('/api/sequencer/analyze', methods=['POST'])
def sequencer_analyze():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json
    return jsonify(burp.sequencer.analyze(data.get('tokens', []), data.get('name', '')))


@app.route('/api/comparer/compare', methods=['POST'])
def comparer_compare():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json
    return jsonify(burp.comparer.compare(data.get('left', {}), data.get('right', {})))


@app.route('/api/collaborator/start', methods=['POST'])
def collaborator_start():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify(burp.collaborator.start())


@app.route('/api/collaborator/stop', methods=['POST'])
def collaborator_stop():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    burp.collaborator.stop()
    return jsonify({'stopped': True})


@app.route('/api/collaborator/interactions')
def collaborator_interactions():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'interactions': burp.collaborator.get_interactions()})


@app.route('/api/collaborator/payloads')
def collaborator_payloads():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify(burp.collaborator.generate_payloads())


@app.route('/api/match-replace/rules')
def get_match_replace_rules():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'rules': burp.match_replace.list_rules()})


@app.route('/api/match-replace/add', methods=['POST'])
def add_match_replace_rule():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json
    rule = burp.match_replace.add_rule(pattern=data.get('pattern', ''), replacement=data.get('replacement', ''), target=data.get('target', 'both'), scope=data.get('scope', ''))
    return jsonify({'rule_id': rule.id})


@app.route('/api/projects/list')
def list_projects():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'projects': burp.project_mgr.list_projects()})


@app.route('/api/projects/create', methods=['POST'])
def create_project():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json
    return jsonify(burp.project_mgr.create_project(data.get('name', 'New Project'), data.get('description', '')))


@app.route('/api/projects/current')
def get_current_project():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    project = burp.project_mgr.get_project()
    return jsonify(project) if project else jsonify({'error': 'No project'})


@app.route('/api/extender/plugins')
def list_plugins():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'plugins': burp.extender.list_plugins()})


@app.route('/api/extender/install', methods=['POST'])
def install_plugin():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json
    return jsonify({'installed': burp.extender.install_plugin(data.get('name', ''), data.get('code', ''), data.get('description', ''), data.get('author', ''))})


@app.route('/api/extender/store')
def get_bapp_store():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'plugins': burp.extender.get_bapp_store()})


@app.route('/api/browser/status')
def browser_status():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'running': burp.browser.is_running(), 'chromium_found': bool(burp.browser._chromium_path), 'proxy': burp.browser.get_proxy_config()})


@app.route('/api/browser/start', methods=['POST'])
def browser_start():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json or {}
    return jsonify({'started': burp.browser.start(url=data.get('url', ''))})


@app.route('/api/browser/stop', methods=['POST'])
def browser_stop():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    burp.browser.stop()
    return jsonify({'stopped': True})


@app.route('/api/browser/open', methods=['POST'])
def browser_open():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json
    burp.browser.open_url(data.get('url', ''))
    return jsonify({'opened': True})


@app.route('/api/payload-processor/operations')
def payload_operations():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'operations': burp.payload_processor.list_operations()})


@app.route('/api/payload-processor/process', methods=['POST'])
def payload_process():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json
    return jsonify({'result': burp.payload_processor.process(data.get('payload', ''), data.get('operation', ''))})


def run_web(host='0.0.0.0', port=4000):
    print(f"Iniciando UI em http://{host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    burp_instance = CustomBurp()
    init_app(burp_instance)
    burp_instance.start_proxy()
    run_web()
