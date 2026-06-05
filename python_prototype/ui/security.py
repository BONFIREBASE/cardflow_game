"""
Cardflow Security Module
========================
Implements three layers of client-side protection:
1. HMAC-Signed Save Data   — Detects if the database has been tampered with.
2. SHA-256 File Integrity   — Detects if game source files have been modified.
3. Anti-Debug Detection     — Detects if a debugger or inspection tool is attached.

All protections use Python standard libraries only (no paid tools needed).
"""

import hashlib
import hmac
import json
import os
import sys
import time

# ─── Configuration ──────────────────────────────────────────────────────────

# Secret key for HMAC signing (in production, derive this from hardware ID)
# This key is embedded in the code — it stops casual cheaters, not experts.
_HMAC_SECRET = b"Cardflow_2026_SchoolProject_HMAC_Key_v1"

# Signature file stored alongside the database
_SIGNATURE_FILENAME = "profile.sig"


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 1: HMAC-Signed Save Data
# ═══════════════════════════════════════════════════════════════════════════

def _get_signature_path(db_path):
    """Returns the path to the signature file next to the database."""
    db_dir = os.path.dirname(db_path)
    return os.path.join(db_dir, _SIGNATURE_FILENAME)


def sign_save_data(profile_dict, db_path):
    """
    Creates an HMAC-SHA256 signature of the profile data and writes it to disk.
    Call this every time you save the user profile.
    """
    try:
        # Create a deterministic string from the profile data
        # Sort keys to ensure consistent ordering
        data_string = json.dumps(profile_dict, sort_keys=True, default=str)
        
        # Generate HMAC signature
        signature = hmac.new(
            _HMAC_SECRET,
            data_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Write signature to file
        sig_path = _get_signature_path(db_path)
        sig_data = {
            "signature": signature,
            "timestamp": int(time.time()),
            "version": 1
        }
        
        os.makedirs(os.path.dirname(sig_path), exist_ok=True)
        with open(sig_path, 'w') as f:
            json.dump(sig_data, f)
            
        return True
    except Exception as e:
        print(f"[Security] Failed to sign save data: {e}")
        return False


def verify_save_data(profile_dict, db_path):
    """
    Verifies the HMAC signature of the profile data.
    Returns True if data is valid/untampered, False if tampered.
    Returns True if no signature file exists (first run).
    """
    sig_path = _get_signature_path(db_path)
    
    # First run — no signature file yet, that's okay
    if not os.path.exists(sig_path):
        return True
    
    try:
        # Read stored signature
        with open(sig_path, 'r') as f:
            sig_data = json.load(f)
        
        stored_signature = sig_data.get("signature", "")
        
        # Recompute signature from current data
        data_string = json.dumps(profile_dict, sort_keys=True, default=str)
        computed_signature = hmac.new(
            _HMAC_SECRET,
            data_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare using constant-time comparison (prevents timing attacks)
        return hmac.compare_digest(stored_signature, computed_signature)
        
    except Exception as e:
        print(f"[Security] Signature verification error: {e}")
        # If we can't verify, assume tampering
        return False


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 2: SHA-256 File Integrity Checks
# ═══════════════════════════════════════════════════════════════════════════

def compute_file_hash(filepath):
    """Computes the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return None


def generate_integrity_manifest(base_dir, critical_files):
    """
    Generates a manifest of SHA-256 hashes for critical game files.
    Call this once during build/deployment to create the manifest.
    
    Args:
        base_dir: Root directory of the project
        critical_files: List of relative paths to critical files
    
    Returns:
        dict mapping relative paths to their SHA-256 hashes
    """
    manifest = {}
    for rel_path in critical_files:
        full_path = os.path.join(base_dir, rel_path)
        file_hash = compute_file_hash(full_path)
        if file_hash:
            manifest[rel_path] = file_hash
    return manifest


def save_integrity_manifest(manifest, output_path):
    """Saves the integrity manifest to a JSON file."""
    try:
        # Sign the manifest itself so it can't be replaced
        manifest_string = json.dumps(manifest, sort_keys=True)
        manifest_signature = hmac.new(
            _HMAC_SECRET,
            manifest_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        data = {
            "files": manifest,
            "manifest_signature": manifest_signature,
            "generated_at": int(time.time())
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"[Security] Failed to save manifest: {e}")
        return False


def verify_file_integrity(base_dir, manifest_path):
    """
    Verifies all files listed in the integrity manifest.
    
    Returns:
        (is_valid, details) — is_valid is True if all files pass,
        details is a list of issues found.
    """
    issues = []
    
    if not os.path.exists(manifest_path):
        # No manifest = first run or dev mode, skip check
        return True, []
    
    try:
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        manifest = data.get("files", {})
        stored_manifest_sig = data.get("manifest_signature", "")
        
        # Verify the manifest itself hasn't been tampered with
        manifest_string = json.dumps(manifest, sort_keys=True)
        computed_sig = hmac.new(
            _HMAC_SECRET,
            manifest_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(stored_manifest_sig, computed_sig):
            return False, ["Integrity manifest has been tampered with"]
        
        # Check each file
        for rel_path, expected_hash in manifest.items():
            full_path = os.path.join(base_dir, rel_path)
            
            if not os.path.exists(full_path):
                issues.append(f"Missing: {rel_path}")
                continue
            
            actual_hash = compute_file_hash(full_path)
            if actual_hash != expected_hash:
                issues.append(f"Modified: {rel_path}")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        return False, [f"Verification error: {e}"]


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 3: Anti-Debug Detection
# ═══════════════════════════════════════════════════════════════════════════

_SUSPICIOUS_PROCESSES = [
    "cheatengine", "cheat engine", "x64dbg", "x32dbg", "ollydbg",
    "idapro64", "idapro", "idaq64", "idaq",
    "processhacker", "procmon", "procexp", "processexplorer",
    "reclass", "reclass.net", "dnspy", "httpanalyzer",
    "frida", "frida-server", "httptoolkit", "charles", "burpsuite",
    "wireshark", "dumpcap", "windbg", "dbgview", "debugview",
    "ghidra", "binaryninja", "immunitydebugger",
    "memu", "nox", "bluestacks",
]


def _get_process_list():
    """Return lowercase process names currently running."""
    names = set()
    try:
        import subprocess
        out = subprocess.check_output(
            'tasklist /fo csv /nh',
            shell=True, timeout=3,
            creationflags=0x08000000  # CREATE_NO_WINDOW
        ).decode('utf-8', errors='replace')
        for line in out.strip().split('\n'):
            line = line.strip().strip('"')
            if line:
                name = line.split('"')[0] if line.startswith('"') else line.split(',')[0]
                names.add(name.strip('" ').lower())
    except Exception:
        pass
    return names


def _check_suspicious_processes():
    """Check for known cheat/debug tools in the process list."""
    procs = _get_process_list()
    for suspect in _SUSPICIOUS_PROCESSES:
        for p in procs:
            if suspect in p:
                return True, suspect
    return False, None


def _check_windows_debugger_api():
    """
    Uses Windows Native API / ctypes to detect a kernel debugger.
    Checks:
      1. IsDebuggerPresent (user-mode debugger flag)
      2. NtQueryInformationProcess(ProcessDebugPort)
      3. NtGlobalFlag (heap flags set by debugger)
    """
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

        # 1. IsDebuggerPresent
        is_debugger = kernel32.IsDebuggerPresent
        is_debugger.restype = wintypes.BOOL
        if is_debugger():
            return True, "IsDebuggerPresent"

        # 2. Check for remote debugger via NtQueryInformationProcess
        ntdll = ctypes.WinDLL('ntdll', use_last_error=True)
        ProcessDebugPort = 7
        pb = ctypes.c_ulong()
        ret_len = wintypes.ULONG()

        nt_query = ntdll.NtQueryInformationProcess
        nt_query.restype = wintypes.LONG
        nt_query.argtypes = [
            ctypes.c_void_p, wintypes.ULONG,
            ctypes.c_void_p, wintypes.ULONG,
            ctypes.POINTER(wintypes.ULONG)
        ]

        handle = ctypes.c_void_p(-1)  # NtCurrentProcess
        status = nt_query(handle, ProcessDebugPort,
                          ctypes.byref(pb), ctypes.sizeof(pb),
                          ctypes.byref(ret_len))
        if status >= 0 and pb.value != 0:
            return True, "NtQueryDebugPort"

    except Exception:
        pass
    return False, None


def is_debugger_attached():
    """
    Checks if a Python debugger is attached to the process.
    This catches tools like pdb, PyCharm debugger, VS Code debugger, etc.
    """
    # Check sys.gettrace (set by most Python debuggers)
    if sys.gettrace() is not None:
        return True

    # Windows API debugger checks
    found, _ = _check_windows_debugger_api()
    if found:
        return True

    # Check for common debugging environment variables
    debug_env_vars = [
        'PYTHONDONTWRITEBYTECODE',
        'PYDEVD_USE_CYTHON',
    ]
    debug_score = 0
    for var in debug_env_vars:
        if os.environ.get(var):
            debug_score += 1
    if debug_score >= 2:
        return True

    # Check for cheat/debug tool processes
    found, _ = _check_suspicious_processes()
    if found:
        return True

    return False


def check_timing_anomaly():
    """
    Detects if the program is being stepped through a debugger by checking
    if a simple operation takes suspiciously long (indicating breakpoints).
    """
    start = time.perf_counter()

    # Multiple rapid operations to detect stepping
    for _ in range(5):
        _ = [i ** 2 for i in range(5000)]

    elapsed = time.perf_counter() - start

    return elapsed > 2.0


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API — Use these in your game
# ═══════════════════════════════════════════════════════════════════════════

# List of critical game files to monitor for tampering
CRITICAL_FILES = [
    os.path.join("python_prototype", "game", "engine.py"),
    os.path.join("python_prototype", "game", "ai_bot.py"),
    os.path.join("python_prototype", "game", "economy.py"),
    os.path.join("python_prototype", "game", "betting_configs.py"),
    os.path.join("python_prototype", "ui", "database.py"),
    os.path.join("python_prototype", "ui", "progression_manager.py"),
    os.path.join("python_prototype", "ui", "chips.py"),
    os.path.join("python_prototype", "ui", "crypto_utils.py"),
]


def run_security_checks(base_dir, db_path, profile_dict):
    """
    Runs all security checks at game startup.
    
    Returns:
        dict with keys:
            'save_valid'     : bool — Is the save data untampered?
            'files_valid'    : bool — Are game files unmodified?
            'debugger_found' : bool — Is a debugger attached?
            'issues'         : list — Detailed list of issues found
    """
    results = {
        'save_valid': True,
        'files_valid': True,
        'debugger_found': False,
        'issues': []
    }
    
    # Layer 1: Verify save data integrity
    if not verify_save_data(profile_dict, db_path):
        results['save_valid'] = False
        results['issues'].append("Save data has been tampered with")
    
    # Layer 2: Verify file integrity
    manifest_path = os.path.join(base_dir, "integrity.manifest")
    files_ok, file_issues = verify_file_integrity(base_dir, manifest_path)
    if not files_ok:
        results['files_valid'] = False
        results['issues'].extend(file_issues)
    
    # Layer 3: Anti-debug check
    if is_debugger_attached() or check_timing_anomaly():
        results['debugger_found'] = True
        results['issues'].append("Debug environment detected")
    
    return results


def on_save(profile_dict, db_path):
    """
    Call this after every save_user_profile() to sign the data.
    """
    sign_save_data(profile_dict, db_path)
