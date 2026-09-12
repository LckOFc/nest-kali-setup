# CVE-2020-0688 Exchange Server RCE - Complete Exploit Toolkit

> **For Authorized Security Testing Only**  
> This toolkit is designed for penetration testing and vulnerability assessment of Microsoft Exchange Server installations. Use only with explicit written authorization.

## 🎯 Overview

CVE-2020-0688 is a **Critical (CVSS 7.5)** vulnerability affecting Microsoft Exchange Server 2013, 2016, and 2019. It allows **unauthenticated remote code execution** via forged ASP.NET ViewState tokens using hardcoded MachineKeys.

### Affected Versions
- Exchange Server 2013 CU23 and earlier
- Exchange Server 2016 CU18 and earlier
- Exchange Server 2019 CU5 and earlier

### Attack Vector
```
Attacker → Exchange ECP (/ecp/) → ASP.NET ViewState Deserialization → RCE
```

## 📁 Files

| File | Description |
|------|-------------|
| `cve_2020_0688_exchange_rce.py` | Main exploit script |
| `cve_2020_0688_payload_gen.py` | Payload generator |
| `cve_2020_0688_auditor.py` | Bulk scanner/auditor |
| `run_exploit.sh` | Quick usage wrapper |
| `requirements.txt` | Python dependencies |

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Check vulnerability
python3 cve_2020_0688_exchange_rce.py --target https://exchange.company.com --check

# Generate payload
python3 cve_2020_0688_payload_gen.py --cmd "whoami" --format psh

# Full exploit
python3 cve_2020_0688_exchange_rce.py --target https://exchange.company.com --cmd "whoami"
```

## 🔬 Technical Deep Dive

### Root Cause

Exchange Server's ECP (Exchange Control Panel) uses ASP.NET Web Forms with a **hardcoded MachineKey** in web.config:

```xml
<machineKey validationKey="45B641FD..." 
            decryptionKey="D044257A..." 
            validation="HMACSHA256" 
            decryption="AES" />
```

This key is **identical across all Exchange installations**, allowing attackers to:
1. Forge valid ViewState tokens
2. Bypass ASP.NET request validation
3. Inject deserialization payloads

### Attack Chain

```
┌─────────────────────────────────────────────────────────────┐
│                    EXPLOITATION FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. RECON                                                   │
│     ├── Identify Exchange ECP endpoint                      │
│     ├── Extract __VIEWSTATE from initial request            │
│     └── Confirm hardcoded MachineKey presence               │
│                                                             │
│  2. FORGERY                                                 │
│     ├── Decrypt original ViewState                          │
│     ├── Inject malicious object graph                       │
│     ├── Re-encrypt with known DecryptionKey                 │
│     └── Sign with known ValidationKey (HMAC-SHA256)         │
│                                                             │
│  3. EXECUTION                                               │
│     ├── POST forged ViewState to ECP page                   │
│     ├── ASP.NET deserializes the payload                    │
│     └── ObjectDataProvider triggers command execution       │
│                                                             │
│  4. PERSISTENCE                                             │
│     ├── Deploy backdoor                                     │
│     ├── Harvest credentials                                 │
│     └── Establish C2 channel                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### ViewState Structure

```
ASP.NET ViewState Format:
┌─────────────────────────────────────────┐
│  Mode Byte (0x01)                       │
│  IV (16 bytes)                          │
│  Encrypted Data (AES-CBC)               │
│  HMAC Signature (SHA256, 32 bytes)      │
└─────────────────────────────────────────┘
```

## 🛡️ Remediation

### Immediate Actions
1. **Apply May 2020 Security Update** (MS20-0555)
2. **Generate dynamic MachineKey** in web.config
3. **Move ECP behind WAF** with input validation

### Dynamic MachineKey Configuration
```xml
<system.web>
  <machineKey validationKey="AutoGenerate,IsolateApps" 
              decryptionKey="AutoGenerate,IsolateApps" 
              validation="HMACSHA256" 
              decryption="AES" />
</system.web>
```

### Detection Signatures
```
# Sigma Rule - Exchange ViewState Anomaly
title: Exchange ECP ViewState Tampering
status: experimental
description: Detect forged ViewState in Exchange ECP
logsource:
    category: application
    product: exchange
detection:
    selection:
        EventID: 1500  # ASP.NET runtime error
        Message: '*__VIEWSTATE*'
    condition: selection
level: high
```

## 🔗 References

- **CVE Details**: https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-0688
- **Microsoft Advisory**: https://msrc.microsoft.com/update-guide/vulnerability/CVE-2020-0688
- **MITRE ATT&CK**: T1190 (Exploit Public-Facing Application)
- **CISA KEV**: https://www.cisa.gov/known-exploited-vulnerabilities-catalog

## ⚠️ Legal Disclaimer

This tool is for **authorized security testing only**. Unauthorized use against systems you don't own or have permission to test is illegal. The author is not responsible for any misuse.

## 📜 License

MIT License - See LICENSE file for details.

---

**Made by Gucci** | ratman4080 | 2024
