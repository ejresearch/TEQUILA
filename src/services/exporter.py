"""Export service for packaging curriculum weeks."""
import zipfile
from pathlib import Path
from .storage import week_dir, get_curriculum_base, save_compiled_week_spec, save_compiled_role_context


def get_exports_dir() -> Path:
    """Get the exports directory path."""
    return get_curriculum_base() / "exports"


def export_week_to_zip(week_number: int) -> Path:
    """
    Export a complete week to a zip file in the exports directory.

    Creates a zip file containing:
    - All Week_Spec parts (including compiled version)
    - All Role_Context parts (including compiled version)
    - All day activities with Flint fields
    - All assets

    Args:
        week_number: The week number (1-36)

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

    # Create zip file
    zip_filename = f"LatinA_Week{week_number:02d}.zip"
    zip_path = exports_dir / zip_filename

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all files from the week directory
        for file_path in week_path.rglob('*'):
            if file_path.is_file():
                # Calculate relative path for archive
                arcname = file_path.relative_to(week_path.parent)
                zipf.write(file_path, arcname)

    return zip_path


def export_all_weeks(num_weeks: int = 36) -> list[Path]:
    """
    Export all weeks to individual zip files.

    Args:
        num_weeks: Number of weeks to export (default: 36)

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
