"""
CustomBurp - Alerts System
Sistema de alertas e notificacoes para issues detectadas
"""

import threading
import time
import logging
from typing import Dict, List, Callable, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger('custom_burp')


class Alert:
    """Representa um alert"""
    
    def __init__(self, alert_id: str, timestamp: float, alert_type: str,
                 severity: str, description: str, request_id: str = '',
                 evidence: str = '', solution: str = '', acknowledged: bool = False):
        self.alert_id = alert_id
        self.timestamp = timestamp
        self.alert_type = alert_type
        self.severity = severity
        self.description = description
        self.request_id = request_id
        self.evidence = evidence
        self.solution = solution
        self.acknowledged = acknowledged
        self.read = False
    
    def to_dict(self) -> Dict:
        return {
            'alert_id': self.alert_id,
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'alert_type': self.alert_type,
            'severity': self.severity,
            'description': self.description,
            'request_id': self.request_id,
            'evidence': self.evidence[:200] if self.evidence else '',
            'solution': self.solution[:200] if self.solution else '',
            'acknowledged': self.acknowledged,
            'read': self.read
        }


class Alerts:
    """Sistema de alerts para CustomBurp"""
    
    SEVERITY_ORDER = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'Info': 4}
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self._callbacks: List[Callable] = []
        self._lock = threading.Lock()
        self._rules: List[Dict] = []
        self._auto_acknowledge = False
    
    def add_alert(self, alert_type: str, severity: str, description: str,
                  request_id: str = '', evidence: str = '', solution: str = '') -> Alert:
        """Adiciona um novo alert"""
        alert_id = f"{alert_type[:4]}_{int(time.time() * 1000)}"
        
        alert = Alert(
            alert_id=alert_id,
            timestamp=time.time(),
            alert_type=alert_type,
            severity=severity,
            description=description,
            request_id=request_id,
            evidence=evidence,
            solution=solution
        )
        
        with self._lock:
            self.alerts.append(alert)
        
        # Aplicar regras automaticas
        self._apply_rules(alert)
        
        # Notificar callbacks
        for cb in self._callbacks:
            try:
                cb(alert)
            except:
                pass
        
        logger.warning(f"Alert: [{severity}] {alert_type} - {description[:60]}")
        return alert
    
    def _apply_rules(self, alert: Alert):
        """Aplica regras automaticas ao alert"""
        for rule in self._rules:
            if rule.get('type') == 'auto_acknowledge':
                if alert.severity in rule.get('severities', []):
                    alert.acknowledged = True
            elif rule.get('type') == 'auto_read':
                if alert.severity in rule.get('severities', []):
                    alert.read = True
    
    def add_rule(self, rule: Dict):
        """Adiciona regra de automatico"""
        self._rules.append(rule)
    
    def remove_alert(self, alert_id: str) -> bool:
        """Remove alert"""
        with self._lock:
            self.alerts = [a for a in self.alerts if a.alert_id != alert_id]
        return True
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Marca alert como acknowledged"""
        with self._lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    return True
        return False
    
    def mark_as_read(self, alert_id: str) -> bool:
        """Marca alert como lido"""
        with self._lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.read = True
                    return True
        return False
    
    def mark_all_read(self):
        """Marca todos como lidos"""
        with self._lock:
            for alert in self.alerts:
                alert.read = True
    
    def get_alerts(self, severity: str = None, alert_type: str = None,
                   acknowledged: bool = None, limit: int = 100) -> List[Dict]:
        """Retorna alerts com filtros"""
        with self._lock:
            alerts = self.alerts[:]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        
        # Ordenar por severidade puis timestamp
        alerts.sort(key=lambda a: (
            self.SEVERITY_ORDER.get(a.severity, 99),
            -a.timestamp
        ))
        
        return [a.to_dict() for a in alerts[:limit]]
    
    def get_unread_count(self) -> int:
        """Retorna numero de alerts nao lidos"""
        with self._lock:
            return sum(1 for a in self.alerts if not a.read)
    
    def get_summary(self) -> Dict:
        """Retorna resumo dos alerts"""
        with self._lock:
            summary = defaultdict(int)
            unread = 0
            for alert in self.alerts:
                summary[alert.severity] += 1
                if not alert.read:
                    unread += 1
            
            type_summary = defaultdict(int)
            for alert in self.alerts:
                type_summary[alert.alert_type] += 1
        
        return {
            'total': len(self.alerts),
            'unread': unread,
            'by_severity': dict(summary),
            'by_type': dict(type_summary),
            'recent': [a.to_dict() for a in sorted(self.alerts, key=lambda a: a.timestamp, reverse=True)[:5]]
        }
    
    def clear_all(self):
        """Limpa todos os alerts"""
        with self._lock:
            self.alerts.clear()
    
    def add_callback(self, callback: Callable):
        """Adiciona callback para novos alerts"""
        self._callbacks.append(callback)
    
    def export_alerts(self, path: str = None) -> str:
        """Exporta alerts para JSON"""
        import json
        if not path:
            from datetime import datetime
            path = f'alerts-export-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
        
        with self._lock:
            data = [a.to_dict() for a in self.alerts]
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return path


if __name__ == '__main__':
    alerts = Alerts()
    
    # Adicionar alerts
    a1 = alerts.add_alert('XSS', 'High', 'Cross-Site Scripting detected', 'req_001', '<script>alert(1)</script>')
    a2 = alerts.add_alert('SQLi', 'Critical', 'SQL Injection detected', 'req_002', "OR 1=1")
    a3 = alerts.add_alert('Header', 'Low', 'Missing Security Header', 'req_003', 'X-Frame-Options')
    
    print(f"Total alerts: {len(alerts.alerts)}")
    print(f"Unread: {alerts.get_unread_count()}")
    
    # Summary
    summary = alerts.get_summary()
    print(f"Summary: {summary}")
    
    # Get alerts
    high_alerts = alerts.get_alerts(severity='High')
    print(f"High alerts: {len(high_alerts)}")
    
    # Acknowledge
    alerts.acknowledge_alert(a1.alert_id)
    print(f"After ack: {alerts.get_summary()['by_severity']}")
    
    print("\nAlerts OK!")
