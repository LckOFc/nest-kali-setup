#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Recreator — Recria interfaces a partir de imagens
Usa o Image Thinking System para análise e recriação
"""

import sys
import json
import os
import re
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class UIRecreator:
    """Recria UI a partir de imagens usando thinking system"""
    
    # Templates de componentes
    TEMPLATES = {
        'button': '''<button class="{class_name}" {attributes}>
    {text}
</button>''',
        
        'input': '''<div class="input-group">
    <label class="input-label" for="{id}">{label}</label>
    <input 
        type="{type}" 
        id="{id}" 
        class="input-field"
        {attributes}
    />
    {error_message}
</div>''',
        
        'card': '''<div class="card {class_name}" {attributes}>
    <div class="card-header">
        <h3 class="card-title">{title}</h3>
        {subtitle}
    </div>
    <div class="card-body">
        {content}
    </div>
    {footer}
</div>''',
        
        'modal': '''<div class="modal {class_name}" {attributes}>
    <div class="modal-overlay"></div>
    <div class="modal-container">
        <div class="modal-header">
            <h2 class="modal-title">{title}</h2>
            <button class="modal-close" aria-label="Close">&times;</button>
        </div>
        <div class="modal-body">
            {content}
        </div>
        <div class="modal-footer">
            {actions}
        </div>
    </div>
</div>''',
        
        'navbar': '''<nav class="navbar {class_name}" {attributes}>
    <div class="navbar-brand">
        {logo}
    </div>
    <button class="navbar-toggle" aria-label="Toggle navigation">
        <span></span>
        <span></span>
        <span></span>
    </button>
    <div class="navbar-menu">
        <ul class="navbar-nav">
            {links}
        </ul>
    </div>
</nav>''',
        
        'form': '''<form class="form {class_name}" {attributes}>
    <fieldset class="form-fieldset">
        <legend class="form-legend">{title}</legend>
        {fields}
    </fieldset>
    <div class="form-actions">
        {actions}
    </div>
</form>''',
        
        'table': '''<div class="table-container {class_name}" {attributes}>
    <table class="table">
        <thead>
            <tr>
                {headers}
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    {pagination}
</div>''',
        
        'sidebar': '''<aside class="sidebar {class_name}" {attributes}>
    <div class="sidebar-header">
        {logo}
    </div>
    <nav class="sidebar-nav">
        <ul class="sidebar-menu">
            {items}
        </ul>
    </nav>
    <div class="sidebar-footer">
        {footer}
    </div>
</aside>''',
    }
    
    # Paletas de cores por estilo
    COLOR_PALETTES = {
        'minimalist': ['#FFFFFF', '#F5F5F5', '#E0E0E0', '#9E9E9E', '#424242', '#212121'],
        'material': ['#FFFFFF', '#F5F5F5', '#E3F2FD', '#2196F3', '#1976D2', '#0D47A1'],
        'flat': ['#FFFFFF', '#ECF0F1', '#BDC3C7', '#3498DB', '#2980B9', '#2C3E50'],
        'dark': ['#121212', '#1E1E1E', '#2D2D2D', '#3D3D3D', '#FFFFFF', '#BB86FC'],
        'glass': ['rgba(255,255,255,0.1)', 'rgba(255,255,255,0.2)', '#FFFFFF', '#000000'],
    }
    
    def __init__(self, output_dir: str = './output'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.thinking_system = None
        self.analysis_cache = {}
    
    def analyze_and_recreate(self, image_path: str, options: Dict = None) -> Dict:
        """Análise completa e recriação"""
        options = options or {}
        
        print(f"\n{'='*60}")
        print(f"  UI RECREATOR — Analyzing {image_path}")
        print(f"{'='*60}")
        
        # Carregar thinking system
        self._load_thinking_system()
        
        # Phase 1: Análise da imagem
        print("\n[PHASE 1] Analyzing image structure...")
        analysis = self._analyze_image(image_path)
        
        # Phase 2: Extração de componentes
        print("\n[PHASE 2] Extracting components...")
        components = self._extract_components(analysis)
        
        # Phase 3: Geração do código
        print("\n[PHASE 3] Generating code...")
        generated = self._generate_code(components, options)
        
        # Phase 4: Salvamento
        print("\n[PHASE 4] Saving files...")
        saved = self._save_output(generated, options)
        
        return {
            'success': True,
            'image': image_path,
            'analysis': analysis,
            'components': components,
            'generated': generated,
            'saved': saved,
            'timestamp': datetime.now().isoformat(),
        }
    
    def _load_thinking_system(self):
        """Carrega o Image Thinking System"""
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from image_thinking_system import ImageThinker
            self.thinking_system = ImageThinker(verbose=False)
        except ImportError:
            print("  [WARN] ImageThinker not found, using basic analysis")
            self.thinking_system = None
    
    def _analyze_image(self, image_path: str) -> Dict:
        """Analisa a imagem usando o thinking system"""
        analysis = {
            'path': image_path,
            'dimensions': {'width': 1920, 'height': 1080},
            'colors': ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
            'layout': 'grid',
            'complexity': 'moderate',
            'platform': 'responsive',
            'components': [],
            'style': 'modern',
        }
        
        # Tentar usar o thinking system
        if self.thinking_system:
            try:
                result = self.thinking_system.think(image_path, {'format': 'html'})
                if hasattr(result, 'stages'):
                    if 'analysis' in result.stages:
                        analysis_data = result.stages['analysis'].data
                        analysis['dimensions'] = analysis_data.get('dimensions', analysis['dimensions'])
                        analysis['colors'] = analysis_data.get('dominantColors', analysis['colors'])
                        analysis['complexity'] = analysis_data.get('complexity', analysis['complexity'])
                        analysis['layout'] = analysis_data.get('layoutType', analysis['layout'])
                    
                    if 'understanding' in result.stages:
                        understanding = result.stages['understanding'].data
                        analysis['platform'] = understanding.get('intendedPlatform', analysis['platform'])
                        analysis['style'] = understanding.get('designSystem', analysis['style'])
                        analysis['components'] = understanding.get('interactiveElements', [])
                        
            except Exception as e:
                print(f"  [WARN] Thinking system error: {e}")
        
        # Análise básica se não tiver thinking system
        analysis = self._basic_analysis(image_path, analysis)
        
        return analysis
    
    def _basic_analysis(self, image_path: str, base: Dict) -> Dict:
        """Análise básica da imagem"""
        try:
            from PIL import Image
            img = Image.open(image_path)
            base['dimensions'] = {'width': img.width, 'height': img.height}
            
            # Extrair cores dominantes
            img_small = img.resize((100, 100))
            colors = img_small.quantize(colors=8).getcolors(10000)
            if colors:
                base['colors'] = [c[1] for c in sorted(colors, key=lambda x: -x[0])[:6]]
                
        except ImportError:
            # Fallback se PIL não estiver disponível
            pass
        except Exception as e:
            print(f"  [WARN] Basic analysis error: {e}")
        
        return base
    
    def _extract_components(self, analysis: Dict) -> List[Dict]:
        """Extrai componentes da análise"""
        components = []
        
        # Estimar componentes baseado na complexidade
        complexity = analysis.get('complexity', 'moderate')
        component_counts = {
            'minimal': {'buttons': 1, 'inputs': 0, 'cards': 1, 'images': 2},
            'simple': {'buttons': 2, 'inputs': 1, 'cards': 2, 'images': 3},
            'moderate': {'buttons': 3, 'inputs': 2, 'cards': 4, 'images': 5},
            'complex': {'buttons': 5, 'inputs': 4, 'cards': 6, 'images': 8},
        }
        
        counts = component_counts.get(complexity, component_counts['moderate'])
        
        # Adicionar componentes comuns
        if analysis.get('layout') in ['navbar', 'dashboard']:
            components.append({'type': 'navbar', 'count': 1, 'position': 'top'})
        
        components.append({'type': 'header', 'count': 1, 'position': 'top'})
        components.append({'type': 'content', 'count': 1, 'position': 'center'})
        components.append({'type': 'footer', 'count': 1, 'position': 'bottom'})
        
        # Adicionar elementos interativos
        for i in range(counts.get('buttons', 0)):
            components.append({'type': 'button', 'count': 1, 'label': f'Button {i+1}'})
        
        for i in range(counts.get('inputs', 0)):
            components.append({'type': 'input', 'count': 1, 'label': f'Input {i+1}'})
        
        for i in range(counts.get('cards', 0)):
            components.append({'type': 'card', 'count': 1, 'title': f'Card {i+1}'})
        
        for i in range(counts.get('images', 0)):
            components.append({'type': 'image', 'count': 1, 'alt': f'Image {i+1}'})
        
        return components
    
    def _generate_code(self, components: List[Dict], options: Dict) -> Dict:
        """Gera o código baseado nos componentes"""
        format_type = options.get('format', 'html')
        framework = options.get('framework', 'vanilla')
        
        generated = {
            'format': format_type,
            'framework': framework,
            'files': [],
            'code': '',
        }
        
        # Gerar HTML base
        html = self._generate_html_structure(components, options)
        
        # Adicionar CSS
        css = self._generate_css(options)
        
        # Adicionar JS (se necessário)
        js = self._generate_js(components, options)
        
        generated['code'] = html + '\n' + css + '\n' + js
        generated['files'] = [
            {'name': 'index.html', 'content': html, 'type': 'html'},
            {'name': 'styles.css', 'content': css, 'type': 'css'},
            {'name': 'script.js', 'content': js, 'type': 'js'},
        ]
        
        # Se for Roblox/Luau
        if format_type == 'luau':
            generated['code'] = self._generate_luau(components, options)
            generated['files'] = [
                {'name': 'UI.lua', 'content': generated['code'], 'type': 'lua'},
            ]
        
        return generated
    
    def _generate_html_structure(self, components: List[Dict], options: Dict) -> str:
        """Gera estrutura HTML"""
        html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated UI</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
'''
        
        # Navbar
        navbar = next((c for c in components if c.get('type') == 'navbar'), None)
        if navbar:
            html += '''    <nav class="navbar">
        <div class="navbar-brand">Logo</div>
        <button class="navbar-toggle" aria-label="Toggle navigation">
            <span></span><span></span><span></span>
        </button>
        <div class="navbar-menu">
            <ul class="navbar-nav">
                <li><a href="#home">Home</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </div>
    </nav>
'''
        
        # Header
        html += '''    <header class="header">
        <div class="container">
            <h1 class="title">Title</h1>
            <p class="subtitle">Subtitle description</p>
        </div>
    </header>
'''
        
        # Main content
        html += '''    <main class="main">
        <div class="container">
'''
        
        # Cards
        cards = [c for c in components if c.get('type') == 'card']
        if cards:
            for card in cards:
                html += f'''            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">{card.get('title', 'Card')}</h3>
                </div>
                <div class="card-body">
                    <p>Card content goes here.</p>
                </div>
            </div>
'''
        
        # Buttons
        buttons = [c for c in components if c.get('type') == 'button']
        if buttons:
            html += '''            <div class="actions">
'''
            for btn in buttons[:3]:
                html += f'''                <button class="btn btn-primary">{btn.get('label', 'Button')}</button>
'''
            html += '''            </div>
'''
        
        # Inputs
        inputs = [c for c in components if c.get('type') == 'input']
        if inputs:
            html += '''            <form class="form">
'''
            for inp in inputs[:2]:
                html += f'''                <div class="form-group">
                    <label class="form-label">{inp.get('label', 'Label')}</label>
                    <input type="text" class="form-input" placeholder="Enter value...">
                </div>
'''
            html += '''                <button type="submit" class="btn btn-primary">Submit</button>
            </form>
'''
        
        html += '''        </div>
    </main>
'''
        
        # Footer
        html += '''    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 Generated UI. All rights reserved.</p>
        </div>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>
'''
        
        return html
    
    def _generate_css(self, options: Dict) -> str:
        """Gera CSS baseado nas opções"""
        colors = options.get('colors', ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'])
        primary = colors[0] if colors else '#3B82F6'
        
        css = f'''/* Generated Styles */
:root {{
    --primary: {primary};
    --primary-dark: {self._darken(primary, 20)};
    --secondary: {colors[1] if len(colors) > 1 else '#10B981'};
    --accent: {colors[2] if len(colors) > 2 else '#F59E0B'};
    --danger: {colors[3] if len(colors) > 3 else '#EF4444'};
    --text: #1F2937;
    --text-light: #6B7280;
    --bg: #FFFFFF;
    --bg-alt: #F3F4F6;
    --border: #E5E7EB;
    --radius: 8px;
    --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --transition: all 0.2s ease;
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: var(--text);
    background: var(--bg);
    line-height: 1.6;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 16px;
}}

/* Navbar */
.navbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
}}

.navbar-brand {{
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary);
}}

.navbar-nav {{
    display: flex;
    list-style: none;
    gap: 24px;
}}

.navbar-nav a {{
    text-decoration: none;
    color: var(--text);
    font-weight: 500;
    transition: var(--transition);
}}

.navbar-nav a:hover {{
    color: var(--primary);
}}

.navbar-toggle {{
    display: none;
    flex-direction: column;
    gap: 4px;
    background: none;
    border: none;
    cursor: pointer;
}}

.navbar-toggle span {{
    width: 24px;
    height: 2px;
    background: var(--text);
}}

/* Header */
.header {{
    padding: 60px 0;
    text-align: center;
    background: linear-gradient(135deg, var(--bg) 0%, var(--bg-alt) 100%);
}}

.title {{
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 16px;
    color: var(--text);
}}

.subtitle {{
    font-size: 1.25rem;
    color: var(--text-light);
    max-width: 600px;
    margin: 0 auto;
}}

/* Main */
.main {{
    padding: 40px 0;
}}

/* Cards */
.card {{
    background: var(--bg);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
    border: 1px solid var(--border);
    transition: var(--transition);
}}

.card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}}

.card-header {{
    padding: 20px;
    border-bottom: 1px solid var(--border);
}}

.card-title {{
    font-size: 1.25rem;
    font-weight: 600;
}}

.card-body {{
    padding: 20px;
}}

/* Buttons */
.btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 12px 24px;
    border-radius: var(--radius);
    font-weight: 600;
    text-decoration: none;
    border: none;
    cursor: pointer;
    transition: var(--transition);
    gap: 8px;
}}

.btn-primary {{
    background: var(--primary);
    color: white;
}}

.btn-primary:hover {{
    background: var(--primary-dark);
}}

/* Form */
.form {{
    max-width: 500px;
    margin: 0 auto;
}}

.form-group {{
    margin-bottom: 20px;
}}

.form-label {{
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: var(--text);
}}

.form-input {{
    width: 100%;
    padding: 12px 16px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 1rem;
    transition: var(--transition);
}}

.form-input:focus {{
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}}

/* Actions */
.actions {{
    display: flex;
    gap: 12px;
    justify-content: center;
    margin-top: 24px;
}}

/* Footer */
.footer {{
    padding: 40px 0;
    text-align: center;
    background: var(--bg-alt);
    border-top: 1px solid var(--border);
    color: var(--text-light);
}}

/* Grid */
.grid {{
    display: grid;
    gap: 24px;
}}

.grid-2 {{ grid-template-columns: repeat(2, 1fr); }}
.grid-3 {{ grid-template-columns: repeat(3, 1fr); }}
.grid-4 {{ grid-template-columns: repeat(4, 1fr); }}

/* Responsive */
@media (max-width: 768px) {{
    .navbar-menu {{ display: none; }}
    .navbar-toggle {{ display: flex; }}
    .title {{ font-size: 2rem; }}
    .grid-2, .grid-3, .grid-4 {{ grid-template-columns: 1fr; }}
}}

/* Utilities */
.text-center {{ text-align: center; }}
.mt-4 {{ margin-top: 1rem; }}
.mb-4 {{ margin-bottom: 1rem; }}
.p-4 {{ padding: 1rem; }}
'''
        
        return css
    
    def _generate_js(self, components: List[Dict], options: Dict) -> str:
        """Gera JavaScript"""
        js = '''// Generated JavaScript
'use strict';

document.addEventListener('DOMContentLoaded', function() {{
    // Mobile navigation toggle
    const toggle = document.querySelector('.navbar-toggle');
    const menu = document.querySelector('.navbar-menu');
    
    if (toggle && menu) {{
        toggle.addEventListener('click', function() {{
            menu.classList.toggle('active');
            toggle.setAttribute('aria-expanded', menu.classList.contains('active'));
        }});
    }}
    
    // Form validation
    const forms = document.querySelectorAll('.form');
    forms.forEach(function(form) {{
        form.addEventListener('submit', function(e) {{
            e.preventDefault();
            // Add validation logic here
            console.log('Form submitted');
        }});
    }});
    
    // Card interactions
    const cards = document.querySelectorAll('.card');
    cards.forEach(function(card) {{
        card.addEventListener('click', function() {{
            card.classList.toggle('selected');
        }});
    }});
    
    // Smooth scroll
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {{
        anchor.addEventListener('click', function(e) {{
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {{
                target.scrollIntoView({{ behavior: 'smooth' }});
            }}
        }});
    }});
}});
'''
        
        return js
    
    def _generate_luau(self, components: List[Dict], options: Dict) -> str:
        """Gera código Luau para Roblox"""
        colors = options.get('colors', ['#3B82F6', '#10B981'])
        primary_color = colors[0] if colors else '#3B82F6'
        
        lua = f'''-- Generated UI by UIRecreator
-- Source: {options.get('source', 'image')}
-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

local ScreenGui = Instance.new("ScreenGui")
ScreenGui.ResetOnSpawn = false
ScreenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
ScreenGui.Name = "GeneratedUI"

-- Colors
local PrimaryColor = Color3.fromHex("{primary_color}")
local SecondaryColor = Color3.new(0.04, 0.71, 0.49)

-- Functions
local function createFrame(name, parent, position, size)
    local frame = Instance.new("Frame")
    frame.Name = name
    frame.Parent = parent
    frame.AnchorPoint = Vector2.new(0.5, 0.5)
    frame.Position = position
    frame.Size = size
    frame.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
    frame.BorderSizePixel = 0
    return frame
end

local function createTextLabel(parent, text, position, size, color)
    local label = Instance.new("TextLabel")
    label.Parent = parent
    label.AnchorPoint = Vector2.new(0.5, 0.5)
    label.Position = position
    label.Size = size
    label.BackgroundTransparency = 1
    label.Text = text
    label.TextColor3 = color or Color3.fromRGB(0, 0, 0)
    label.TextSize = 24
    label.Font = Enum.Font.SourceSans
    return label
end

local function createTextButton(parent, text, position, size, callback)
    local button = Instance.new("TextButton")
    button.Parent = parent
    button.AnchorPoint = Vector2.new(0.5, 0.5)
    button.Position = position
    button.Size = size
    button.BackgroundColor3 = PrimaryColor
    button.BorderSizePixel = 0
    button.Text = text
    button.TextColor3 = Color3.fromRGB(255, 255, 255)
    button.TextSize = 18
    button.Font = Enum.Font.SourceSansBold
    
    if callback then
        button.MouseButton1Click:Connect(callback)
    end
    
    return button
end

-- Main container
local mainContainer = createFrame("MainContainer", ScreenGui, 
    UDim2.new(0.5, 0, 0.5, 0), 
    UDim2.new(1, 0, 1, 0))

-- Title
createTextLabel(mainContainer, "Generated UI", 
    UDim2.new(0.5, 0, 0.1, 0), 
    UDim2.new(0.8, 0, 0.1, 0), 
    PrimaryColor)

-- Content area
local contentArea = createFrame("ContentArea", mainContainer,
    UDim2.new(0.5, 0, 0.4, 0),
    UDim2.new(0.9, 0, 0.4, 0))
contentArea.BackgroundColor3 = Color3.fromRGB(245, 245, 245)
contentArea.CornerRadius = UDim.new(0, 8)

-- Buttons
createTextButton(contentArea, "Primary Action",
    UDim2.new(0.5, -80, 0.5, 0),
    UDim2.new(0, 160, 0, 40),
    function()
        print("Primary action clicked")
    end)

createTextButton(contentArea, "Secondary Action",
    UDim2.new(0.5, 80, 0.5, 0),
    UDim2.new(0, 160, 0, 40),
    function()
        print("Secondary action clicked")
    end)

-- Output
return ScreenGui
'''
        
        return lua
    
    def _save_output(self, generated: Dict, options: Dict) -> Dict:
        """Salva os arquivos gerados"""
        output_dir = Path(options.get('output_dir', str(self.output_dir)))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        for file_info in generated.get('files', []):
            file_path = output_dir / file_info['name']
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_info['content'])
            saved_files.append(str(file_path))
        
        return {
            'directory': str(output_dir),
            'files': saved_files,
            'count': len(saved_files),
        }
    
    def _darken(self, hex_color: str, percent: int) -> str:
        """Escurece uma cor hex"""
        try:
            hex_color = hex_color.lstrip('#')
            r = max(0, int(hex_color[0:2], 16) * (100 - percent) // 100)
            g = max(0, int(hex_color[2:4], 16) * (100 - percent) // 100)
            b = max(0, int(hex_color[4:6], 16) * (100 - percent) // 100)
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return hex_color


def main():
    import argparse
    parser = argparse.ArgumentParser(description='UI Recreator — Recria UI a partir de imagens')
    parser.add_argument('image', help='Caminho da imagem de entrada')
    parser.add_argument('--output', '-o', default='./output', help='Diretório de saída')
    parser.add_argument('--format', '-f', choices=['html', 'luau', 'jsx'], default='html')
    parser.add_argument('--framework', choices=['vanilla', 'react', 'roblox'], default='vanilla')
    parser.add_argument('--colors', '-c', nargs='+', help='Cores personalizadas')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    creator = UIRecreator(output_dir=args.output)
    options = {
        'format': args.format,
        'framework': args.framework,
        'output_dir': args.output,
        'colors': args.colors,
        'source': args.image,
    }
    
    result = creator.analyze_and_recreate(args.image, options)
    
    print(f"\n{'='*60}")
    print(f"  RESULT")
    print(f"{'='*60}")
    print(f"  Success: {result['success']}")
    print(f"  Output: {result['saved']['directory']}")
    print(f"  Files: {result['saved']['count']}")
    print(f"  Components: {len(result['components'])}")
    
    if result['saved']['files']:
        print(f"\n  Generated files:")
        for f in result['saved']['files']:
            print(f"    - {f}")


if __name__ == "__main__":
    main()
