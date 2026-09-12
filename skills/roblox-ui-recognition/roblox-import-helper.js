#!/usr/bin/env node
"use strict";

/**
 * roblox-import-helper.js — Helper completo para importação no Roblox Studio
 *
 * Gera instruções passo a passo e arquivos de apoio para importação manual
 *
 * Uso:
 *   node roblox-import-helper.js <output-dir> --screen <nome>
 */

const fs = require("node:fs");
const path = require("path");

function generateImportGuide(outputDir, screenName) {
	const guide = `
# 🎮 Guia de Importação para Roblox Studio
# =========================================

## Tela: ${screenName}
## Data: ${new Date().toLocaleString('pt-BR')}

---

## Passo 1: Preparar Pasta no Roblox

No Roblox Studio, no Explorer:

1. Vá em **ReplicatedStorage**
2. Clique direito → **Insert Folder**
3. Nomeie como **UIAssets** (se não existir)
4. Dentro de UIAssets, crie outra pasta chamada **${screenName}**

Estrutura final:
\`\`\`
ReplicatedStorage/
└── UIAssets/
    └── ${screenName}/
        ├── _manifest.json
        ├── _controller.lua
        ├── _upload_guide.txt
        └── *.png  ← assets serão importados aqui
\`\`\`

---

## Passo 2: Importar Assets

1. Abra a pasta de saída: **${outputDir}**
2. Selecione **todos os arquivos .png**
3. Arraste para a pasta **${screenName}** no Explorer do Roblox Studio
4. Aguarde o upload completar (barra de progresso aparece)

⏱️ Tempo estimado: 2-5 minutos por asset

---

## Passo 3: Linkar Assets ao Manifest

Após importação, execute no **Output** do Roblox Studio:

\`\`\`lua
local AssetManager = require(game.ReplicatedStorage.UIBridge.AssetManager)
local mapping = AssetManager.LinkAssets("${screenName}")
print("Assets linkados:", mapping)
\`\`\`

Ou use o plugin **AssetImporter** (View > Plugins > AssetImporter)

---

## Passo 4: Atualizar Manifest

O manifest será atualizado automaticamente com os Asset IDs.

Verifique em:
**ReplicatedStorage > UIAssets > ${screenName} > _manifest.json**

---

## Passo 5: Testar a UI

Execute no **Output**:

\`\`\`lua
local GeneratedUI = require(game.ReplicatedStorage.UIAssets.${screenName}._controller)
local ui = GeneratedUI.new()
ui:Build()
\`\`\`

---

## Assets para Importar

\`\`\`
`;

	// Listar assets
	const files = fs.readdirSync(outputDir).filter(f => f.endsWith(".png"));
	for (const file of files) {
		const stats = fs.statSync(path.join(outputDir, file));
		guide += `- ${file} (${(stats.size / 1024).toFixed(1)} KB)\n`;
	}

	guide += `
\`\`\`

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Asset não aparece | Aguarde o upload completar |
| ID incorreto | Execute LinkAssets novamente |
| UI não carrega | Verifique se _controller.lua está correto |
| Erro de permissão | Execute como admin no Roblox Studio |

---

Gerado por FigmaPS2Roblox v3.0.0
`;

	return guide;
}

function main() {
	const args = process.argv.slice(2);
	const outputDir = args[0];
	let screenName = "Screen";

	for (let i = 1; i < args.length; i++) {
		if (args[i] === "--screen" && args[i + 1]) {
			screenName = args[++i];
		}
	}

	if (!outputDir) {
		console.error("❌ Informe o diretório de saída");
		console.error("Uso: node roblox-import-helper.js <output-dir> --screen <nome>");
		process.exit(1);
	}

	const guideContent = generateImportGuide(outputDir, screenName);
	const guidePath = path.join(outputDir, `_${screenName}_import_guide.txt`);

	fs.writeFileSync(guidePath, guideContent, "utf-8");

	console.log(`✅ Guia gerado: ${guidePath}`);
	console.log(`\nAbra o arquivo para ver as instruções completas.`);
}

main();
