{
  "name": "shadow-toolkit",
  "version": "36.1.0",
  "description": "Shadow v36.1 — Full Recon + Exploit Engine (patched)",
  "skills": [
    {
      "id": "shadow_recon",
      "name": "Shadow Recon",
      "description": "Cloudflare bypass and endpoint enumeration",
      "commands": [
        "/toolkit shadow scan <domain>",
        "/toolkit shadow probe <endpoint>",
        "/toolkit shadow enumerate <domain>"
      ]
    },
    {
      "id": "shadow_exploit",
      "name": "Shadow Exploit",
      "description": "Automated transfer and withdrawal pipeline",
      "commands": [
        "/toolkit shadow transfer <account> <amount>",
        "/toolkit shadow withdraw <account>",
        "/toolkit shadow flow <account>"
      ]
    },
    {
      "id": "shadow_analysis",
      "name": "Shadow Analysis",
      "description": "JWT analysis and vulnerability detection",
      "commands": [
        "/toolkit shadow tokens",
        "/toolkit shadow vulns",
        "/toolkit shadow analyze <token>"
      ]
    },
    {
      "id": "shadow_export",
      "name": "Shadow Export",
      "description": "Data export and reporting",
      "commands": [
        "/toolkit shadow export",
        "/toolkit shadow report",
        "/toolkit shadow clear"
      ]
    }
  ],
  "integration": {
    "apex_compatible": true,
    "quantum_drift": true,
    "self_evolution": true
  },
  "features_v36.1": [
    "_test_endpoints: conta só status sensíveis (200/201/202/204)",
    "_sql_injection: registra erro SQL como achado independente de token",
    "_jwt_algorithm_confusion: key confusion real (HS256 + JWKS)",
    "_house_balance: distingue 401 de 0 real",
    "WebSocket: fila por conexão (sem sobrescrever websocket)",
    "main(): valida expiração do token restaurado do autosave",
    "_download_file / _probe_user_endpoints: locks corretos"
  ]
}
