"""AutoInstall CLI entry point"""
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import get_engine, KNOWN_PACKAGES

def main():
    args = sys.argv[1:]
    
    if not args:
        print("""
AutoInstall v1 - Instalacao por linguagem natural
Uso:
  python autoinstall.py "instala flask"
  python autoinstall.py "instala vite e eslint"
  python autoinstall.py "instala node" --suggest
  python autoinstall.py --search flask
  python autoinstall.py --list
  python autoinstall.py --list pip
  python autoinstall.py --history
  python autoinstall.py --stats
  python autoinstall.py --info
  python autoinstall.py "desinstala npm" --uninstall
  python autoinstall.py "instala vscode" --dry-run
""")
        return
    
    dry_run = '--dry-run' in args or '-n' in args
    uninstall = '--uninstall' in args or '-u' in args
    history = '--history' in args or '-H' in args
    stats = '--stats' in args or '-s' in args
    info = '--info' in args or '-i' in args
    suggest = '--suggest' in args or '-S' in args
    search_flag = '--search' in args or '-se' in args
    list_flag = '--list' in args or '-l' in args
    force_manager = '--force-manager' in args
    
    # Remove flags from args
    non_flag_args = [a for a in args if not a.startswith('--') and a not in ('-n', '-u', '-H', '-s', '-i', '-S', '-se', '-l')]
    
    engine = get_engine(dry_run=dry_run)
    
    if history:
        h = engine.get_history()
        print(f"\n{'='*60}")
        print(f"  History ({len(h)} entries)")
        print(f"{'='*60}\n")
        for entry in h:
            from datetime import datetime
            ts = datetime.fromtimestamp(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            icon = '[OK]' if entry['status'] == 'success' else '[FAIL]'
            pkgs = entry.get('packages', [])
            if isinstance(pkgs, str):
                try:
                    import json
                    pkgs = json.loads(pkgs)
                except:
                    pkgs = [pkgs]
            print(f"  {ts}  {icon}  {', '.join(pkgs)}  [{entry['manager']}]  {entry['duration_ms']:.0f}ms")
        return
    
    if stats:
        s = engine.get_stats()
        print(f"\n{'='*60}")
        print(f"  Statistics")
        print(f"{'='*60}\n")
        print(f"  Total: {s['total_installs']}")
        print(f"  Success: {s['successful']}")
        print(f"  Failed: {s['failed']}")
        print(f"  Rollback: {s['rolled_back']}")
        print(f"  Success rate: {s['success_rate']}")
        print(f"  Avg duration: {s['avg_duration_ms']:.0f}ms")
        return
    
    if info:
        i = engine.info()
        print(f"\n{'='*60}")
        print(f"  System Info")
        print(f"{'='*60}\n")
        print(f"  OS: {i['os']['os']} {i['os']['machine']}")
        print(f"  Python: {i['os']['python_version']}")
        print(f"  Known packages: {i['known_packages_count']}")
        print(f"\n  Package Managers:")
        for pm, avail in i['package_managers'].items():
            icon = '[OK]' if avail else '[X]'
            print(f"    {icon} {pm}")
        return
    
    if search_flag:
        query = ' '.join(non_flag_args) if non_flag_args else ''
        if not query:
            print("Usage: python autoinstall.py --search <query>")
            return
        results = engine.search(query)
        print(f"\n{'='*60}")
        print(f"  Search: '{query}' ({len(results)} found)")
        print(f"{'='*60}\n")
        for r in results:
            print(f"  {r['alias']:25s} -> {r['package_name']:40s} [{r['manager']}]")
        return
    
    if list_flag:
        mgr_filter = non_flag_args[0] if non_flag_args else None
        results = engine.list_all(manager=mgr_filter)
        print(f"\n{'='*60}")
        print(f"  All packages ({len(results)})")
        print(f"{'='*60}\n")
        for r in results:
            print(f"  {r['alias']:25s} -> {r['package_name']:40s} [{r['manager']}]")
        return
    
    if suggest and non_flag_args:
        text = ' '.join(non_flag_args)
        result = engine.suggest(text)
        print(f"\n[SUGGEST] For: '{text}'\n")
        print(f"  Action: {result['plan']['action']}")
        print(f"  Manager: {result['plan']['manager']}")
        print(f"  Packages: {', '.join(result['plan']['packages'])}")
        print(f"\n  Command: {result['command']}")
        return
    
    if non_flag_args:
        text = ' '.join(non_flag_args)
        force_mgr = None
        if force_manager and len(sys.argv) > args.index('--force-manager') + 1:
            idx = args.index('--force-manager')
            force_mgr = sys.argv[idx + 1]
        
        result = engine.execute(text, force_manager=force_mgr)
        print(f"\n{'='*60}")
        print(f"  {'Uninstall' if uninstall else 'Install'} Complete")
        print(f"{'='*60}\n")
        print(f"  Request: {text}")
        print(f"  Dry run: {result.get('summary', {}).get('dry_run', False)}")
        print(f"\n  Results:")
        for r in result.get('results', []):
            icon = '[OK]' if r['status'] == 'success' else '[FAIL]'
            print(f"    {icon} {r['name']} ({r['manager']}) - {r['duration_ms']:.0f}ms")
            if r.get('error'):
                print(f"       Error: {r['error'][:100]}")
        print()
        if result.get('summary', {}).get('message'):
            print(f"  {result['summary']['message']}")
        sys.exit(0 if result.get('success', False) else 1)
    else:
        print("No request specified. Use --help for usage.")


if __name__ == '__main__':
    main()
