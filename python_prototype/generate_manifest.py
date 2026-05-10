"""
Cardflow Integrity Manifest Generator
======================================
Run this script BEFORE building the EXE to generate a manifest
of SHA-256 hashes for all critical game files.

Usage:
    python.exe -m python_prototype.generate_manifest
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from python_prototype.ui.security import (
    CRITICAL_FILES,
    generate_integrity_manifest,
    save_integrity_manifest
)


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    manifest_path = os.path.join(base_dir, "integrity.manifest")
    
    print("=" * 50)
    print("  Cardflow Integrity Manifest Generator")
    print("=" * 50)
    print()
    
    # Generate hashes for all critical files
    print("Scanning critical files...")
    manifest = generate_integrity_manifest(base_dir, CRITICAL_FILES)
    
    if not manifest:
        print("[ERROR] No critical files found! Check your paths.")
        sys.exit(1)
    
    # Display results
    for rel_path, file_hash in manifest.items():
        status = "OK" if file_hash else "MISSING"
        print(f"  [{status}] {rel_path}")
        if file_hash:
            print(f"         SHA-256: {file_hash[:16]}...")
    
    print()
    
    # Save manifest
    if save_integrity_manifest(manifest, manifest_path):
        print(f"Manifest saved to: {manifest_path}")
        print(f"Total files protected: {len(manifest)}")
    else:
        print("[ERROR] Failed to save manifest!")
        sys.exit(1)
    
    print()
    print("Done! Now build your EXE with:")
    print("  pyinstaller --clean --noconfirm Cardflow.spec")


if __name__ == "__main__":
    main()
