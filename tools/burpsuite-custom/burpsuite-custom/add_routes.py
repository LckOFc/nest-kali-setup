"""Add missing API routes to app.py"""
with open('web/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Routes to add
new_routes = '''

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
    count = burp.alerts.get_unread_count()
    return jsonify({'unread': count})

@app.route('/api/alerts/acknowledge/<alert_id>', methods=['POST'])
def acknowledge_alert(alert_id):
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    success = burp.alerts.acknowledge_alert(alert_id)
    return jsonify({'acknowledged': success})

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
    item = burp.organizer.add(
        request=data.get('request', {}),
        response=data.get('response'),
        notes=data.get('notes', ''),
        tags=data.get('tags', []),
        folder=data.get('folder', 'Geral')
    )
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
    session = burp.session_mgr.create_session()
    return jsonify(session.to_dict())

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
    if session:
        return jsonify(session.to_dict())
    return jsonify({'error': 'Session not found'}), 404

@app.route('/api/sequencer/analyze', methods=['POST'])
def sequencer_analyze():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json
    result = burp.sequencer.analyze(data.get('tokens', []), data.get('name', ''))
    return jsonify(result)

@app.route('/api/comparer/compare', methods=['POST'])
def comparer_compare():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json
    result = burp.comparer.compare(data.get('left', {}), data.get('right', {}))
    return jsonify(result)

@app.route('/api/collaborator/start', methods=['POST'])
def collaborator_start():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    info = burp.collaborator.start()
    return jsonify(info)

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
    rule = burp.match_replace.add_rule(
        pattern=data.get('pattern', ''),
        replacement=data.get('replacement', ''),
        target=data.get('target', 'both'),
        scope=data.get('scope', '')
    )
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
    project = burp.project_mgr.create_project(data.get('name', 'New Project'), data.get('description', ''))
    return jsonify(project)

@app.route('/api/projects/current')
def get_current_project():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    project = burp.project_mgr.get_project()
    return jsonify(project) if project else jsonify({'error': 'No project selected'})

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
    success = burp.extender.install_plugin(
        data.get('name', ''),
        data.get('code', ''),
        data.get('description', ''),
        data.get('author', '')
    )
    return jsonify({'installed': success})

@app.route('/api/extender/store')
def get_bapp_store():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({'plugins': burp.extender.get_bapp_store()})

@app.route('/api/browser/status')
def browser_status():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    return jsonify({
        'running': burp.browser.is_running(),
        'chromium_found': bool(burp.browser._chromium_path),
        'proxy': burp.browser.get_proxy_config()
    })

@app.route('/api/browser/start', methods=['POST'])
def browser_start():
    if not burp:
        return jsonify({'error': 'Burp nao inicializado'})
    data = request.json or {}
    url = data.get('url', '')
    success = burp.browser.start(url=url)
    return jsonify({'started': success})

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
    result = burp.payload_processor.process(data.get('payload', ''), data.get('operation', ''))
    return jsonify({'result': result})
'''

# Insert before run_web function
if 'def run_web(host=' in content:
    content = content.replace('def run_web(host=', new_routes + '\n\ndef run_web(host=')
    with open('web/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Routes added successfully!')
else:
    print('Could not find insertion point')
