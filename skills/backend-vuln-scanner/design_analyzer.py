#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Design Analyzer — Análise estrutural de designs e interfaces
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class DesignAnalyzer:
    """Analisador estrutural de designs"""
    
    # Componentes conhecidos
    COMPONENT_PATTERNS = {
        'button': [r'<button', r'<a\s+.*?class=".*?btn', r'<input\s+.*?type="submit"'],
        'input': [r'<input', r'<textarea', r'<select'],
        'image': [r'<img', r'<picture', r'<svg'],
        'link': [r'<a\s+href', r'<a\s+.*?class=".*?link'],
        'list': [r'<ul', r'<ol', r'<li'],
        'table': [r'<table', r'<thead', r'<tbody'],
        'form': [r'<form'],
        'nav': [r'<nav', r'<header', r'<footer'],
        'card': [r'class=".*?card', r'data-component="card"'],
        'modal': [r'class=".*?modal', r'data-component="modal"'],
        'slider': [r'<slider', r'class=".*?slider', r'class=".*?carousel'],
        'tab': [r'class=".*?tab', r'<tabs'],
        'dropdown': [r'class=".*?dropdown', r'<dropdown'],
        'accordion': [r'class=".*?accordion', r'<details'],
        'tooltip': [r'class=".*?tooltip', r'title="'],
        'badge': [r'class=".*?badge', r'class=".*?tag'],
        'alert': [r'class=".*?alert', r'class=".*?notice'],
        'skeleton': [r'class=".*?skeleton', r'class=".*?loading'],
    }
    
    # Tipografia
    TYPOGRAPHY_PATTERNS = {
        'heading': [r'<h[1-6]', r'class=".*?heading', r'class=".*?title'],
        'paragraph': [r'<p>', r'<span', r'class=".*?text', r'class=".*?content'],
        'caption': [r'class=".*?caption', r'class=".*?small', r'class=".*?muted'],
    }
    
    # Layout
    LAYOUT_PATTERNS = {
        'grid': [r'class=".*?grid', r'display:\s*grid', r'grid-template'],
        'flex': [r'class=".*?flex', r'display:\s*flex', r'flex-container'],
        'stack': [r'class=".*?stack', r'class=".*?column', r'class=".*?row'],
        'sidebar': [r'class=".*?sidebar', r'class=".*?aside', r'width:\s*250'],
        'container': [r'class=".*?container', r'max-width', r'class=".*?wrapper'],
    }
    
    # Cores
    COLOR_PATTERNS = {
        'primary': [r'--primary', r'color-primary', r'btn-primary'],
        'secondary': [r'--secondary', r'color-secondary', r'btn-secondary'],
        'success': [r'--success', r'color-success', r'btn-success'],
        'danger': [r'--danger', r'color-danger', r'btn-danger'],
        'warning': [r'--warning', r'color-warning', r'btn-warning'],
        'info': [r'--info', r'color-info', r'btn-info'],
    }
    
    def __init__(self):
        self.analyses = {}
        self.cache = {}
    
    def analyze_html(self, html_content: str, source: str = "unknown") -> Dict:
        """Analisa conteúdo HTML"""
        analysis = {
            'source': source,
            'timestamp': datetime.now().isoformat(),
            'structure': {},
            'components': {},
            'typography': {},
            'layout': {},
            'colors': {},
            'accessibility': {},
            'performance': {},
            'summary': {},
        }
        
        # Estrutura
        analysis['structure'] = self._analyze_structure(html_content)
        
        # Componentes
        analysis['components'] = self._analyze_components(html_content)
        
        # Tipografia
        analysis['typography'] = self._analyze_typography(html_content)
        
        # Layout
        analysis['layout'] = self._analyze_layout(html_content)
        
        # Cores
        analysis['colors'] = self._analyze_colors(html_content)
        
        # Acessibilidade
        analysis['accessibility'] = self._analyze_accessibility(html_content)
        
        # Performance
        analysis['performance'] = self._analyze_performance(html_content)
        
        # Resumo
        analysis['summary'] = self._generate_summary(analysis)
        
        self.analyses[source] = analysis
        return analysis
    
    def _analyze_structure(self, html: str) -> Dict:
        """Analisa estrutura HTML"""
        structure = {
            'tags': {},
            'depth': 0,
            'total_elements': 0,
            'semantic_elements': [],
        }
        
        # Contar tags
        tag_pattern = r'<(\w+)[\s/>]'
        tags = re.findall(tag_pattern, html)
        structure['tags'] = dict(__import__('collections').Counter(tags))
        
        # Elementos semânticos
        semantic_tags = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']
        structure['semantic_elements'] = [
            tag for tag in semantic_tags if tag in structure['tags']
        ]
        
        # Calcular profundidade
        structure['depth'] = html.count('<') // 2  # Estimativa
        
        # Total de elementos
        structure['total_elements'] = sum(structure['tags'].values())
        
        return structure
    
    def _analyze_components(self, html: str) -> Dict:
        """Analisa componentes presentes"""
        components = {}
        
        for comp_type, patterns in self.COMPONENT_PATTERNS.items():
            count = 0
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                count += len(matches)
            
            if count > 0:
                components[comp_type] = {
                    'count': count,
                    'patterns_matched': [p for p in patterns if re.search(p, html, re.IGNORECASE)]
                }
        
        return components
    
    def _analyze_typography(self, html: str) -> Dict:
        """Analisa tipografia"""
        typography = {
            'headings': {},
            'styles': set(),
            'font_sizes': set(),
        }
        
        # Headings
        heading_counts = {}
        for level in range(1, 7):
            count = len(re.findall(rf'<h{level}', html, re.IGNORECASE))
            if count > 0:
                heading_counts[f'h{level}'] = count
        
        typography['headings'] = heading_counts
        
        # Font styles (heurística baseada em classes)
        font_patterns = re.findall(r'font-family:\s*([^;]+)', html)
        typography['styles'] = set(font_patterns)
        
        # Font sizes
        size_patterns = re.findall(r'font-size:\s*([^;]+)', html)
        typography['font_sizes'] = set(size_patterns)
        
        return typography
    
    def _analyze_layout(self, html: str) -> Dict:
        """Analisa layout"""
        layout = {
            'types': set(),
            'breakpoints': set(),
            'responsive': False,
        }
        
        # Tipologia de layout
        for lay_type, patterns in self.LAYOUT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    layout['types'].add(lay_type)
        
        layout['types'] = list(layout['types'])
        
        # Breakpoints
        breakpoints = re.findall(r'@media\s*\(.*?max-width:\s*(\d+)px', html)
        layout['breakpoints'] = list(set(breakpoints))
        
        # Responsividade
        layout['responsive'] = len(layout['breakpoints']) > 0 or 'flex' in layout['types'] or 'grid' in layout['types']
        
        return layout
    
    def _analyze_colors(self, html: str) -> Dict:
        """Analisa esquema de cores"""
        colors = {
            'css_variables': {},
            'classes': set(),
            'hex_values': set(),
            'rgb_values': set(),
        }
        
        # CSS Variables
        var_pattern = r'--([\w-]+):\s*([^;]+)'
        vars_found = re.findall(var_pattern, html)
        colors['css_variables'] = dict(vars_found)
        
        # Classes de cor
        for color_type, patterns in self.COLOR_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                if matches:
                    colors['classes'].add(color_type)
        
        # Valores hex
        hex_values = re.findall(r'#[0-9a-fA-F]{3,8}', html)
        colors['hex_values'] = set(hex_values)
        
        # Valores RGB
        rgb_values = re.findall(r'rgb\(.*?\)', html)
        colors['rgb_values'] = set(rgb_values)
        
        colors['classes'] = list(colors['classes'])
        
        return colors
    
    def _analyze_accessibility(self, html: str) -> Dict:
        """Analisa acessibilidade"""
        a11y = {
            'score': 0,
            'checks': {},
            'issues': [],
            'recommendations': [],
        }
        
        # Alt text
        imgs = re.findall(r'<img[^>]*>', html)
        imgs_with_alt = [img for img in imgs if 'alt=' in img]
        a11y['checks']['images_have_alt'] = {
            'total': len(imgs),
            'with_alt': len(imgs_with_alt),
            'pass': len(imgs) == 0 or len(imgs_with_alt) == len(imgs)
        }
        
        # Lang attribute
        has_lang = bool(re.search(r'<html[^>]*\slang=', html, re.IGNORECASE))
        a11y['checks']['has_lang'] = {
            'pass': has_lang,
            'value': 'lang attribute present' if has_lang else 'missing lang attribute'
        }
        
        # ARIA labels
        aria_labels = re.findall(r'aria-[^=]+="[^"]+"', html)
        a11y['checks']['has_aria'] = {
            'count': len(aria_labels),
            'pass': len(aria_labels) > 0
        }
        
        # Heading hierarchy
        headings = re.findall(r'<h[1-6]', html)
        if headings:
            first_level = headings[0].lower()
            a11y['checks']['heading_hierarchy'] = {
                'first': first_level,
                'pass': first_level == '<h1>'
            }
        else:
            a11y['checks']['heading_hierarchy'] = {
                'pass': False,
                'issue': 'no headings found'
            }
        
        # Semantic elements
        semantic = re.findall(r'<(header|nav|main|article|section|aside|footer)', html, re.IGNORECASE)
        a11y['checks']['semantic_html'] = {
            'count': len(semantic),
            'pass': len(semantic) >= 2
        }
        
        # Calcula score
        passed = sum(1 for check in a11y['checks'].values() if check.get('pass', False))
        total = len(a11y['checks'])
        a11y['score'] = int((passed / total) * 100) if total > 0 else 0
        
        # Issues
        for check_name, check_data in a11y['checks'].items():
            if not check_data.get('pass', True):
                a11y['issues'].append({
                    'check': check_name,
                    'severity': 'high' if check_name in ['images_have_alt', 'has_lang'] else 'medium',
                    'detail': check_data.get('issue', '') or check_data.get('value', '')
                })
        
        # Recommendations
        if not has_lang:
            a11y['recommendations'].append('Adicionar atributo lang ao elemento html')
        if a11y['checks'].get('images_have_alt', {}).get('pass') is False:
            a11y['recommendations'].append('Adicionar alt text em todas as imagens')
        if a11y['checks'].get('has_aria', {}).get('count', 0) == 0:
            a11y['recommendations'].append('Adicionar ARIA labels para melhor acessibilidade')
        if not a11y['checks'].get('heading_hierarchy', {}).get('pass'):
            a11y['recommendations'].append('Usar H1 como primeiro heading')
        
        return a11y
    
    def _analyze_performance(self, html: str) -> Dict:
        """Analisa performance"""
        perf = {
            'checks': {},
            'issues': [],
            'score': 100,
        }
        
        # Image count
        img_count = len(re.findall(r'<img', html, re.IGNORECASE))
        perf['checks']['image_count'] = {
            'count': img_count,
            'pass': img_count <= 10,
            'suggestion': f'Reduzir para <= 10 imagens (atual: {img_count})' if img_count > 10 else ''
        }
        
        # External resources
        external_css = len(re.findall(r'<link[^>]*stylesheet', html, re.IGNORECASE))
        external_js = len(re.findall(r'<script[^>]*src=', html, re.IGNORECASE))
        perf['checks']['external_resources'] = {
            'css': external_css,
            'js': external_js,
            'total': external_css + external_js,
            'pass': (external_css + external_js) <= 5
        }
        
        # Inline styles
        inline_styles = len(re.findall(r'style="[^"]+"', html))
        perf['checks']['inline_styles'] = {
            'count': inline_styles,
            'pass': inline_styles <= 5,
            'suggestion': 'Mover estilos inline para arquivo CSS' if inline_styles > 5 else ''
        }
        
        # Calculate score
        passed = sum(1 for check in perf['checks'].values() if check.get('pass', True))
        total = len(perf['checks'])
        perf['score'] = int((passed / total) * 100) if total > 0 else 100
        
        # Issues
        for check_name, check_data in perf['checks'].items():
            if not check_data.get('pass', True) and check_data.get('suggestion'):
                perf['issues'].append({
                    'check': check_name,
                    'suggestion': check_data['suggestion']
                })
        
        return perf
    
    def _generate_summary(self, analysis: Dict) -> Dict:
        """Gera resumo da análise"""
        summary = {
            'total_elements': analysis['structure']['total_elements'],
            'component_types': len(analysis['components']),
            'layout_types': len(analysis['layout']['types']),
            'color_palette_size': len(analysis['colors']['hex_values']),
            'accessibility_score': analysis['accessibility']['score'],
            'performance_score': analysis['performance']['score'],
            'overall_score': 0,
            'issues_count': len(analysis['accessibility']['issues']) + len(analysis['performance']['issues']),
            'responsive': analysis['layout']['responsive'],
        }
        
        # Overall score (weighted)
        a11y_score = analysis['accessibility']['score']
        perf_score = analysis['performance']['score']
        summary['overall_score'] = int((a11y_score * 0.5) + (perf_score * 0.5))
        
        # Grade
        if summary['overall_score'] >= 90:
            summary['grade'] = 'A'
        elif summary['overall_score'] >= 80:
            summary['grade'] = 'B'
        elif summary['overall_score'] >= 70:
            summary['grade'] = 'C'
        elif summary['overall_score'] >= 60:
            summary['grade'] = 'D'
        else:
            summary['grade'] = 'F'
        
        return summary
    
    def compare_analyses(self, source1: str, source2: str) -> Dict:
        """Compara duas análises"""
        if source1 not in self.analyses or source2 not in self.analyses:
            return {'error': 'Source not found'}
        
        a1 = self.analyses[source1]
        a2 = self.analyses[source2]
        
        comparison = {
            'source1': source1,
            'source2': source2,
            'differences': {},
            'similarities': {},
        }
        
        # Comparar componentes
        comps1 = set(a1['components'].keys())
        comps2 = set(a2['components'].keys())
        comparison['differences']['components'] = {
            'only_in_1': list(comps1 - comps2),
            'only_in_2': list(comps2 - comps1),
            'common': list(comps1 & comps2),
        }
        
        # Comparar scores
        comparison['differences']['scores'] = {
            'accessibility': {
                'source1': a1['accessibility']['score'],
                'source2': a2['accessibility']['score'],
                'diff': a2['accessibility']['score'] - a1['accessibility']['score'],
            },
            'performance': {
                'source1': a1['performance']['score'],
                'source2': a2['performance']['score'],
                'diff': a2['performance']['score'] - a1['performance']['score'],
            },
        }
        
        return comparison
    
    def get_analysis(self, source: str) -> Optional[Dict]:
        """Retorna análise salva"""
        return self.analyses.get(source)
    
    def export_report(self, source: str, output_path: str = None) -> str:
        """Exporta relatório em JSON"""
        analysis = self.analyses.get(source)
        if not analysis:
            raise ValueError(f"Analysis not found for: {source}")
        
        if not output_path:
            output_path = f"analysis_{source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
        
        return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Design Analyzer — Analisa estruturas HTML/CSS')
    parser.add_argument('input', help='Arquivo HTML ou URL')
    parser.add_argument('--source', '-s', help='Nome da fonte')
    parser.add_argument('--output', '-o', help='Arquivo de saída JSON')
    parser.add_argument('--compare', '-c', nargs=2, help='Comparar duas fontes')
    
    args = parser.parse_args()
    
    analyzer = DesignAnalyzer()
    
    # Ler arquivo
    if args.input.startswith('http'):
        import urllib.request
        with urllib.request.urlopen(args.input, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        source = args.source or 'url'
    else:
        with open(args.input, 'r', encoding='utf-8') as f:
            html = f.read()
        source = args.source or Path(args.input).stem
    
    # Analisar
    analysis = analyzer.analyze_html(html, source)
    
    # Comparar
    if args.compare:
        s1, s2 = args.compare
        if s1 in analyzer.analyses and s2 in analyzer.analyses:
            comparison = analyzer.compare_analyses(s1, s2)
            print(json.dumps(comparison, indent=2, default=str))
        else:
            print(f"Error: sources {s1} and/or {s2} not found")
    
    # Output
    if args.output:
        path = analyzer.export_report(source, args.output)
        print(f"Report saved to: {path}")
    else:
        print(json.dumps(analysis, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
