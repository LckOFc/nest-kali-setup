"""
fuzzy_hash.py
SSdeep/spamsum-style fuzzy hashing for malware variant detection
"""
import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class FuzzyResult:
    file_a: str
    file_b: str
    hash_a: str
    hash_b: str
    similarity: float
    verdict: str

class FuzzyHashEngine:
    """
    Implementacao de hashing fuzzy baseado em SSdeep.
    
    Algoritmo:
    1. Divide o arquivo em blocos de tamanho variavel
    2. Calcula hash rolling para cada bloco
    3. Combina com hash de contexto (regioes unicas)
    4. Produz hash comparavel para arquivos similares
    """
    
    # Tamanhos de bloco possiveis
    BLOCK_SIZES = [1, 3, 64, 1024]
    
    def __init__(self, block_size: int = 3):
        self.block_size = block_size
    
    def compute(self, file_path: str) -> str:
        """Calcula hash fuzzy de um arquivo."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        data = path.read_bytes()
        
        # Escolhe tamanho de bloco baseado no tamanho do arquivo
        bs = self._select_block_size(len(data))
        
        # Rolling hash dos blocos
        rolling_hashes = self._rolling_hash(data, bs)
        
        # Context hash (fingerprint das regioes unicas)
        context_hash = self._context_hash(data)
        
        # Hash global
        global_hash = self._global_hash(data)
        
        return f"{bs}:{rolling_hashes}:{context_hash}:{global_hash}"
    
    def _select_block_size(self, file_size: int) -> int:
        """Seleciona tamanho de bloco otimico baseado no tamanho do arquivo."""
        if file_size < 1024:
            return 3
        elif file_size < 65536:
            return 3
        elif file_size < 1048576:
            return 64
        else:
            return 1024
    
    def _rolling_hash(self, data: bytes, block_size: int) -> str:
        """Calcula rolling hash em blocos."""
        if len(data) < block_size:
            block_size = max(1, len(data) // 4)
        
        hashes = []
        for i in range(0, len(data) - block_size + 1, block_size):
            chunk = data[i:i+block_size]
            # Hash do bloco
            h = hashlib.md5(chunk).hexdigest()[:8]
            hashes.append(h)
        
        # Combina hashes dos blocos
        combined = hashlib.md5(''.join(hashes).encode()).hexdigest()[:16]
        return combined
    
    def _context_hash(self, data: bytes) -> str:
        """Hash de contexto baseado em regioes unicas do arquivo."""
        # Usa as primeiras e ultimas partes do arquivo como contexto
        sample_size = min(4096, len(data))
        header = data[:sample_size//2]
        footer = data[-sample_size//2:] if len(data) > sample_size else b''
        
        context = header + footer
        return hashlib.sha256(context).hexdigest()[:12]
    
    def _global_hash(self, data: bytes) -> str:
        """Hash global do arquivo completo."""
        return hashlib.sha256(data).hexdigest()[:16]
    
    def compare(self, hash_a: str, hash_b: str) -> FuzzyResult:
        """
        Compara dois hashes fuzzy e retorna similaridade.
        
        Algoritmo de scoring:
        - Divide os hashes em partes
        - Compara partes correspondentes
        - Score baseado em caracteres em comum
        """
        if not hash_a or not hash_b:
            return FuzzyResult("", "", hash_a, hash_b, 0.0, "unknown")
        
        if hash_a == hash_b:
            return FuzzyResult("", "", hash_a, hash_b, 100.0, "identical")
        
        # Divide em partes
        parts_a = hash_a.split(':')
        parts_b = hash_b.split(':')
        
        if len(parts_a) < 2 or len(parts_b) < 2:
            return FuzzyResult("", "", hash_a, hash_b, 0.0, "unknown")
        
        # Score por correspondencia de partes
        total_score = 0
        max_score = 0
        
        # Compara rolling hashes (segunda parte)
        if len(parts_a) > 1 and len(parts_b) > 1:
            rolling_a = parts_a[1]
            rolling_b = parts_b[1]
            roll_score = self._string_similarity(rolling_a, rolling_b)
            total_score += roll_score * 0.5
            max_score += 0.5
        
        # Compara context hashes (terceira parte)
        if len(parts_a) > 2 and len(parts_b) > 2:
            ctx_a = parts_a[2]
            ctx_b = parts_b[2]
            ctx_score = self._string_similarity(ctx_a, ctx_b)
            total_score += ctx_score * 0.3
            max_score += 0.3
        
        # Compara global hashes (quarta parte)
        if len(parts_a) > 3 and len(parts_b) > 3:
            glob_a = parts_a[3]
            glob_b = parts_b[3]
            glob_score = self._string_similarity(glob_a, glob_b)
            total_score += glob_score * 0.2
            max_score += 0.2
        
        # Normaliza para 0-100
        similarity = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Verdict
        verdict = self._get_verdict(similarity)
        
        return FuzzyResult("", "", hash_a, hash_b, round(similarity, 2), verdict)
    
    def _string_similarity(self, a: str, b: str) -> float:
        """Calcula similaridade entre duas strings (Jaccard-like)."""
        if not a or not b:
            return 0.0
        
        # Sets de caracteres
        set_a = set(a)
        set_b = set(b)
        
        # Intersecao
        intersection = len(set_a & set_b)
        
        # Uniao
        union = len(set_a | set_b)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def batch_compare(self, file_paths: list[str], threshold: float = 60.0) -> list[FuzzyResult]:
        """Compara todos os arquivos em lote, retornando pares similares."""
        # Computa hashes
        hashes = {}
        for path in file_paths:
            try:
                hashes[path] = self.compute(path)
            except Exception as e:
                print(f"Erro ao processar {path}: {e}")
        
        # Compara pares
        results = []
        paths = list(hashes.keys())
        
        for i in range(len(paths)):
            for j in range(i+1, len(paths)):
                path_a = paths[i]
                path_b = paths[j]
                
                result = self.compare(hashes[path_a], hashes[path_b])
                result.file_a = path_a
                result.file_b = path_b
                
                # Filtra por threshold
                if result.similarity >= threshold:
                    results.append(result)
        
        # Ordena por similaridade (maior primeiro)
        results.sort(key=lambda x: x.similarity, reverse=True)
        
        return results
    
    def find_similar(self, target_file: str, baseline_hashes: dict[str, str], 
                     threshold: float = 60.0) -> list[tuple[str, float]]:
        """
        Encontra arquivos similares a uma baseline.
        
        Args:
            target_file: Arquivo para comparar
            baseline_hashes: Dict {nome: hash_fuzzy}
            threshold: Similaridade minima
        
        Returns:
            Lista de (nome, similaridade) para matches acima do threshold
        """
        target_hash = self.compute(target_file)
        matches = []
        
        for name, baseline_hash in baseline_hashes.items():
            result = self.compare(target_hash, baseline_hash)
            if result.similarity >= threshold:
                matches.append((name, result.similarity))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def _get_verdict(self, similarity: float) -> str:
        """Retorna veredito baseado na similaridade."""
        if similarity >= 95:
            return "identical"
        elif similarity >= 80:
            return "near_identical"
        elif similarity >= 60:
            return "similar"
        elif similarity >= 40:
            return "somewhat_similar"
        elif similarity >= 20:
            return "slightly_similar"
        else:
            return "dissimilar"


# CLI interface
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Fuzzy Hash Engine")
    parser.add_argument("file", nargs="?", help="Arquivo para calcular hash fuzzy")
    parser.add_argument("--compare", "-c", nargs=2, metavar=("FILE_A", "FILE_B"),
                        help="Comparar dois arquivos")
    parser.add_argument("--dir", "-d", help="Diretorio para comparar todos os arquivos")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recursivo em diretorio")
    parser.add_argument("--threshold", "-t", type=float, default=60.0,
                        help="Threshold de similaridade (default: 60)")
    parser.add_argument("--format", "-f", choices=["json", "text"], default="text",
                        help="Formato de saida")
    parser.add_argument("--output", "-o", help="Salvar resultado em arquivo")
    args = parser.parse_args()
    
    engine = FuzzyHashEngine()
    
    def output_text(results):
        for r in results:
            print(f"{r.similarity:6.2f}%  {r.verdict:15s}  {r.file_a}")
            print(f"{'':6s}  {'':15s}  {r.file_b}")
            print()
    
    def output_json(results):
        data = [
            {
                "file_a": r.file_a,
                "file_b": r.file_b,
                "similarity": r.similarity,
                "verdict": r.verdict
            }
            for r in results
        ]
        print(json.dumps(data, indent=2))
    
    async def main():
        if args.file and not args.compare and not args.dir:
            # Apenas hash de um arquivo
            result = engine.compute(args.file)
            print(f"File: {args.file}")
            print(f"Fuzzy Hash: {result}")
            print(f"SHA256: {hashlib.sha256(Path(args.file).read_bytes()).hexdigest()}")
        
        elif args.compare:
            # Comparar dois arquivos
            hash_a = engine.compute(args.compare[0])
            hash_b = engine.compute(args.compare[1])
            result = engine.compare(hash_a, hash_b)
            result.file_a = args.compare[0]
            result.file_b = args.compare[1]
            
            print(f"Comparison: {args.compare[0]} vs {args.compare[1]}")
            print(f"Similarity: {result.similarity:.2f}%")
            print(f"Verdict: {result.verdict}")
        
        elif args.dir:
            # Comparar diretorio inteiro
            import glob
            patterns = ["*.exe", "*.dll", "*.sys", "*.bin"]
            files = []
            
            for pattern in patterns:
                if args.recursive:
                    files.extend(glob.glob(f"{args.dir}/**/{pattern}", recursive=True))
                else:
                    files.extend(glob.glob(f"{args.dir}/{pattern}"))
            
            if not files:
                print("Nenhum arquivo encontrado no diretorio.")
                return
            
            print(f"Analisando {len(files)} arquivos...")
            results = engine.batch_compare(files, threshold=args.threshold)
            
            if args.format == "json":
                output_json(results)
            else:
                output_text(results)
            
            print(f"\nTotal: {len(results)} pares similares (threshold: {args.threshold}%)")
        
        if args.output:
            # Salvar resultado
            if args.format == "json":
                Path(args.output).write_text(json.dumps(results, indent=2))
            else:
                Path(args.output).write_text(f"Results saved to {args.output}")
            print(f"Resultado salvo em: {args.output}")
    
    import asyncio
    asyncio.run(main())
