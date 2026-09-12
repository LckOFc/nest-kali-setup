/**
 * FigmaPS2Roblox — CEP Panel JavaScript v2.2.0 (Simplified)
 */

// ── CEP Bridge ───────────────────────────────────────────────
(function() {
  if (typeof CSInterface !== 'undefined') return;
  window.CSInterface = function() {
    this.hostEnvironment = { appVersion: "25.0", hostName: "PHXS", hostVersion: "25.0" };
  };
  CSInterface.prototype.evalScript = function(script, callback) {
    if (typeof $.evalFile !== 'undefined') {
      try { var r = eval(script); if (callback) callback(r || ''); }
      catch(e) { if (callback) callback('ERROR: ' + e.message); }
      return;
    }
    if (window.__cepBridge) { window.__cepBridge.evalScript(script, callback); return; }
    if (typeof cep !== 'undefined' && cep.representations) {
      cep.representations.executeScript(script, function(r) { if (callback) callback(r || ''); });
    } else if (callback) { callback(''); }
  };
  CSInterface.prototype.getHostEnvironment = function() { return this.hostEnvironment; };
})();

// ── App ──────────────────────────────────────────────────────
(function() {
  'use strict';
  
  const cs = new CSInterface();
  let layerData = null;
  let artboardsList = [];
  let selectedArtboard = 'all';
  let isConnected = false;
  
  // ── Init ─────────────────────────────────────────────────
  function init() {
    cs.evalScript('app.documents.length > 0 ? "ok" : "none"', function(r) {
      if (r === 'ok') refreshInfo();
      else setStatus('disconnected', 'Nenhum documento');
    });
    setInterval(() => { if (isConnected) refreshInfo(); }, 3000);
  }
  
  // ── Refresh Doc Info ─────────────────────────────────────
  function refreshInfo() {
    cs.evalScript('handleCEPCommand("getDocInfo", null)', function(result) {
      try {
        const info = JSON.parse(result);
        if (!info) { setStatus('disconnected', 'Nenhum documento'); return; }
        
        isConnected = true;
        document.getElementById('docName').textContent = info.name;
        document.getElementById('canvasSize').textContent = info.width + '×' + info.height;
        document.getElementById('layerCount').textContent = info.layers;
        document.getElementById('artboardCount').textContent = info.artboards;
        
        setStatus('connected', 'Pronto — ' + info.name);
        document.getElementById('exportBtn').disabled = false;
        
        refreshArtboards();
        refreshLayers();
      } catch(e) {
        console.error(e);
        setStatus('error', 'Erro ao ler documento');
      }
    });
  }
  
  // ── Refresh Artboards ────────────────────────────────────
  function refreshArtboards() {
    cs.evalScript('handleCEPCommand("getArtboards", null)', function(result) {
      try {
        artboardsList = JSON.parse(result);
        buildArtboardSelector();
      } catch(e) {}
    });
  }
  
  function buildArtboardSelector() {
    const container = document.getElementById('artboardSelector');
    const section = document.getElementById('artboardSection');
    
    if (artboardsList.length === 0) {
      section.style.display = 'none';
      return;
    }
    
    section.style.display = 'block';
    container.innerHTML = '<button class="artboard-btn ' + (selectedArtboard === 'all' ? 'active' : '') + '" onclick="selectArtboard(\'all\')">Todas</button>';
    
    artboardsList.forEach(ab => {
      const btn = document.createElement('button');
      btn.className = 'artboard-btn ' + (selectedArtboard == ab.id ? 'active' : '');
      btn.textContent = ab.name;
      btn.onclick = () => selectArtboard(ab.id);
      container.appendChild(btn);
    });
  }
  
  window.selectArtboard = function(id) {
    selectedArtboard = id;
    document.querySelectorAll('.artboard-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    refreshLayers();
  };
  
  // ── Refresh Layers ───────────────────────────────────────
  function refreshLayers() {
    const params = selectedArtboard === 'all' ? null : JSON.stringify({ artboardId: selectedArtboard });
    cs.evalScript('handleCEPCommand("getLayerTree", ' + (params || 'null') + ')', function(result) {
      try {
        layerData = JSON.parse(result);
        renderLayerPreview();
      } catch(e) { console.error(e); }
    });
  }
  
  function renderLayerPreview() {
    const container = document.getElementById('layerPreview');
    if (!layerData || layerData.length === 0) {
      container.innerHTML = '<div style="color: var(--muted); text-align: center; padding: 20px;">Nenhuma camada visível</div>';
      return;
    }
    
    // Flatten layers
    const layers = [];
    function flatten(arr) {
      arr.forEach(l => {
        if (l.type === 'group' || l.type === 'artboard') {
          if (l.children) flatten(l.children);
        } else {
          layers.push(l);
        }
      });
    }
    flatten(layerData);
    
    // Show first 20 layers
    const preview = layers.slice(0, 20);
    container.innerHTML = preview.map(l => `
      <div class="layer-item">
        <div class="layer-dot"></div>
        <span class="layer-name">${escHtml(l.name)}</span>
        <span class="layer-size">${l.width}×${l.height}</span>
        <span class="layer-type">${l.type || 'frame'}</span>
      </div>
    `).join('') + (layers.length > 20 ? `<div style="color: var(--muted); text-align: center; padding: 8px;">+${layers.length - 20} mais...</div>` : '');
  }
  
  // ── Export ────────────────────────────────────────────────
  window.exportToRoblox = function() {
    const screenName = document.getElementById('docName').textContent.replace(/\.[^\.]+$/, '') || 'Screen';
    const bypass = document.getElementById('optBypass').checked;
    const hash = document.getElementById('optHash').checked;
    const lua = document.getElementById('optLua').checked;
    
    // Auto-select output folder (next to PSD or Documents)
    cs.evalScript('app.activeDocument.path ? app.activeDocument.path.fsName : Folder.myDocuments.fsName', function(result) {
      const outputPath = result || Folder.myDocuments.fsName;
      
      const options = {
        bypass: bypass,
        bypassTech: 'all',
        antiReupload: hash,
        generateLuau: lua,
        artboardId: selectedArtboard === 'all' ? null : selectedArtboard
      };
      
      document.getElementById('exportBtn').disabled = true;
      document.getElementById('progress').classList.add('active');
      setProgress(10, 'Analisando...');
      
      cs.evalScript(`handleCEPCommand("export", JSON.stringify({outputPath:${JSON.stringify(outputPath)}, screenName:${JSON.stringify(screenName)}, options:${JSON.stringify(options)}}))`, function(result) {
        try {
          const data = JSON.parse(result);
          if (data.success) {
            setProgress(100, 'Concluído!');
            setTimeout(() => {
              document.getElementById('progress').classList.remove('active');
              document.getElementById('exportBtn').disabled = false;
              showToast('✅ ' + data.exported + ' assets exportados', 'success');
              
              // Open folder
              cs.evalScript('(function(){ var f = new Folder(' + JSON.stringify(data.outputFolder) + '); if(f.exists) f.execute(); })()');
            }, 1000);
          } else {
            setProgress(0, 'Erro');
            document.getElementById('exportBtn').disabled = false;
            showToast('❌ ' + (data.error || 'Erro na exportação'), 'error');
          }
        } catch(e) {
          setProgress(0, 'Erro');
          document.getElementById('exportBtn').disabled = false;
          showToast('❌ Erro: ' + e.message, 'error');
        }
      });
    });
  };
  
  function setProgress(pct, text) {
    document.getElementById('progressFill').style.width = pct + '%';
    document.getElementById('progressText').textContent = text;
  }
  
  // ── Status ────────────────────────────────────────────────
  function setStatus(state, text) {
    const dot = document.getElementById('statusDot');
    const badge = document.getElementById('badge');
    const statusText = document.getElementById('statusText');
    
    dot.className = 'status-dot' + (state === 'connected' ? '' : state === 'error' ? ' error' : ' loading');
    badge.textContent = state === 'connected' ? 'Conectado' : state === 'error' ? 'Erro' : '...';
    badge.className = 'badge' + (state === 'connected' ? ' connected' : '');
    statusText.textContent = text;
  }
  
  // ── Toast ─────────────────────────────────────────────────
  function showToast(msg, type) {
    const toast = document.createElement('div');
    toast.style.cssText = `
      position: fixed; bottom: 40px; left: 50%; transform: translateX(-50%) translateY(20px);
      background: ${type === 'success' ? 'var(--green)' : 'var(--red)'};
      color: white; padding: 10px 20px; border-radius: 6px; font-size: 12px;
      opacity: 0; transition: all 0.2s; z-index: 1000;
    `;
    toast.textContent = msg;
    document.body.appendChild(toast);
    
    setTimeout(() => { toast.style.opacity = '1'; toast.style.transform = 'translateX(-50%) translateY(0)'; }, 10);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 200); }, 3000);
  }
  
  function escHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
  
  // Start
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
