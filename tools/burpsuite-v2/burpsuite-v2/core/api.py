"""
CustomBurp v2 - REST API
All endpoints for the web UI
"""

import json
import time
import logging
import hashlib
from typing import Dict, List, Optional
from aiohttp import web
from aiohttp.web_app import Application
from aiohttp.web_exceptions import HTTPNotFound, HTTPBadRequest
import asyncio

logger = logging.getLogger('custom_burp.api')


class BurpAPI:
    """REST API for CustomBurp v2"""
    
    def __init__(self, burp_instance):
        self.burp = burp_instance
        self._app = None
        self._routes = []
    
    def get_app(self) -> Application:
        """Get aiohttp application"""
        if self._app is None:
            self._app = web.Application()
            self._setup_routes()
        return self._app
    
    def _setup_routes(self):
        """Setup API routes"""
        routes = [
            # Status
            ('GET', '/api/status', self.get_status),
            ('GET', '/api/stats', self.get_stats),
            
            # Proxy
            ('POST', '/api/proxy/toggle', self.toggle_proxy),
            ('GET', '/api/proxy/status', self.get_proxy_status),
            ('GET', '/api/proxy/ca-cert', self.get_ca_cert),
            ('GET', '/api/proxy/requests/pending', self.get_pending_requests),
            
            # Requests / Logger
            ('GET', '/api/requests', self.get_requests),
            ('GET', '/api/requests/{id}', self.get_request),
            ('DELETE', '/api/requests/{id}', self.delete_request),
            ('POST', '/api/requests/clear', self.clear_requests),
            ('GET', '/api/requests/export', self.export_requests),
            ('GET', '/api/hosts', self.get_hosts),
            ('GET', '/api/methods', self.get_methods),
            ('GET', '/api/status-codes', self.get_status_codes),
            
            # Repeater
            ('POST', '/api/repeater/send', self.repeater_send),
            ('GET', '/api/repeater/history', self.repeater_history),
            
            # Intruder
            ('POST', '/api/intruder/start', self.intruder_start),
            ('GET', '/api/intruder/results/{attack_id}', self.intruder_results),
            ('GET', '/api/intruder/status', self.intruder_status),
            ('POST', '/api/intruder/clear', self.intruder_clear),
            
            # Scanner
            ('POST', '/api/scan/run', self.scan_run),
            ('GET', '/api/scan/status', self.scan_status),
            ('GET', '/api/scan/results/{scan_id}', self.scan_results),
            ('GET', '/api/scan/all', self.scan_all_results),
            
            # Issues
            ('GET', '/api/issues', self.get_issues),
            ('DELETE', '/api/issues/clear', self.clear_issues),
            
            # Decoder
            ('POST', '/api/decoder/transform', self.decoder_transform),
            
            # Target / Scope
            ('POST', '/api/target/add', self.target_add),
            ('DELETE', '/api/target/remove', self.target_remove),
            ('GET', '/api/target/scope', self.target_scope),
            ('GET', '/api/target/sitemap', self.target_sitemap),
            ('POST', '/api/target/clear', self.target_clear),
            
            # Session
            ('POST', '/api/session/create', self.session_create),
            ('GET', '/api/session/list', self.session_list),
            ('GET', '/api/session/active', self.session_active),
            ('POST', '/api/session/set/{session_id}', self.session_set),
            ('DELETE', '/api/session/delete/{session_id}', self.session_delete),
            ('POST', '/api/session/cookie/add', self.session_add_cookie),
            ('POST', '/api/session/token/add', self.session_add_token),
            ('GET', '/api/session/headers', self.session_get_headers),
            
            # Organizer
            ('GET', '/api/organizer/items', self.organizer_items),
            ('POST', '/api/organizer/tag', self.organizer_add_tag),
            ('DELETE', '/api/organizer/tag', self.organizer_remove_tag),
            ('POST', '/api/organizer/folder', self.organizer_set_folder),
            ('POST', '/api/organizer/notes', self.organizer_set_notes),
            ('GET', '/api/organizer/tags', self.organizer_tags),
            ('GET', '/api/organizer/folders', self.organizer_folders),
            
            # Comparer
            ('POST', '/api/comparer/compare', self.comparer_compare),
            
            # Sequencer
            ('POST', '/api/sequencer/analyze', self.sequencer_analyze),
            
            # Collaborator
            ('POST', '/api/collaborator/start', self.collab_start),
            ('POST', '/api/collaborator/stop', self.collab_stop),
            ('GET', '/api/collaborator/status', self.collab_status),
            ('GET', '/api/collaborator/payloads', self.collab_payloads),
            ('GET', '/api/collaborator/interactions', self.collab_interactions),
            ('POST', '/api/collaborator/clear', self.collab_clear),
            
            # Alerts
            ('GET', '/api/alerts', self.get_alerts),
            ('POST', '/api/alerts/acknowledge/{alert_id}', self.acknowledge_alert),
            ('DELETE', '/api/alerts/clear', self.clear_alerts),
            ('GET', '/api/alerts/summary', self.alerts_summary),
            
            # Projects
            ('POST', '/api/projects/create', self.project_create),
            ('GET', '/api/projects/list', self.project_list),
            ('GET', '/api/projects/{id}', self.project_get),
            ('DELETE', '/api/projects/{id}', self.project_delete),
        ]
        
        for method, path, handler in routes:
            self._app.router.add_route(method, path, handler)
    
    # =========================================================================
    # STATUS
    # =========================================================================
    
    async def get_status(self, request: web.Request) -> web.Response:
        stats = self.burp.db.get_stats()
        proxy_stats = self.burp.proxy.get_stats() if self.burp.proxy else {}
        
        return web.json_response({
            'version': '2.0.0',
            'name': 'CustomBurp Suite',
            'stats': stats,
            'proxy': proxy_stats,
            'scanner': self.burp.scanner.get_scan_status() if self.burp.scanner else {},
            'intruder': {
                'is_running': self.burp.intruder.is_running() if self.burp.intruder else False,
            },
            'timestamp': time.time(),
        })
    
    async def get_stats(self, request: web.Request) -> web.Response:
        return web.json_response(self.burp.db.get_stats())
    
    # =========================================================================
    # PROXY
    # =========================================================================
    
    async def toggle_proxy(self, request: web.Request) -> web.Response:
        if self.burp.proxy.running:
            await self.burp.proxy.stop()
            return web.json_response({'running': False, 'message': 'Proxy stopped'})
        else:
            loop = asyncio.get_event_loop()
            loop.create_task(self.burp.proxy.start())
            return web.json_response({'running': True, 'message': 'Proxy started'})
    
    async def get_proxy_status(self, request: web.Request) -> web.Response:
        if self.burp.proxy:
            return web.json_response(self.burp.proxy.get_stats())
        return web.json_response({'running': False})
    
    async def get_ca_cert(self, request: web.Request) -> web.Response:
        if self.burp.proxy and self.burp.proxy.mitm.ca_cert:
            cert_bytes = self.burp.proxy.mitm.export_ca_cert()
            return web.Response(
                body=cert_bytes,
                content_type='application/x-x509-ca-cert',
                headers={'Content-Disposition': 'attachment; filename="customburp-ca.crt"'}
            )
        return web.json_response({'error': 'CA cert not available'}, status=404)
    
    async def get_pending_requests(self, request: web.Request) -> web.Response:
        # This would be implemented with a queue in the proxy
        return web.json_response({'pending': [], 'count': 0})
    
    # =========================================================================
    # REQUESTS / LOGGER
    # =========================================================================
    
    async def get_requests(self, request: web.Request) -> web.Response:
        host = request.query.get('host')
        method = request.query.get('method')
        search = request.query.get('search')
        limit = int(request.query.get('limit', 200))
        offset = int(request.query.get('offset', 0))
        tags = request.query.get('tags')
        
        tags_list = tags.split(',') if tags else None
        
        requests = self.burp.db.get_requests(
            host=host,
            method=method,
            search=search,
            tags=tags_list,
            limit=limit,
            offset=offset
        )
        
        return web.json_response(requests)
    
    async def get_request(self, request: web.Request) -> web.Response:
        req_id = request.match_info['id']
        req = self.burp.db.get_request(req_id)
        if not req:
            return web.json_response({'error': 'Request not found'}, status=404)
        return web.json_response(req)
    
    async def delete_request(self, request: web.Request) -> web.Response:
        req_id = request.match_info['id']
        self.burp.db.delete_request(req_id)
        return web.json_response({'deleted': True})
    
    async def clear_requests(self, request: web.Request) -> web.Response:
        self.burp.db.clear_all()
        return web.json_response({'cleared': True})
    
    async def export_requests(self, request: web.Request) -> web.Response:
        limit = int(request.query.get('limit', 10000))
        entries = self.burp.db.export_requests(limit=limit)
        return web.json_response(entries)
    
    async def get_hosts(self, request: web.Request) -> web.Response:
        return web.json_response({'hosts': self.burp.logger.get_hosts()})
    
    async def get_methods(self, request: web.Request) -> web.Response:
        return web.json_response({'methods': self.burp.logger.get_methods()})
    
    async def get_status_codes(self, request: web.Request) -> web.Response:
        return web.json_response(self.burp.logger.get_status_codes())
    
    # =========================================================================
    # REPEATER
    # =========================================================================
    
    async def repeater_send(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            result = await self.burp.repeater.send(data)
            return web.json_response(result)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def repeater_history(self, request: web.Request) -> web.Response:
        limit = int(request.query.get('limit', 50))
        return web.json_response(self.burp.repeater.get_history(limit=limit))
    
    # =========================================================================
    # INTRUDER
    # =========================================================================
    
    async def intruder_start(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            request_data = data.get('request', {})
            payloads = data.get('payloads', [])
            mode = data.get('mode', 'sniper')
            threads = int(data.get('threads', 5))
            
            # Parse position indicators from request text
            request_text = request_data.get('raw', '') or request_data.get('body', '') or ''
            positions = []
            
            if '!@' in request_text:
                # Find !@...!@ markers
                pos = 0
                while True:
                    start = request_text.find('!@', pos)
                    if start == -1:
                        break
                    end = request_text.find('@!', start + 2)
                    if end == -1:
                        break
                    positions.append((start, end + 2))
                    pos = end + 2
            
            # Run intruder in background
            asyncio.create_task(self._run_intruder(request_data, payloads, positions, mode, threads))
            
            return web.json_response({
                'status': 'started',
                'mode': mode,
                'payload_count': len(payloads),
                'threads': threads,
            })
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def _run_intruder(self, request_data, payloads, positions, mode, threads):
        """Run intruder attack"""
        results = await self.burp.intruder.attack(
            request_data=request_data,
            payload_sets=[payloads],
            position_indicators=positions,
            mode=mode,
            thread_count=threads
        )
        return results
    
    async def intruder_results(self, request: web.Request) -> web.Response:
        attack_id = request.match_info['attack_id']
        results = self.burp.intruder.get_results(attack_id)
        return web.json_response(results or [])
    
    async def intruder_status(self, request: web.Request) -> web.Response:
        return web.json_response({
            'is_running': self.burp.intruder.is_running() if self.burp.intruder else False,
            'modes': self.burp.intruder.get_mode_info() if self.burp.intruder else {},
        })
    
    async def intruder_clear(self, request: web.Request) -> web.Response:
        self.burp.intruder.clear_results()
        return web.json_response({'cleared': True})
    
    # =========================================================================
    # SCANNER
    # =========================================================================
    
    async def scan_run(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            host = data.get('host', '')
            paths = data.get('paths')
            
            if not host:
                return web.json_response({'error': 'Host required'}, status=400)
            
            # Run scan in background
            task = asyncio.create_task(self.burp.scanner.scan_host(host, paths=paths))
            
            return web.json_response({
                'status': 'started',
                'host': host,
                'scan_id': 'running'
            })
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def scan_status(self, request: web.Request) -> web.Response:
        return web.json_response(self.burp.scanner.get_scan_status())
    
    async def scan_results(self, request: web.Request) -> web.Response:
        scan_id = request.match_info['scan_id']
        results = self.burp.scanner.get_results(scan_id)
        if not results:
            return web.json_response({'error': 'Scan not found'}, status=404)
        return web.json_response(results)
    
    async def scan_all_results(self, request: web.Request) -> web.Response:
        return web.json_response(self.burp.scanner.get_all_results())
    
    # =========================================================================
    # ISSUES
    # =========================================================================
    
    async def get_issues(self, request: web.Request) -> web.Response:
        severity = request.query.get('severity')
        limit = int(request.query.get('limit', 100))
        issues = self.burp.db.get_issues(severity=severity, limit=limit)
        return web.json_response(issues)
    
    async def clear_issues(self, request: web.Request) -> web.Response:
        self.burp.db.clear_issues()
        return web.json_response({'cleared': True})
    
    # =========================================================================
    # DECODER
    # =========================================================================
    
    async def decoder_transform(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            action = data.get('action', '')
            input_data = data.get('input', '')
            
            result = self.burp.decoder.transform(action, input_data)
            return web.json_response(result)
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    # =========================================================================
    # TARGET / SCOPE
    # =========================================================================
    
    async def target_add(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            host = data.get('host', '')
            port = int(data.get('port', 0))
            included = data.get('include', True)
            self.burp.target.add_host(host, port, included)
            return web.json_response({'added': host})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def target_remove(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            host = data.get('host', '')
            self.burp.target.remove_host(host)
            return web.json_response({'removed': host})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def target_scope(self, request: web.Request) -> web.Response:
        return web.json_response(self.burp.target.get_scope())
    
    async def target_sitemap(self, request: web.Request) -> web.Response:
        host = request.query.get('host')
        return web.json_response(self.burp.target.get_sitemap(host=host))
    
    async def target_clear(self, request: web.Request) -> web.Response:
        self.burp.target.clear_scope()
        return web.json_response({'cleared': True})
    
    # =========================================================================
    # SESSION
    # =========================================================================
    
    async def session_create(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            name = data.get('name', '')
            session = self.burp.session.create_session(name)
            self.burp.session.set_session(session['session_id'])
            return web.json_response(session)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def session_list(self, request: web.Request) -> web.Response:
        return web.json_response({'sessions': self.burp.session.list_sessions()})
    
    async def session_active(self, request: web.Request) -> web.Response:
        session = self.burp.session.get_active_session()
        return web.json_response(session or {})
    
    async def session_set(self, request: web.Request) -> web.Response:
        session_id = request.match_info['session_id']
        self.burp.session.set_session(session_id)
        return web.json_response({'set': session_id})
    
    async def session_delete(self, request: web.Request) -> web.Response:
        session_id = request.match_info['session_id']
        self.burp.session.delete_session(session_id)
        return web.json_response({'deleted': session_id})
    
    async def session_add_cookie(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            self.burp.session.add_cookie(
                name=data.get('name', ''),
                value=data.get('value', ''),
                domain=data.get('domain', ''),
                path=data.get('path', '/'),
            )
            return web.json_response({'added': data.get('name', '')})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def session_add_token(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            self.burp.session.add_token(
                token_type=data.get('type', 'token'),
                value=data.get('value', ''),
            )
            return web.json_response({'added': data.get('type', 'token')})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def session_get_headers(self, request: web.Request) -> web.Response:
        headers = self.burp.session.get_session_headers()
        return web.json_response(headers)
    
    # =========================================================================
    # ORGANIZER
    # =========================================================================
    
    async def organizer_items(self, request: web.Request) -> web.Response:
        folder = request.query.get('folder')
        tag = request.query.get('tag')
        search = request.query.get('search')
        items = self.burp.organizer.get_items(folder=folder, tag=tag, search=search)
        return web.json_response({'items': items})
    
    async def organizer_add_tag(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            self.burp.organizer.add_tag(data.get('request_id', ''), data.get('tag', ''))
            return web.json_response({'tagged': data.get('tag', '')})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def organizer_remove_tag(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            self.burp.organizer.remove_tag(data.get('request_id', ''), data.get('tag', ''))
            return web.json_response({'untagged': data.get('tag', '')})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def organizer_set_folder(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            self.burp.organizer.set_folder(data.get('request_id', ''), data.get('folder', ''))
            return web.json_response({'foldered': data.get('folder', '')})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def organizer_set_notes(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            self.burp.organizer.set_notes(data.get('request_id', ''), data.get('notes', ''))
            return web.json_response({'notes_set': True})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def organizer_tags(self, request: web.Request) -> web.Response:
        return web.json_response({'tags': self.burp.organizer.get_tags()})
    
    async def organizer_folders(self, request: web.Request) -> web.Response:
        return web.json_response({'folders': self.burp.organizer.get_folders()})
    
    # =========================================================================
    # COMPARER
    # =========================================================================
    
    async def comparer_compare(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            left = data.get('left', {})
            right = data.get('right', {})
            result = self.burp.comparer.compare(left, right)
            return web.json_response(result)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    # =========================================================================
    # SEQUENCER
    # =========================================================================
    
    async def sequencer_analyze(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            tokens = data.get('tokens', [])
            name = data.get('name', '')
            result = self.burp.sequencer.analyze(tokens, name)
            return web.json_response(result)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    # =========================================================================
    # COLLABORATOR
    # =========================================================================
    
    async def collab_start(self, request: web.Request) -> web.Response:
        try:
            result = await self.burp.collaborator.start()
            return web.json_response(result)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def collab_stop(self, request: web.Request) -> web.Response:
        await self.burp.collaborator.stop()
        return web.json_response({'stopped': True})
    
    async def collab_status(self, request: web.Request) -> web.Response:
        return web.json_response(self.burp.collaborator.get_status())
    
    async def collab_payloads(self, request: web.Request) -> web.Response:
        return web.json_response(self.burp.collaborator.get_payloads())
    
    async def collab_interactions(self, request: web.Request) -> web.Response:
        return web.json_response({'interactions': self.burp.collaborator.get_interactions()})
    
    async def collab_clear(self, request: web.Request) -> web.Response:
        self.burp.collaborator.clear_interactions()
        return web.json_response({'cleared': True})
    
    # =========================================================================
    # ALERTS
    # =========================================================================
    
    async def get_alerts(self, request: web.Request) -> web.Response:
        severity = request.query.get('severity')
        alerts = self.burp.alerts.get_alerts(severity=severity)
        return web.json_response({'alerts': alerts})
    
    async def acknowledge_alert(self, request: web.Request) -> web.Response:
        alert_id = request.match_info['alert_id']
        self.burp.alerts.acknowledge(alert_id)
        return web.json_response({'acknowledged': alert_id})
    
    async def clear_alerts(self, request: web.Request) -> web.Response:
        self.burp.alerts.clear_all()
        return web.json_response({'cleared': True})
    
    async def alerts_summary(self, request: web.Request) -> web.Response:
        return web.json_response(self.burp.alerts.get_summary())
    
    # =========================================================================
    # PROJECTS
    # =========================================================================
    
    async def project_create(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            name = data.get('name', '')
            project_id = hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:12]
            
            project_data = {
                'id': project_id,
                'name': name,
                'created_at': time.time(),
                'updated_at': time.time(),
                'settings': {},
                'data_path': '',
            }
            
            self.burp.db.save_project(project_data)
            return web.json_response(project_data)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def project_list(self, request: web.Request) -> web.Response:
        return web.json_response({'projects': self.burp.db.list_projects()})
    
    async def project_get(self, request: web.Request) -> web.Response:
        project_id = request.match_info['id']
        project = self.burp.db.get_project(project_id)
        if not project:
            return web.json_response({'error': 'Project not found'}, status=404)
        return web.json_response(project)
    
    async def project_delete(self, request: web.Request) -> web.Response:
        project_id = request.match_info['id']
        self.burp.db.delete_project(project_id)
        return web.json_response({'deleted': project_id})
