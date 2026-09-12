"""
OSINT Aggregator v1 — Open Source Intelligence Tool
Reuniao de dados publicos: WHOIS, DNS, subdominios, emails, brechas, redes sociais
"""

import sys
import os
import json
import time
import re
import hashlib
import logging
import asyncio
import socket
import ssl
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

log_dir = Path(__file__).parent / 'log'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'osint.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('osint')


# =========================================================================
# Data Sources
# =========================================================================

class DataSource:
    """Base class for OSINT data sources"""
    name = ''
    description = ''
    
    async def collect(self, target: str) -> Dict:
        raise NotImplementedError


class WhoisData(DataSource):
    """WHOIS information collector"""
    name = 'whois'
    description = 'Domain registration info'
    
    def __init__(self):
        self.cache = {}
    
    def collect_sync(self, domain: str) -> Dict:
        """Collect WHOIS data synchronously"""
        if domain in self.cache:
            return self.cache[domain]
        
        try:
            import whois
            w = whois.whois(domain)
            data = {
                'domain': domain,
                'registrar': w.registrar if hasattr(w, 'registrar') else 'N/A',
                'creation_date': str(w.creation_date) if hasattr(w, 'creation_date') and w.creation_date else 'N/A',
                'expiration_date': str(w.expiration_date) if hasattr(w, 'expiration_date') and w.expiration_date else 'N/A',
                'updated_date': str(w.updated_date) if hasattr(w, 'updated_date') and w.updated_date else 'N/A',
                'name_servers': w.name_servers if hasattr(w, 'name_servers') else [],
                'status': w.status if hasattr(w, 'status') else 'N/A',
                'registrant_country': w.country if hasattr(w, 'country') else 'N/A',
                'registrant_organization': w.org if hasattr(w, 'org') else 'N/A',
                'raw': str(w)[:2000] if w else ''
            }
            self.cache[domain] = data
            return data
        except ImportError:
            return {'error': 'whois module not installed', 'pip': 'pip install python-whois'}
        except Exception as e:
            return {'error': str(e)}


class DnsData(DataSource):
    """DNS enumeration"""
    name = 'dns'
    description = 'DNS records and enumeration'
    
    COMMON_RECORDS = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA', 'PTR', 'SRV']
    
    def collect_sync(self, domain: str) -> Dict:
        results = {'domain': domain, 'records': {}}
        
        try:
            # A record
            try:
                addr = socket.getaddrinfo(domain, 80)
                ips = list(set(a[4][0] for a in addr))
                results['records']['A'] = ips
            except:
                pass
            
            # NS records via DNS lookup
            try:
                import subprocess
                r = subprocess.run(['dig', 'NS', domain, '+short'], 
                                 capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    results['records']['NS'] = [l.strip() for l in r.stdout.strip().split('\n') if l.strip()]
            except:
                pass
            
            # MX records
            try:
                r = subprocess.run(['dig', 'MX', domain, '+short'], 
                                 capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    results['records']['MX'] = [l.strip() for l in r.stdout.strip().split('\n') if l.strip()]
            except:
                pass
            
            # TXT records (SPF, DKIM, DMARC)
            try:
                r = subprocess.run(['dig', 'TXT', domain, '+short'], 
                                 capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    results['records']['TXT'] = [l.strip().strip('"') for l in r.stdout.strip().split('\n') if l.strip()]
            except:
                pass
            
            # CNAME
            try:
                r = subprocess.run(['dig', 'CNAME', domain, '+short'], 
                                 capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    results['records']['CNAME'] = [l.strip() for l in r.stdout.strip().split('\n') if l.strip()]
            except:
                pass
            
            # Reverse DNS on collected IPs
            reverse_ips = []
            for record_type, values in results['records'].items():
                if record_type == 'A':
                    for ip in values:
                        try:
                            hostname = socket.getptrname(ip)
                            if hostname and hostname != ip:
                                reverse_ips.append({'ip': ip, 'hostname': hostname})
                        except:
                            pass
            
            if reverse_ips:
                results['reverse_dns'] = reverse_ips
                
        except Exception as e:
            results['error'] = str(e)
        
        return results


class SubdomainEnum(DataSource):
    """Subdomain enumeration"""
    name = 'subdomain_enum'
    description = 'Discover subdomains'
    
    # Common subdomain wordlist
    WORDLIST = [
        'www', 'mail', 'ftp', 'ftp2', 'ftp3', 'ftp4', 'ftp5',
        'smtp', 'pop', 'pop3', 'imap', 'mx', 'ns1', 'ns2', 'ns3', 'ns4',
        'vpn', 'remote', 'dev', 'staging', 'stage', 'test', 'sandbox',
        'api', 'app', 'admin', 'dashboard', 'cpanel', 'webmail',
        'blog', 'shop', 'store', 'portal', 'members', 'login',
        'cdn', 'static', 'assets', 'media', 'images', 'img',
        'docs', 'wiki', 'kb', 'help', 'support',
        'status', 'monitor', 'grafana', 'kibana', 'elk',
        'git', 'github', 'gitlab', 'jira', 'confluence',
        'slack', 'teams', 'discord',
        'auth', 'oauth', 'sso', 'identity', 'accounts',
        'pay', 'billing', 'invoice', 'checkout',
        'ssl', 'secure', 'account', 'member',
        'm', 'mobile', 'apps',
        'en', 'pt', 'es', 'fr', 'de', 'jp', 'cn',
        'us', 'eu', 'uk', 'br', 'au', 'ca', 'mx',
        'i', 'beta', 'old', 'new', 'v2', 'v3',
        'dev1', 'dev2', 'dev3', 'prod', 'uat', 'preprod',
        'img0', 'img1', 'img2', 'img3',
        'upload', 'uploads', 'files', 'media', 'video', 'audio',
        'ec2', 'aws', 'azure', 'gcp', 'cloud',
        'st1', 'st2', 'st3', 'cdn1', 'cdn2',
        'fb', 'facebook', 'twitter', 'instagram', 'linkedin',
        'js', 'css', 'fonts', 'wp', 'wordpress',
        'tracking', 'analytics', 'tag', 'pixel',
        'mail1', 'mail2', 'mail3', 'smtp1', 'smtp2',
        'db', 'database', 'mysql', 'postgres',
        'search', 'news', 'press', 'about', 'contact',
        'careers', 'jobs', 'hr', 'team',
        'legal', 'privacy', 'terms', 'policy', 'compliance',
        'partners', 'affiliates', 'vendors',
        'proxy', 'gateway', 'jump', 'bastion',
        'jenkins', 'ci', 'cd', 'build',
        'nagios', 'zabbix', 'prometheus',
        'vpn1', 'vpn2', 'sslvpn',
    ]
    
    def collect_sync(self, domain: str, timeout: int = 2) -> Dict:
        results = {'domain': domain, 'subdomains': [], 'scan_time': time.time()}
        
        try:
            base_ip = None
            try:
                base_ip = socket.getaddrinfo(domain, 443)[0][4][0]
            except:
                pass
            
            found = set()
            
            # Try crt.sh (passive enumeration via HTTP)
            try:
                url = f"https://crt.sh/?q=%25.{domain}&output=json"
                req = urllib.request.Request(url, headers={'User-Agent': 'OSINT-Agent/1.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
                    for entry in data:
                        subj = entry.get('common_name', '')
                        name = entry.get('name_value', '')
                        for val in [subj, name]:
                            if val and val.endswith(f'.{domain}') and val != domain:
                                found.add(val.lower().strip('.'))
            except Exception as e:
                logger.debug(f"crt.sh failed: {e}")
            
            # Active enumeration
            if base_ip:
                # Check common subdomains
                for sub in self.WORDLIST:
                    full = f"{sub}.{domain}"
                    try:
                        addr = socket.getaddrinfo(full, 443, socket.AF_INET)
                        for a in addr:
                            ip = a[4][0]
                            if ip != base_ip or sub in ('www',):
                                found.add(full.lower())
                    except socket.gaierror:
                        pass
                    except Exception:
                        pass
                
                # Rate limit
                time.sleep(0.05)
            
            results['subdomains'] = sorted(found)
            results['total'] = len(results['subdomains'])
            
            # Passive: try DNS zone transfer (rarely works but worth trying)
            try:
                import subprocess
                r = subprocess.run(['dig', '-t', 'AXFR', domain, '@ns1.' + domain], 
                                 capture_output=True, text=True, timeout=5)
                if r.returncode == 0 and 'TRANSFER' in r.stdout.upper():
                    results['zone_transfer'] = 'POSSIBLE'
            except:
                pass
                
        except Exception as e:
            results['error'] = str(e)
        
        return results


class EmailHunter(DataSource):
    """Email discovery from public sources"""
    name = 'email_hunter'
    description = 'Find emails associated with domain'
    
    EMAIL_PATTERNS = [
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    ]
    
    def collect_sync(self, domain: str) -> Dict:
        results = {'domain': domain, 'emails': [], 'sources': {}}
        
        try:
            # Pattern-based extraction from known URLs
            patterns = [
                f'https://www.{domain}/contact',
                f'https://www.{domain}/about',
                f'https://www.{domain}/team',
                f'https://www.{domain}/careers',
                f'https://{domain}/contact',
                f'https://{domain}/about',
            ]
            
            email_regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.{domain}'.format(domain=re.escape(domain)))
            found_emails = set()
            
            for url in patterns:
                try:
                    req = urllib.request.Request(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        content = resp.read().decode('utf-8', errors='replace')
                        emails = email_regex.findall(content)
                        for e in emails:
                            found_emails.add(e.lower())
                except:
                    pass
            
            # Try common email formats
            common_names = ['admin', 'contact', 'info', 'support', 'sales', 'hello', 
                          'webmaster', 'postmaster', 'abuse', 'security', 'privacy',
                          'hr', 'jobs', 'press', 'media', 'feedback', 'help']
            for name in common_names:
                found_emails.add(f"{name}@{domain}")
            
            results['emails'] = sorted(found_emails)
            results['total'] = len(results['emails'])
            
        except Exception as e:
            results['error'] = str(e)
        
        return results


class BreachSearch(DataSource):
    """Check if domain appears in known breaches"""
    name = 'breach_search'
    description = 'Check against known data breaches'
    
    # Common breach indicators (simplified — in production use HaveIBeenPwned API)
    BREACH_INDICATORS = {
        'linkedin': 'LinkedIn breach (2012, 2021)',
        'adobe': 'Adobe breach (2013)',
        'yahoo': 'Yahoo breach (2013-2014)',
        'equifax': 'Equifax breach (2017)',
        'att': 'AT&T breach (2016)',
        'canva': 'Canva breach (2019)',
        'minecraft': 'Minecraft breach (2019)',
        'troyhunt': 'Collection #1 (2019)',
        'collection1': 'Collection #1 (2019)',
        'collection2': 'Collection #2 (2020)',
        'rumble': 'Rumble breach (2023)',
    }
    
    def collect_sync(self, domain: str) -> Dict:
        results = {'domain': domain, 'breaches': [], 'status': 'manual_check_required'}
        
        # Note: Real breach checking requires HaveIBeenPwned API key
        # This is a placeholder that explains how to use it properly
        results['note'] = 'Use https://haveibeenpwned.com/api/v3/breachedaccount/{email} with API key'
        results['breach_indicators'] = self.BREACH_INDICATORS
        
        return results


# =========================================================================
# Main Engine
# =========================================================================

class OSINTAggregator:
    """Main OSINT aggregation engine"""
    
    def __init__(self):
        self.sources = {
            'whois': WhoisData(),
            'dns': DnsData(),
            'subdomains': SubdomainEnum(),
            'emails': EmailHunter(),
            'breaches': BreachSearch(),
        }
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour
    
    def collect(self, target: str, sources: Optional[List[str]] = None) -> Dict:
        """Collect OSINT data from all specified sources"""
        if sources is None:
            sources = list(self.sources.keys())
        
        target = target.lower().strip()
        # Remove protocol and path
        target = re.sub(r'^https?://', '', target)
        target = target.split('/')[0]
        target = target.split(':')[0]
        
        result = {
            'target': target,
            'collected_at': datetime.now().isoformat(),
            'elapsed_seconds': 0,
            'sources': {},
            'summary': {}
        }
        
        start = time.time()
        
        for source_name in sources:
            if source_name not in self.sources:
                continue
            
            source = self.sources[source_name]
            try:
                data = source.collect_sync(target)
                result['sources'][source_name] = data
            except Exception as e:
                result['sources'][source_name] = {'error': str(e)}
        
        result['elapsed_seconds'] = round(time.time() - start, 2)
        
        # Generate summary
        result['summary'] = self._generate_summary(result)
        
        # Cache
        self._cache[target] = result
        self._cache[target]['cached_at'] = time.time()
        
        return result
    
    def _generate_summary(self, data: Dict) -> Dict:
        """Generate a human-readable summary"""
        summary = {
            'total_sources': len(data.get('sources', {})),
            'total_subdomains': 0,
            'total_emails': 0,
            'ip_addresses': [],
            'name_servers': [],
            'mail_servers': [],
            'risk_indicators': [],
        }
        
        sources = data.get('sources', {})
        
        # DNS subdomains
        if 'subdomains' in sources:
            subs = sources['subdomains'].get('subdomains', [])
            summary['total_subdomains'] = len(subs)
            summary['risk_indicators'].append(f'{len(subs)} subdomains found')
        
        # DNS IPs
        if 'dns' in sources:
            records = sources['dns'].get('records', {})
            if 'A' in records:
                summary['ip_addresses'] = records['A'][:10]
            if 'NS' in records:
                summary['name_servers'] = records['NS']
            if 'MX' in records:
                summary['mail_servers'] = records['MX']
        
        # Emails
        if 'emails' in sources:
            emails = sources['emails'].get('emails', [])
            summary['total_emails'] = len(emails)
        
        # WHOIS info
        if 'whois' in sources:
            w = sources['whois']
            if 'error' not in w:
                if w.get('registrant_organization'):
                    summary['organization'] = w['registrant_organization']
                if w.get('creation_date'):
                    summary['domain_age'] = f"Created: {w['creation_date']}"
        
        return summary
    
    def get_cached(self, target: str) -> Optional[Dict]:
        """Get cached result if still valid"""
        if target in self._cache:
            age = time.time() - self._cache[target].get('cached_at', 0)
            if age < self._cache_ttl:
                return self._cache[target]
        return None
    
    def export_json(self, result: Dict, filepath: Optional[str] = None) -> str:
        """Export results to JSON file"""
        if filepath is None:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"osint_{result['target']}_{ts}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        return filepath


# =========================================================================
# CLI Entry
# =========================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='OSINT Aggregator — Coleta de inteligencia fontes aberturas')
    parser.add_argument('target', nargs='?', help='Target domain (e.g., example.com)')
    parser.add_argument('--sources', '-s', nargs='*', 
                       help='Sources: whois, dns, subdomains, emails, breaches',
                       default=['whois', 'dns', 'subdomains', 'emails'])
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    parser.add_argument('--export', '-e', help='Export to file')
    parser.add_argument('--list-sources', action='store_true', help='List available sources')
    parser.add_argument('--cache', action='store_true', help='Use cached results')
    
    args = parser.parse_args()
    
    engine = OSINTAggregator()
    
    if args.list_sources:
        print("\nAvailable OSINT sources:")
        for name, source in engine.sources.items():
            print(f"  {name:15s} — {source.description}")
        print()
        sys.exit(0)
    
    if not args.target:
        print("""
OSINT Aggregator v1 — Coleta de inteligencia de fontes aberturas
Uso:
  python osint_aggregator.py example.com
  python osint_aggregator.py example.com --sources whois dns subdomains
  python osint_aggregator.py example.com --json
  python osint_aggregator.py example.com --export report.json
  python osint_aggregator.py --list-sources
""")
        sys.exit(0)
    
    # Get or collect
    if args.cache:
        result = engine.get_cached(args.target)
        if result:
            print(f"[CACHE] Using cached results for {args.target}")
        else:
            result = engine.collect(args.target, sources=args.sources)
    else:
        result = engine.collect(args.target, sources=args.sources)
    
    # Export
    if args.export:
        filepath = engine.export_json(result, args.export)
        print(f"[+] Exported to: {filepath}")
    
    # Output
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        print(f"\n{'='*60}")
        print(f"  OSINT Report: {result['target']}")
        print(f"  Collected: {result['collected_at']}")
        print(f"  Elapsed: {result['elapsed_seconds']}s")
        print(f"{'='*60}\n")
        
        summary = result.get('summary', {})
        
        print("📊 Summary:")
        print(f"  Subdomains found: {summary.get('total_subdomains', 0)}")
        print(f"  Emails found: {summary.get('total_emails', 0)}")
        print(f"  IPs: {', '.join(summary.get('ip_addresses', ['N/A']))[:100]}")
        print(f"  Name Servers: {', '.join(summary.get('name_servers', ['N/A']))}")
        print(f"  Mail Servers: {', '.join(summary.get('mail_servers', ['N/A']))}")
        if summary.get('organization'):
            print(f"  Organization: {summary['organization']}")
        if summary.get('domain_age'):
            print(f"  Domain Age: {summary['domain_age']}")
        
        if summary.get('risk_indicators'):
            print(f"\n⚠️  Risk Indicators:")
            for ind in summary['risk_indicators']:
                print(f"  • {ind}")
        
        # Show subdomains
        subs = result.get('sources', {}).get('subdomains', {}).get('subdomains', [])
        if subs:
            print(f"\n🌐 Subdomains ({len(subs)}):")
            for s in subs[:30]:
                print(f"  • {s}")
            if len(subs) > 30:
                print(f"  ... and {len(subs) - 30} more")
        
        # Show emails
        emails = result.get('sources', {}).get('emails', {}).get('emails', [])
        if emails:
            print(f"\n📧 Emails ({len(emails)}):")
            for e in emails[:20]:
                print(f"  • {e}")
        
        # Show DNS records
        dns = result.get('sources', {}).get('dns', {}).get('records', {})
        if dns:
            print(f"\n🔍 DNS Records:")
            for rtype, values in dns.items():
                if values:
                    print(f"  {rtype}: {', '.join(str(v) for v in values[:5])}")
        
        # Show WHOIS
        whois = result.get('sources', {}).get('whois', {})
        if whois and 'error' not in whois:
            print(f"\n📋 WHOIS:")
            for k, v in whois.items():
                if k not in ('domain', 'raw') and v and v != 'N/A':
                    print(f"  {k}: {v}")
    
    print()


if __name__ == '__main__':
    main()
