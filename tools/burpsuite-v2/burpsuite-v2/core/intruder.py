"""
CustomBurp v2 - Intruder Engine
Payload injection com modos reais: Sniper, Battering Ram, Pitchfork, Cluster Bomb
"""

import asyncio
import hashlib
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import re

logger = logging.getLogger('custom_burp.intruder')


class Intruder:
    """Real payload-based attack engine"""
    
    MODES = {
        'sniper': 'Sniper - one payload per position',
        'battering_ram': 'Battering Ram - same payload at all positions',
        'pitchfork': 'Pitchfork - one payload per position from separate lists',
        'cluster_bomb': 'Cluster Bomb - all combinations of payloads',
    }
    
    def __init__(self, db, max_concurrent: int = 10):
        self.db = db
        self.max_concurrent = max_concurrent
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self._results: Dict[str, List[Dict]] = {}
        self._running = False
    
    async def attack(self, 
                     request_data: Dict,
                     payload_sets: List[List[str]],
                     position_indicators: List[Tuple[int, int]],
                     mode: str = 'sniper',
                     thread_count: int = 5) -> List[Dict]:
        """Execute intruder attack"""
        if mode not in self.MODES:
            mode = 'sniper'
        
        attack_id = hashlib.md5(f"{request_data.get('id', 'unknown')}{time.time()}".encode()).hexdigest()[:12]
        self._running = True
        
        logger.info(f"Intruder attack {attack_id} started: mode={mode}, payloads={len(payload_sets)}, threads={thread_count}")
        
        # Generate payload combinations based on mode
        combinations = self._generate_combinations(payload_sets, mode)
        logger.info(f"Intruder attack {attack_id}: {len(combinations)} total combinations")
        
        results = []
        sem = asyncio.Semaphore(thread_count)
        
        async def worker(combo_idx: int, combo_payloads: List[str]):
            async with sem:
                try:
                    result = await self._execute_single(
                        request_data, combo_payloads, combo_idx, attack_id
                    )
                    results.append(result)
                    
                    # Save to DB
                    self.db.save_intruder_result({
                        'id': hashlib.md5(f"{attack_id}{combo_idx}{time.time()}".encode()).hexdigest()[:16],
                        'timestamp': time.time(),
                        'request_id': request_data.get('id', ''),
                        'payload_set': combo_idx,
                        'payload_value': ' | '.join(combo_payloads),
                        'status_code': result.get('response', {}).get('status_code', 0),
                        'response_length': len(result.get('response', {}).get('body', '')),
                        'time_ms': result.get('time_ms', 0),
                        'result': result,
                        'is_highlighted': result.get('highlight', False),
                    })
                    
                except Exception as e:
                    logger.error(f"Intruder worker error: {e}")
                    results.append({
                        'index': combo_idx,
                        'payload': ' | '.join(combo_payloads),
                        'error': str(e),
                        'status_code': 0,
                        'response_length': 0,
                        'time_ms': 0,
                    })
        
        # Schedule all workers
        tasks = []
        for idx, payloads in enumerate(combinations):
            tasks.append(worker(idx, payloads))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self._running = False
        self._results[attack_id] = results
        
        logger.info(f"Intruder attack {attack_id} completed: {len(results)} results")
        return results
    
    def _generate_combinations(self, payload_sets: List[List[str]], mode: str) -> List[List[str]]:
        """Generate payload combinations based on mode"""
        if mode == 'sniper':
            # One payload at a time across all positions
            combos = []
            for payloads in payload_sets:
                for payload in payloads:
                    combos.append([payload])
            return combos
        
        elif mode == 'battering_ram':
            # Same payload at all positions
            if payload_sets:
                first_set = payload_sets[0]
                return [[p] * len(payload_sets) for p in first_set]
            return []
        
        elif mode == 'pitchfork':
            # One from each set simultaneously
            if not payload_sets:
                return []
            combos = [[]]
            for payload_set in payload_sets:
                new_combos = []
                for combo in combos:
                    for payload in payload_set:
                        new_combos.append(combo + [payload])
                combos = new_combos
            return combos
        
        elif mode == 'cluster_bomb':
            # All combinations (Cartesian product)
            if not payload_sets:
                return []
            combos = [[]]
            for payload_set in payload_sets:
                new_combos = []
                for combo in combos:
                    for payload in payload_set:
                        new_combos.append(combo + [payload])
                combos = new_combos
            return combos
        
        return []
    
    async def _execute_single(self, request_data: Dict, 
                               payloads: List[str],
                               idx: int,
                               attack_id: str) -> Dict:
        """Execute a single request with payloads"""
        from core.repeater import Repeater
        from core.proxy import BurpProxy
        
        repeater = Repeater(self.db)
        
        # Apply payloads to request
        modified_request = self._apply_payloads(request_data, payloads)
        
        start_time = time.time()
        result = await repeater.send(modified_request)
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Determine highlight
        resp = result.get('response', {})
        status_code = resp.get('status_code', 0)
        resp_body = resp.get('body', '')
        
        highlight = False
        highlight_reason = ''
        
        # Highlight different status codes
        if status_code and status_code != request_data.get('expected_status', 0):
            highlight = True
            highlight_reason = f"Status {status_code} differs from expected"
        
        # Highlight different response lengths
        orig_length = len(request_data.get('original_body', resp_body))
        if orig_length > 0 and abs(len(resp_body) - orig_length) > orig_length * 0.1:
            highlight = True
            highlight_reason = f"Response length differs: {len(resp_body)} vs {orig_length}"
        
        return {
            'index': idx,
            'attack_id': attack_id,
            'payload': ' | '.join(payloads),
            'payloads': payloads,
            'status_code': status_code,
            'response_length': len(resp_body),
            'time_ms': elapsed_ms,
            'response': resp,
            'highlight': highlight,
            'highlight_reason': highlight_reason,
            'error': result.get('error', ''),
        }
    
    def _apply_payloads(self, request_data: Dict, payloads: List[str]) -> Dict:
        """Apply payloads to request data"""
        import copy
        modified = copy.deepcopy(request_data)
        
        body = modified.get('body', '')
        url = modified.get('url', '')
        headers = dict(modified.get('headers', {}))
        
        # Find markers in body: !@payload!@ or just replace position markers
        payload_idx = 0
        for pos_start, pos_end in modified.get('_positions', []):
            if payload_idx < len(payloads):
                body = body[:pos_start] + payloads[payload_idx] + body[pos_end:]
                payload_idx += 1
        
        # Also check for !@...!@ markers
        if '!@' in body:
            parts = body.split('!@')
            new_body = ''
            p_idx = 0
            for i, part in enumerate(parts):
                new_body += part
                if i % 2 == 1 and p_idx < len(payloads):
                    new_body += payloads[p_idx]
                    p_idx += 1
            body = new_body
        
        modified['body'] = body
        
        # Update Content-Length if body changed
        if body and 'Content-Length' in headers:
            headers['Content-Length'] = str(len(body.encode('utf-8')))
        elif body:
            headers['Content-Length'] = str(len(body.encode('utf-8')))
        
        modified['headers'] = headers
        
        return modified
    
    def get_results(self, attack_id: str) -> List[Dict]:
        """Get results for an attack"""
        return self._results.get(attack_id, [])
    
    def get_all_results(self) -> Dict[str, List[Dict]]:
        """Get all attack results"""
        return dict(self._results)
    
    def clear_results(self):
        """Clear all results"""
        self._results.clear()
    
    def is_running(self) -> bool:
        return self._running
    
    def get_mode_info(self) -> Dict:
        """Get mode descriptions"""
        return self.MODES
