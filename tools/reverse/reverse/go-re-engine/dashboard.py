"""
Web Dashboard para o Go RE Engine
Equivalente a interfaces visuais do Ghidra/Binary Ninja
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from pathlib import Path

app = Flask(__name__)

# Global analysis data
analysis_data = {}

@app.route('/')
def index():
    """Dashboard principal."""
    return render_template('dashboard.html', data=analysis_data)

@app.route('/api/overview')
def api_overview():
    """Overview dos resultados."""
    return jsonify({
        'binary': analysis_data.get('binary', 'N/A'),
        'size': analysis_data.get('size', 0),
        'strings_total': analysis_data.get('strings', {}).get('total', 0),
        'functions_total': analysis_data.get('functions', {}).get('total', 0),
        'types_total': analysis_data.get('types', {}).get('total', 0),
        'cfg_analyzed': analysis_data.get('cfg', {}).get('analyzed', 0),
    })

@app.route('/api/strings')
def api_strings():
    """Retornar strings categorizadas."""
    return jsonify(analysis_data.get('strings', {}))

@app.route('/api/functions')
def api_functions():
    """Retornar funções recuperadas."""
    return jsonify(analysis_data.get('functions', {}))

@app.route('/api/types')
def api_types():
    """Retornar tipos recuperados."""
    return jsonify(analysis_data.get('types', {}))

@app.route('/api/cfg')
def api_cfg():
    """Retornar graphs de fluxo de controle."""
    return jsonify(analysis_data.get('cfg', {}))

@app.route('/api/function/<addr>')
def api_function(addr):
    """Detalhes de uma função específica."""
    functions = analysis_data.get('functions', {}).get('sample', [])
    for func in functions:
        if func.get('addr') == addr:
            return jsonify(func)
    return jsonify({'error': 'Function not found'}), 404

def load_analysis(report_path: str):
    """Carregar dados de análise."""
    global analysis_data
    if os.path.exists(report_path):
        with open(report_path) as f:
            analysis_data = json.load(f)

if __name__ == '__main__':
    # Default report path
    report_path = r'C:\Users\devel\tools\reverse\output\analysis_report.json'
    load_analysis(report_path)
    app.run(host='0.0.0.0', port=5000, debug=True)