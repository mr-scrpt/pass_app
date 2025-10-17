#!/usr/bin/env python3
"""Analyze project dependencies to find used and unused files."""

import os
import re
from pathlib import Path

# Start from the main file
MAIN_FILE = "pass_client.py"
PROJECT_ROOT = Path(__file__).parent

# Track all used files
used_files = set()
to_analyze = [MAIN_FILE]

def extract_imports(filepath):
    """Extract all local imports from a Python file."""
    imports = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Match: from module import ...
        # Match: import module
        patterns = [
            r'from\s+([\w.]+)\s+import',
            r'import\s+([\w.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return imports

def resolve_import_to_file(import_name):
    """Convert import name to file path."""
    # Remove 'components.' prefix if present
    parts = import_name.split('.')
    
    # Try as module (directory with __init__.py)
    potential_paths = [
        f"{'/'.join(parts)}.py",
        f"{'/'.join(parts)}/__init__.py",
    ]
    
    for path in potential_paths:
        full_path = PROJECT_ROOT / path
        if full_path.exists():
            return path
    
    return None

# Analyze dependencies
print("🔍 Analyzing dependencies starting from", MAIN_FILE)
print()

while to_analyze:
    current = to_analyze.pop(0)
    
    if current in used_files:
        continue
    
    used_files.add(current)
    filepath = PROJECT_ROOT / current
    
    if not filepath.exists():
        continue
    
    print(f"  ✓ {current}")
    
    imports = extract_imports(filepath)
    
    for imp in imports:
        # Skip standard library and third-party imports
        if imp.startswith(('PySide6', 'Qt', 'qt_material', 'sys', 'os', 're', 
                          'subprocess', 'json', 'string', 'secrets', 'random',
                          'collections', 'typing', 'pathlib')):
            continue
        
        resolved = resolve_import_to_file(imp)
        if resolved and resolved not in used_files:
            to_analyze.append(resolved)

print()
print("📊 Summary:")
print(f"  Used Python files: {len(used_files)}")
print()

# Find all Python files
all_py_files = set()
for py_file in PROJECT_ROOT.rglob("*.py"):
    if '.venv' in str(py_file) or '__pycache__' in str(py_file) or 'build' in str(py_file):
        continue
    rel_path = py_file.relative_to(PROJECT_ROOT)
    all_py_files.add(str(rel_path))

# Find unused files
unused_files = all_py_files - used_files

print("🗑️  Potentially unused Python files:")
for f in sorted(unused_files):
    print(f"  • {f}")

print()
print("📝 Used files:")
for f in sorted(used_files):
    print(f"  ✓ {f}")
