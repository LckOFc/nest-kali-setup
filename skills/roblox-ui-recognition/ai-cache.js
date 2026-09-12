/**
 * ai-cache.js
 *
 * Cache local de respostas da IA para evitar chamadas repetidas.
 * Usa filesystem como storage (portátil, sem dependências).
 *
 * Estrutura:
 *   ~/.config/figmap2roblox/cache/
 *     <hash>.json  → { input, output, timestamp, model }
 *
 * Uso:
 *   const { AICache } = require('./ai-cache');
 *   const cache = new AICache();
 *   const result = await cache.getOrCompute(key, computeFn);
 */

const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

// ── Config ──────────────────────────────────────────────────────────────────────

const CONFIG = {
    cacheDir: path.join(process.env.APPDATA || process.home, ".figmap2roblox", "cache"),
    ttlHours: 24,          // Tempo de vida do cache
    maxEntries: 100,       // Máximo de entradas
    maxSizeMB: 50,         // Tamanho máximo do diretório
};

// ── AICache Class ──────────────────────────────────────────────────────────────

class AICache {
    constructor(options = {}) {
        this.cacheDir = options.cacheDir || CONFIG.cacheDir;
        this.ttl = (options.ttlHours || CONFIG.ttlHours) * 3600 * 1000;
        this.maxEntries = options.maxEntries || CONFIG.maxEntries;
        this._ensureDir();
    }

    /**
     * Gera key única a partir do input
     */
    static makeKey(input, model = "default") {
        const data = JSON.stringify({ input, model });
        return crypto.createHash("sha256").update(data).digest("hex").substring(0, 16);
    }

    /**
     * Busca no cache ou computa
     */
    async getOrCompute(key, computeFn, model = "default") {
        // Tentar cache
        const cached = this.get(key, model);
        if (cached) {
            return { fromCache: true, data: cached };
        }

        // Computar
        const data = await computeFn();

        // Salvar
        this.set(key, data, model);

        return { fromCache: false, data };
    }

    /**
     * Busca entrada no cache
     */
    get(key, model = "default") {
        const entry = this._readEntry(key, model);
        if (!entry) return null;

        // Verificar TTL
        if (Date.now() - entry.timestamp > this.ttl) {
            this._deleteEntry(key, model);
            return null;
        }

        return entry.data;
    }

    /**
     * Salva entrada no cache
     */
    set(key, data, model = "default") {
        const entry = {
            key,
            model,
            data,
            timestamp: Date.now(),
        };

        this._writeEntry(key, model, entry);
        this._prune();
    }

    /**
     * Limpa cache manualmente
     */
    clear() {
        if (fs.existsSync(this.cacheDir)) {
            fs.rmSync(this.cacheDir, { recursive: true, force: true });
        }
        this._ensureDir();
    }

    /**
     * Remove entrada específica
     */
    remove(key, model = "default") {
        this._deleteEntry(key, model);
    }

    /**
     * Lista todas as entradas
     */
    list() {
        if (!fs.existsSync(this.cacheDir)) return [];
        return fs.readdirSync(this.cacheDir)
            .filter(f => f.endsWith(".json"))
            .map(f => {
                try {
                    return JSON.parse(fs.readFileSync(path.join(this.cacheDir, f), "utf-8"));
                } catch {
                    return null;
                }
            })
            .filter(Boolean);
    }

    /**
     * Estatísticas do cache
     */
    stats() {
        const entries = this.list();
        const totalSize = entries.reduce((sum, e) => {
            try {
                return sum + fs.statSync(path.join(this.cacheDir, e.key + "_" + e.model + ".json")).size;
            } catch {
                return sum;
            }
        }, 0);

        return {
            entries: entries.length,
            maxSize: this.maxEntries,
            ttlHours: this.ttl / 3600000,
            totalSizeKB: Math.round(totalSize / 1024),
            dir: this.cacheDir,
        };
    }

    // ── Private ──────────────────────────────────────────────────────────────

    _ensureDir() {
        fs.mkdirSync(this.cacheDir, { recursive: true });
    }

    _entryPath(key, model) {
        return path.join(this.cacheDir, `${key}_${model}.json`);
    }

    _readEntry(key, model) {
        try {
            return JSON.parse(fs.readFileSync(this._entryPath(key, model), "utf-8"));
        } catch {
            return null;
        }
    }

    _writeEntry(key, model, entry) {
        fs.writeFileSync(this._entryPath(key, model), JSON.stringify(entry, null, 2), "utf-8");
    }

    _deleteEntry(key, model) {
        try {
            fs.unlinkSync(this._entryPath(key, model));
        } catch {}
    }

    _prune() {
        const entries = this.list();
        if (entries.length <= this.maxEntries) return;

        // Ordenar por timestamp (mais antigo primeiro)
        entries.sort((a, b) => a.timestamp - b.timestamp);

        // Manter apenas maxEntries mais recentes
        const toDelete = entries.slice(0, entries.length - this.maxEntries);
        for (const entry of toDelete) {
            this._deleteEntry(entry.key, entry.model);
        }
    }
}

// ── Export ──────────────────────────────────────────────────────────────────────

module.exports = { AICache };
