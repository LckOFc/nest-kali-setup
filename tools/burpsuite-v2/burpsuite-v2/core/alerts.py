"""
CustomBurp v2 - Alert System
Real-time alerts based on request patterns
"""

import hashlib
import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger('custom_burp.alerts')


class Alerts:
    """Real-time alert system"""
    
    ALERT_RULES = [
        {
            'name': 'SQL Error Detected',
            'check': lambda req, resp: any(p in (resp.get('body', '') or '').lower() 
                                           for p in ['sql syntax', 'mysql', 'sqlite', 'odbc', 'postgresql']),
            'severity': 'High',
            'type': 'sql_error',
        },
        {
            'name': 'Server Error (5xx)',
            'check': lambda req, resp: 500 <= (resp.get('status_code', 0) or 0) < 600,
            'severity': 'Medium',
            'type': 'server_error',
        },
        {
            'name': 'Sensitive Data Exposure',
            'check': lambda req, resp: any(p in (resp.get('body', '') or '').lower()
                                           for p in ['password', 'secret', 'api_key', 'private_key', 'access_token']),
            'severity': 'High',
            'type': 'sensitive_data',
        },
        {
            'name': 'Potential XSS',
            'check': lambda req, resp: any(p in (resp.get('body', '') or '').lower()
                                           for p in ['<script', 'javascript:', 'onerror=', 'onload=']),
            'severity': 'Medium',
            'type': 'xss_suspect',
        },
        {
            'name': 'Debug Mode Active',
            'check': lambda req, resp: any(h.lower() in ('debug', 'trace', 'development') 
                                           for h in (resp.get('headers', {}) or {}).values()),
            'severity': 'Low',
            'type': 'debug_mode',
        },
        {
            'name': 'No HTTPS',
            'check': lambda req, resp: not req.get('url', '').startswith('https://') 
                                       and 'login' in req.get('path', '').lower(),
            'severity': 'Medium',
            'type': 'insecure_auth',
        },
    ]
    
    def __init__(self, db):
        self.db = db
        self._alerts: List[Dict] = []
    
    def check_request(self, request_data: Dict, response_data: Dict):
        """Check request/response for alert conditions"""
        for rule in self.ALERT_RULES:
            try:
                if rule['check'](request_data, response_data):
                    alert_id = hashlib.md5(f"{rule['name']}{request_data.get('id', '')}{time.time()}".encode()).hexdigest()[:16]
                    
                    alert = {
                        'id': alert_id,
                        'timestamp': time.time(),
                        'type': rule['type'],
                        'severity': rule['severity'],
                        'message': f"{rule['name']}: {request_data.get('method', '')} {request_data.get('full_url', request_data.get('path', ''))}",
                        'evidence': json.dumps({
                            'method': request_data.get('method'),
                            'url': request_data.get('full_url', request_data.get('path')),
                            'status_code': response_data.get('status_code'),
                        }),
                        'request_id': request_data.get('id', ''),
                        'acknowledged': 0,
                    }
                    
                    self._alerts.append(alert)
                    
                    # Save to DB
                    self.db.save_alert(alert)
                    
                    logger.info(f"Alert triggered: {rule['name']}")
                    
            except Exception as e:
                logger.debug(f"Alert check error: {e}")
    
    def get_alerts(self, severity: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get alerts"""
        alerts = self.db.get_alerts(severity=severity, limit=limit)
        return alerts
    
    def acknowledge(self, alert_id: str):
        """Acknowledge an alert"""
        self.db.acknowledge_alert(alert_id)
        for a in self._alerts:
            if a['id'] == alert_id:
                a['acknowledged'] = 1
    
    def clear_all(self):
        """Clear all alerts"""
        self._alerts.clear()
        self.db.clear_alerts()
    
    def get_summary(self) -> Dict:
        """Get alert summary"""
        alerts = self.get_alerts()
        summary = {
            'total': len(alerts),
            'unacknowledged': len([a for a in alerts if not a.get('acknowledged')]),
            'by_severity': {},
            'by_type': {},
        }
        
        for a in alerts:
            sev = a.get('severity', 'Unknown')
            typ = a.get('type', 'unknown')
            summary['by_severity'][sev] = summary['by_severity'].get(sev, 0) + 1
            summary['by_type'][typ] = summary['by_type'].get(typ, 0) + 1
        
        return summary
