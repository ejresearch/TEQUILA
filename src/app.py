"""FastAPI application for Latin A curriculum management."""
from fastapi import FastAPI, HTTPException, Path as PathParam
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Any
from pathlib import Path

from .config import settings
from .services.generator_week import scaffold_week
from .services.generator_day import scaffold_day
from .services.storage import (
    day_field_path,
    week_spec_part_path,
    role_context_part_path,
    compile_day_flint_bundle,
    compile_week_spec,
    compile_role_context,
    read_file,
    write_file,
    read_json,
    write_json,
    DAY_FIELDS,
    WEEK_SPEC_PARTS,
    ROLE_CONTEXT_PARTS
)
from .services.validator import validate_week
from .services.exporter import export_week_to_zip

# Create FastAPI app
app = FastAPI(
    title="Latin A Curriculum API",
    description="API for managing 36-week Latin A curriculum with per-field file structure",
    version="1.0.0"
)


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "Latin A Curriculum API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# ============================================================================
# WEEK SCAFFOLDING
# ============================================================================

@app.post("/api/v1/weeks/{week}/scaffold")
def scaffold_week_endpoint(
    week: int = PathParam(..., ge=1, le=36, description="Week number (1-36)")
):
    """
    Scaffold a complete week structure with all folders and placeholder files.

    Creates:
    - Week_Spec/ with 12 parts
    - Role_Context/ with 7 parts
    - activities/ directory
    - assets/ directory
    """
    try:
        week_path = scaffold_week(week)
        return {
            "message": f"Week {week} scaffolded successfully",
            "week_path": str(week_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DAY FIELD OPERATIONS
# ============================================================================

@app.get("/api/v1/weeks/{week}/days/{day}/fields/{field}")
def get_day_field(
    week: int = PathParam(..., ge=1, le=36),
    day: int = PathParam(..., ge=1, le=4),
    field: str = PathParam(..., description="Field name (e.g., 01_class_name.txt)")
):
    """Get a specific day field file content."""
    if field not in DAY_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid field name. Must be one of: {DAY_FIELDS}")

    field_path = day_field_path(week, day, field)

    if not field_path.exists():
        raise HTTPException(status_code=404, detail=f"Field not found: {field}")

    try:
        if field.endswith(".json"):
            content = read_json(field_path)
        else:
            content = read_file(field_path)

        return {"field": field, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/weeks/{week}/days/{day}/fields/{field}")
def update_day_field(
    content: Dict[str, Any],
    week: int = PathParam(..., ge=1, le=36),
    day: int = PathParam(..., ge=1, le=4),
    field: str = PathParam(..., description="Field name")
):
    """Update a specific day field file content."""
    if field not in DAY_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid field name. Must be one of: {DAY_FIELDS}")

    field_path = day_field_path(week, day, field)

    try:
        if field.endswith(".json"):
            write_json(field_path, content.get("content", {}))
        else:
            write_file(field_path, content.get("content", ""))

        return {"message": f"Field {field} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/weeks/{week}/days/{day}/flint-bundle")
def get_day_flint_bundle(
    week: int = PathParam(..., ge=1, le=36),
    day: int = PathParam(..., ge=1, le=4)
):
    """Get all six Flint fields compiled into a single JSON bundle."""
    try:
        bundle = compile_day_flint_bundle(week, day)
        return {
            "week": week,
            "day": day,
            "fields": bundle
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEEK SPEC OPERATIONS
# ============================================================================

@app.get("/api/v1/weeks/{week}/spec/parts/{part}")
def get_week_spec_part(
    week: int = PathParam(..., ge=1, le=36),
    part: str = PathParam(..., description="Spec part name (e.g., 01_metadata.json)")
):
    """Get a specific week spec part."""
    if part not in WEEK_SPEC_PARTS:
        raise HTTPException(status_code=400, detail=f"Invalid part name. Must be one of: {WEEK_SPEC_PARTS}")

    part_path = week_spec_part_path(week, part)

    if not part_path.exists():
        raise HTTPException(status_code=404, detail=f"Spec part not found: {part}")

    try:
        if part.endswith(".json"):
            content = read_json(part_path)
        else:
            content = read_file(part_path)

        return {"part": part, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/weeks/{week}/spec/parts/{part}")
def update_week_spec_part(
    content: Dict[str, Any],
    week: int = PathParam(..., ge=1, le=36),
    part: str = PathParam(..., description="Spec part name")
):
    """Update a specific week spec part."""
    if part not in WEEK_SPEC_PARTS:
        raise HTTPException(status_code=400, detail=f"Invalid part name. Must be one of: {WEEK_SPEC_PARTS}")

    part_path = week_spec_part_path(week, part)

    try:
        if part.endswith(".json"):
            write_json(part_path, content.get("content", {}))
        else:
            write_file(part_path, content.get("content", ""))

        return {"message": f"Spec part {part} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/weeks/{week}/spec/compiled")
def get_compiled_week_spec(
    week: int = PathParam(..., ge=1, le=36)
):
    """Get the compiled week specification (all parts combined)."""
    try:
        spec = compile_week_spec(week)
        return {
            "week": week,
            "spec": spec
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# VALIDATION AND EXPORT
# ============================================================================

@app.post("/api/v1/weeks/{week}/validate")
def validate_week_endpoint(
    week: int = PathParam(..., ge=1, le=36)
):
    """Validate a complete week structure."""
    result = validate_week(week)

    return {
        "week": week,
        "is_valid": result.is_valid(),
        "summary": result.summary(),
        "errors": [{"location": e.location, "message": e.message} for e in result.errors],
        "warnings": [{"location": w.location, "message": w.message} for w in result.warnings],
        "info": [{"location": i.location, "message": i.message} for i in result.info]
    }


@app.post("/api/v1/weeks/{week}/export")
def export_week_endpoint(
    week: int = PathParam(..., ge=1, le=36)
):
    """Export a week to a zip file in the exports directory."""
    # First validate
    result = validate_week(week)

    if not result.is_valid():
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Week validation failed. Fix errors before exporting.",
                "errors": [{"location": e.location, "message": e.message} for e in result.errors]
            }
        )

    try:
        zip_path = export_week_to_zip(week)
        return {
            "message": f"Week {week} exported successfully",
            "zip_path": str(zip_path),
            "size_kb": zip_path.stat().st_size / 1024
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/weeks/{week}/export/download")
def download_week_export(
    week: int = PathParam(..., ge=1, le=36)
):
    """Download the exported zip file for a week."""
    from .services.exporter import get_exports_dir

    zip_path = get_exports_dir() / f"LatinA_Week{week:02d}.zip"

    if not zip_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Export not found for Week {week}. Use POST /api/v1/weeks/{week}/export first."
        )

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=zip_path.name
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
