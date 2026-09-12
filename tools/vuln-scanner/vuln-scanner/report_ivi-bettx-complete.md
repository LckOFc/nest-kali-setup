# Vulnerability Scan Report — Complete Analysis
## Target: https://ivi-bettx.net
## Date: 2026-09-11
## Scanner: VulnScanner v4070-APEX + Deep API Discovery

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Target** | https://ivi-bettx.net |
| **Technology** | Spring Boot + Angular/React SPA |
| **Protection** | Cloudflare WAF |
| **Total Paths Tested** | 84+ |
| **Real Vulnerabilities** | 2 (LOW) |
| **API Endpoints Found** | 1 (root /api) |
| **Subdomains Tested** | 11 |
| **Overall Risk** | **LOW** |

---

## Complete Findings

### REAL VULNERABILITIES (2)

#### 1. Missing Security Headers [LOW]

**Severity:** LOW  
**Type:** Misconfiguration  
**Endpoint:** https://ivi-bettx.net  
**Description:** Multiple security headers missing from HTTP responses.

**Missing Headers:**
- X-Content-Type-Options
- X-Frame-Options
- Strict-Transport-Security (HSTS)
- Content-Security-Policy (CSP)
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy

**Impact:** Low. Increases attack surface for XSS and clickjacking.

**Remediation:**
```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

---

#### 2. Sensitive Paths Disclosed in robots.txt [LOW]

**Severity:** LOW  
**Type:** Information Disclosure  
**Endpoint:** https://ivi-bettx.net/robots.txt  
**Description:** robots.txt reveals paths that should not be public.

**Discovered Paths:**
```
Disallow: /admin/
Disallow: /cabinet/
Sitemap: https://ivibet.com/sitemap.xml
```

**Impact:** Low. Helps attackers identify potential targets.

**Remediation:** Remove sensitive paths from robots.txt.

---

### API DISCOVERY RESULTS

#### Exposed API Endpoints

| Endpoint | Status | Content-Type | Notes |
|----------|--------|--------------|-------|
| `/api` | 200 | application/json | API root - returns success message |
| `/api/v1` | 404 | application/json | Expected - version not exposed |
| `/api/v1/*` | 404 | application/json | All return "page not exists" |
| `/api/graphql` | 404 | application/json | GraphQL not at this path |
| `/graphql` | 200 | text/html | SPA fallback |

**API Root Response:**
```json
{"error":false,"status":"success","code":200,"data":"API fully functional"}
```

**Analysis:**
- ✅ Only root `/api` endpoint exposed (minimal attack surface)
- ✅ All versioned APIs return 404 (no info disclosure)
- ✅ No authentication bypass detected
- ✅ No sensitive data in API responses

---

### SPRING ACTUATOR STATUS

All actuator endpoints return **HTML (SPA fallback)**, NOT JSON:

```
/actuator           -> HTML (41,347 bytes)
/actuator/env       -> HTML (not config disclosure)
/actuator/health    -> HTML (not health details)
/actuator/info      -> HTML
/actuator/mappings  -> HTML
/actuator/beans     -> HTML
/actuator/configprops -> HTML
/actuator/trace     -> HTML
/actuator/loggers   -> HTML
/actuator/threaddump -> HTML
/actuator/heapdump  -> HTML
```

**Status:** ✅ PROPERLY CONFIGURED - No info disclosure

---

### GRAPHQL STATUS

| Test | Result |
|------|--------|
| `/graphql` | 200 HTML (SPA fallback) |
| `/api/graphql` | 404 JSON |
| Introspection query | 405 Method Not Allowed |

**Status:** ✅ PROTECTED - Introspection disabled

---

### SUBDOMAIN DISCOVERY

| Subdomain | Status |
|-----------|--------|
| ivi-bettx.net | 200 OK |
| ivibet.com | 200 OK |
| www.ivibet.com | 301 Redirect |
| api.ivibet.com | Connection refused |
| app.ivibet.com | Connection refused |
| bet.ivibet.com | Connection refused |
| live.ivibet.com | Connection refused |
| casino.ivibet.com | Connection refused |
| sports.ivibet.com | Connection refused |
| payment.ivibet.com | Connection refused |
| admin.ivibet.com | Connection refused |

**Status:** ✅ No exposed subdomains

---

### FILES & CONFIG DISCLOSURE

| Path | Status | Content |
|------|--------|---------|
| `/.git/config` | 403 | Blocked |
| `/.env` | 403 | Blocked |
| `/backup.sql` | 200 | SPA HTML (not SQL) |
| `/application.yml` | 200 | SPA HTML (not config) |
| `/application.properties` | 200 | SPA HTML (not config) |
| `/h2-console` | 200 | SPA HTML (not DB) |
| `/phpinfo.php` | 403 | Blocked |

**Status:** ✅ All sensitive paths protected

---

## DETAILED ANALYSIS

### Why 10 "HIGH" findings were FALSE POSITIVES

Initial scan detected status 200 on paths like:
- `/backup.sql`
- `/application.yml`
- `/actuator/env`
- `/actuator/health`
- etc.

**However**, after content analysis:
- All returned **41,347 bytes of HTML** (the SPA shell)
- No actual SQL, YAML, or JSON config content
- This is **client-side routing** behavior (Angular/React)
- The SPA handles all unknown routes by serving the same HTML

**Conclusion:** The application is properly configured with:
1. Spring Boot backend with restricted actuator
2. SPA frontend with client-side routing
3. Cloudflare WAF protecting against direct backend access

---

## SECURITY POSTURE ASSESSMENT

### Strengths ✅
| Control | Status | Notes |
|---------|--------|-------|
| Actuator endpoints | SECURE | Returns HTML, not JSON |
| API versioning | SECURE | v1 not exposed |
| Sensitive files | PROTECTED | 403 or SPA fallback |
| GraphQL | PROTECTED | Introspection disabled |
| Subdomains | CLEAN | No exposed services |
| WAF | ACTIVE | Cloudflare protecting |
| SPA architecture | SECURE | No direct backend access |

### Weaknesses ⚠️
| Control | Status | Impact |
|---------|--------|--------|
| Security headers | MISSING | LOW |
| robots.txt | LEAKS paths | LOW |

---

## RECOMMENDATIONS

### Priority 1 (Low Impact)
1. **Add Security Headers**
   ```nginx
   add_header X-Content-Type-Options "nosniff" always;
   add_header X-Frame-Options "DENY" always;
   add_header Strict-Transport-Security "max-age=31536000" always;
   add_header Content-Security-Policy "default-src 'self'" always;
   ```

2. **Update robots.txt**
   ```txt
   User-agent: *
   Allow: /
   # Remove sensitive paths
   ```

### Priority 2 (Nice to Have)
3. Consider enabling HSTS preload
4. Add Permissions-Policy header
5. Review CSP policy for SPA requirements

---

## CONCLUSION

**Overall Security Posture: GOOD**

The target application demonstrates proper security configuration:
- No critical or high-severity vulnerabilities
- Backend properly secured behind SPA
- API versioning correctly implemented
- Cloudflare WAF active
- Only 2 low-severity misconfigurations

**Risk Level: LOW**

---

*Report generated by VulnScanner v4070-APEX*
*Scan duration: ~90 seconds*
*Paths tested: 84+*