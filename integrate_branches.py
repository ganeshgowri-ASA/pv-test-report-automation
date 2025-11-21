#!/usr/bin/env python3
"""
Branch Integration Script for PV Test Automation
Systematically extracts and integrates code from all 60+ feature branches
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

# Branch mapping: defines which branches contribute to which modules
BRANCH_INTEGRATION_MAP = {
    # Core Foundation (01-04)
    'core': [
        'claude/01-database-models-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/02-config-system-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/03-security-core-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/04-audit-trail-01Ee5VFdXvTFxTYjX4N8bMmo',
        'origin/claude/database-models-0199a1AWKuvzDHpprQTsk69P',
        'origin/claude/config-management-system-01N7rnbhvAmDHkmr139pdxKo',
        'origin/claude/security-core-implementation-015YSAWGFAuKapYksYoBY1ib',
        'origin/claude/audit-trail-lineage-01QocYmQyhhiQxvdtdb2LtPh',
    ],

    # Data Ingestion (05-10)
    'ingestion': [
        'claude/05-validation-utils-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/06-data-excel-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/07-data-documents-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/08-data-images-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/09-data-storage-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/10-data-traceability-01Ee5VFdXvTFxTYjX4N8bMmo',
        'origin/claude/data-validation-utilities-01D8dfxwSPmiAVu5FDCShFmt',
        'origin/claude/excel-ingestion-engine-01Xx2tjtricPdRBuHdzvXZix',
        'origin/claude/word-pdf-ingestion-engine-01DtuTTm9PDdmjoo7rFCFU7j',
        'origin/claude/image-processor-engine-01MGwEnZDVAyekm6QEEYXiNo',
        'origin/claude/json-csv-ingestion-engine-01NTrCz8GUksBVWpp5j2LGYA',
        'origin/claude/visio-gantt-smartsheet-ingestion-01Hezar3E7V4LyTCGNsL7Nqc',
        'origin/claude/image-ingestion-defect-detection-01ANUaBecxwHxToSuYbXFBJd',
    ],

    # IEC Protocols (11-18)
    'protocols': [
        'claude/11-protocol-61215-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/12-protocol-61730-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/13-protocol-61853-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/14-protocol-62716-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/15-protocol-61701-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/16-protocol-62804-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/17-protocol-60904-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/18-protocol-62759-01Ee5VFdXvTFxTYjX4N8bMmo',
        'origin/claude/implement-iec-61215-protocol-01UGAktxD9UFCAxJVnxwKt17',
        'origin/claude/iec61730-safety-handler-012FwmxNBeGmLVUfczTVcVTH',
        'origin/claude/iec-61853-protocol-013EYJftGWeyiSocC8uNr2YV',
        'origin/claude/implement-iec-62716-01VohgmE8VRfV8h37fTv5imF',
        'origin/claude/iec-61701-salt-mist-01TE7drdhVZAz1LXzYMUNmw5',
        'origin/claude/iec-62804-pid-protocol-01NcVVqQaipdtg4V5dvN4dRN',
        'origin/claude/iec-60904-electrical-01B6p1mRquVAtiaMNpj41BTB',
        'origin/claude/iec-62759-transportation-testing-01Xv1ZBYVPcGsWC6rnc3AsBD',
    ],

    # Test Blocks (19-27)
    'test_blocks': [
        'claude/19-test-iv-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/20-test-el-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/21-test-vi-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/22-test-ir-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/23-test-climate-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/24-test-outdoor-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/25-test-insulation-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/26-test-wlt-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/27-test-gct-01Ee5VFdXvTFxTYjX4N8bMmo',
        'origin/claude/iv-curve-analysis-system-01VtJKRxjyda1pwdmNpUUVYg',
        'origin/claude/el-defect-detection-019sj9iMqt2pNf2nK7E1aYZR',
        'origin/claude/insulation-resistance-test-01C6kFQxSDJe8qcxMnFJTf63',
        'origin/claude/wet-leakage-test-block-017f2ycvjgv4acNbut3LewCK',
        'origin/claude/ground-continuity-test-018kf4vVgemgaws9VLddTzJY',
        'origin/claude/hot-spot-endurance-test-01QMMapgxyhuHtqtEVj6CtiH',
        'origin/claude/bypass-diode-test-01CPwGPj8FV15BvqAqS8jkAR',
        'origin/claude/mechanical-load-test-01Pm6pEM69LsHjqMjsboCqkS',
        'origin/claude/hail-impact-test-block-018pPWMqAxSBCftbUtBRdrs2',
    ],

    # Workflows (28-33)
    'workflows': [
        'claude/28-workflow-review-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/29-workflow-approval-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/30-workflow-notifications-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/31-equipment-mgmt-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/32-calibration-track-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/33-spc-uncertainty-01Ee5VFdXvTFxTYjX4N8bMmo',
        'origin/claude/review-workflow-system-01EhraVQK5Fnbrj1aUqupV7k',
        'origin/claude/approval-workflow-engine-01PGnFnnP5YWREXRLLGMsW9G',
        'origin/claude/notification-alert-system-01DSTsAuyeNnMmDF2QYEuP5P',
        'origin/claude/equipment-database-tracking-01SLmptjsBLRzzkuaBEDGwje',
        'origin/claude/calibration-certificate-management-01Ma2Th5NyCSTyjAWjoR2GWm',
        'origin/claude/add-spc-uncertainty-01CVpYihm7XrPUDNSHuGZHzv',
    ],

    # LLM Integration (34-38)
    'llm': [
        'claude/34-llm-claude-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/35-llm-gpt-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/36-llm-gemini-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/37-llm-compliance-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/38-llm-summarizer-01Ee5VFdXvTFxTYjX4N8bMmo',
        'origin/claude/llm-claude-api-integration-0174yGa82sDuVDJJxdUymbid',
        'origin/claude/gpt-integration-01CKQhmQiYVfVvnk54THC99q',
        'origin/claude/gemini-integration-01V2YRQaXtKu1ncjtJw6JwYX',
    ],

    # Export Engines (39-44)
    'exports': [
        'claude/39-export-latex-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/40-export-pdf-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/41-export-word-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/42-export-html-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/43-export-excel-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/44-export-json-xml-01Ee5VFdXvTFxTYjX4N8bMmo',
        'origin/claude/latex-report-export-01F9omgyBqc469DhxmoNdSm2',
    ],

    # Editors (45-48)
    'editors': [
        'claude/45-editor-document-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/46-editor-excel-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/47-editor-flowchart-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/48-editor-gantt-01Ee5VFdXvTFxTYjX4N8bMmo',
    ],

    # UI Components (49-54)
    'ui': [
        'claude/49-ui-main-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/50-ui-dashboard-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/51-ui-upload-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/52-ui-report-builder-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/53-ui-review-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/54-ui-export-01Ee5VFdXvTFxTYjX4N8bMmo',
        'origin/claude/streamlit-ui-application-013fJZ6cU3DGzszKVZSAFFLQ',
        'origin/claude/streamlit-pv-app-phase1-017t4fcPoZzjXEQknSdmSGrt',
        'origin/claude/deploy-streamlit-pv-automation-01K1Q3f4We5qSWMdXGcV3FiU',
    ],

    # Testing (55-58)
    'tests': [
        'claude/55-integration-tests-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/56-unit-tests-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/57-qa-tests-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/58-e2e-workflow-01Ee5VFdXvTFxTYjX4N8bMmo',
    ],

    # Optimization & Deployment (59-60)
    'deployment': [
        'claude/59-optimization-01Ee5VFdXvTFxTYjX4N8bMmo',
        'claude/60-deployment-01Ee5VFdXvTFxTYjX4N8bMmo',
    ],
}


def run_command(cmd: List[str]) -> str:
    """Execute shell command and return output"""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def checkout_branch(branch: str) -> bool:
    """Checkout a specific branch"""
    try:
        if branch.startswith('origin/'):
            branch_name = branch.replace('origin/', '')
            subprocess.run(['git', 'checkout', '-b', f'temp-{branch_name}', branch],
                         check=True, capture_output=True)
        else:
            subprocess.run(['git', 'checkout', branch], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        print(f"  ⚠️  Failed to checkout {branch}")
        return False


def copy_python_files(source_dir: str, target_dir: str, prefix: str = ""):
    """Copy Python files from source to target directory"""
    source_path = Path(source_dir)
    target_path = Path(target_dir)

    if not source_path.exists():
        return 0

    count = 0
    for py_file in source_path.rglob('*.py'):
        if '__pycache__' in str(py_file) or 'venv' in str(py_file):
            continue

        rel_path = py_file.relative_to(source_path)

        if prefix:
            target_file = target_path / f"{prefix}_{rel_path.name}"
        else:
            target_file = target_path / rel_path.name

        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(py_file, target_file)
        count += 1

    return count


def integrate_module(module_name: str, branches: List[str], target_dir: str):
    """Integrate code from multiple branches into a target directory"""
    print(f"\n{'='*80}")
    print(f"📦 Integrating {module_name.upper()} module")
    print(f"{'='*80}")

    original_branch = run_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
    total_files = 0

    for branch in branches:
        print(f"\n  🔄 Processing {branch}...")

        if not checkout_branch(branch):
            continue

        # Look for common source directories
        source_dirs = ['src', 'app', 'modules', '.']
        files_copied = 0

        for src_dir in source_dirs:
            if Path(src_dir).exists():
                files_copied += copy_python_files(src_dir, target_dir)

        print(f"     ✓ Copied {files_copied} files")
        total_files += files_copied

        # Cleanup temp branch
        if branch.startswith('origin/'):
            subprocess.run(['git', 'checkout', original_branch],
                         capture_output=True)
            temp_branch = f"temp-{branch.replace('origin/', '')}"
            subprocess.run(['git', 'branch', '-D', temp_branch],
                         capture_output=True)

    # Return to original branch
    subprocess.run(['git', 'checkout', original_branch], capture_output=True)

    print(f"\n  ✅ {module_name.upper()}: Integrated {total_files} total files")
    return total_files


def main():
    """Main integration orchestrator"""
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║        PV TEST AUTOMATION - BRANCH INTEGRATION SYSTEM                ║
    ║        Stitching 60+ Feature Branches into Unified Codebase          ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Integration order (dependency-based)
    integration_order = [
        ('core', 'src/core'),
        ('ingestion', 'src/ingestion'),
        ('protocols', 'src/protocols'),
        ('test_blocks', 'src/test_blocks'),
        ('workflows', 'src/workflows'),
        ('llm', 'src/llm'),
        ('exports', 'src/exports'),
        ('editors', 'src/utils/editors'),
        ('ui', 'streamlit_app'),
        ('tests', 'tests'),
        ('deployment', 'docker'),
    ]

    total_integrated = 0

    for module, target in integration_order:
        if module in BRANCH_INTEGRATION_MAP:
            count = integrate_module(
                module,
                BRANCH_INTEGRATION_MAP[module],
                target
            )
            total_integrated += count

    print(f"""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║        ✅ INTEGRATION COMPLETE!                                      ║
    ║        Total files integrated: {total_integrated:4d}                                    ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)


if __name__ == '__main__':
    main()
