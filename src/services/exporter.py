"""Export service for packaging curriculum weeks (v1.0 Pilot)."""
import zipfile
import hashlib
import orjson
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from .storage import week_dir, get_curriculum_base, save_compiled_week_spec, save_compiled_role_context


def get_exports_dir() -> Path:
    """Get the exports directory path."""
    return get_curriculum_base() / "exports"


def _calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _generate_manifest(week_number: int, week_path: Path) -> Dict[str, Any]:
    """
    Generate a manifest.json for the week export.

    Includes:
    - Week metadata
    - List of all files with SHA256 hashes
    - Export timestamp
    - Version info
    """
    manifest = {
        "week": week_number,
        "export_date": datetime.now().isoformat(),
        "version": "1.0.0",
        "pilot": "Latin A v1.0 Pilot (35 weeks)",
        "files": []
    }

    # Collect all files with SHA256 hashes
    for file_path in sorted(week_path.rglob('*')):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(week_path))
            file_info = {
                "path": rel_path,
                "size_bytes": file_path.stat().st_size,
                "sha256": _calculate_sha256(file_path)
            }
            manifest["files"].append(file_info)

    manifest["file_count"] = len(manifest["files"])
    manifest["total_size_bytes"] = sum(f["size_bytes"] for f in manifest["files"])

    return manifest


def export_week_to_zip(week_number: int) -> Path:
    """
    Export a complete week to a zip file with manifest.json in the exports directory.

    Creates a zip file containing:
    - All Week_Spec parts (including compiled version)
    - All Role_Context parts (including compiled version)
    - All day activities with Flint fields (7-field architecture)
    - All assets
    - manifest.json with SHA256 hashes for all files

    Args:
        week_number: The week number (1-35 for v1.0 Pilot)

    Returns:
        Path to the created zip file.
    """
    week_path = week_dir(week_number)

    if not week_path.exists():
        raise FileNotFoundError(f"Week {week_number} does not exist at {week_path}")

    # Create exports directory if it doesn't exist
    exports_dir = get_exports_dir()
    exports_dir.mkdir(parents=True, exist_ok=True)

    # Generate compiled files before exporting
    try:
        save_compiled_week_spec(week_number)
        save_compiled_role_context(week_number)
    except Exception as e:
        print(f"Warning: Could not generate compiled files: {e}")

    # Generate manifest with SHA256 hashes
    manifest = _generate_manifest(week_number, week_path)

    # Save manifest.json temporarily in week directory
    manifest_path = week_path / "manifest.json"
    with open(manifest_path, 'wb') as f:
        f.write(orjson.dumps(manifest, option=orjson.OPT_INDENT_2))

    # Create zip file
    zip_filename = f"Week{week_number:02d}.zip"
    zip_path = exports_dir / zip_filename

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from the week directory
            for file_path in week_path.rglob('*'):
                if file_path.is_file():
                    # Calculate relative path for archive
                    arcname = file_path.relative_to(week_path.parent)
                    zipf.write(file_path, arcname)
    finally:
        # Clean up temporary manifest
        if manifest_path.exists():
            manifest_path.unlink()

    return zip_path


def export_all_weeks(num_weeks: int = 35) -> list[Path]:
    """
    Export all weeks to individual zip files (v1.0 Pilot: 35 weeks).

    Args:
        num_weeks: Number of weeks to export (default: 35 for v1.0 Pilot)

    Returns:
        List of paths to created zip files.
    """
    zip_paths = []

    for week_num in range(1, num_weeks + 1):
        week_path = week_dir(week_num)
        if week_path.exists():
            try:
                zip_path = export_week_to_zip(week_num)
                zip_paths.append(zip_path)
                print(f"✓ Exported Week {week_num} to {zip_path.name}")
            except Exception as e:
                print(f"✗ Failed to export Week {week_num}: {e}")
        else:
            print(f"⊘ Skipped Week {week_num} (does not exist)")

    return zip_paths
