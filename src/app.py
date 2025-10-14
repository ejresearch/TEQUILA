"""FastAPI application for Latin A curriculum management."""
from fastapi import FastAPI, HTTPException, Path as PathParam, Header, Depends
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Any, Optional
from pathlib import Path
import os

from .config import settings, get_llm_client
from .services.generator_week import (
    scaffold_week,
    generate_week_spec_from_outline,
    generate_role_context,
    generate_assets
)
from .services.generator_day import (
    scaffold_day,
    generate_day_fields,
    generate_day_document,
    hydrate_day_from_llm
)
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
from .services.usage_tracker import get_tracker

# Create FastAPI app
app = FastAPI(
    title="Latin A Curriculum API",
    description="API for managing 36-week Latin A curriculum with per-field file structure",
    version="1.0.0"
)


# ============================================================================
# AUTHENTICATION
# ============================================================================

def require_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Require API key for protected endpoints.

    Set API_AUTH_KEY in .env to enable authentication.
    If not set, all requests are allowed (development mode).
    """
    auth_key = os.getenv("API_AUTH_KEY")

    # If no auth key configured, allow all requests (dev mode)
    if not auth_key:
        return

    # If auth key is configured, require it
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header."
        )

    if x_api_key != auth_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "Latin A Curriculum API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/v1/usage")
def get_usage():
    """Get LLM usage statistics and cost estimates."""
    return get_tracker().get_summary()


@app.post("/api/v1/usage/reset")
def reset_usage(_auth: None = Depends(require_api_key)):
    """Reset usage statistics. Requires API key."""
    get_tracker().reset()
    return {"message": "Usage statistics reset successfully"}


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


# ============================================================================
# LLM GENERATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/gen/weeks/{week}/spec")
def generate_week_spec_endpoint(
    week: int = PathParam(..., ge=1, le=36),
    _auth: None = Depends(require_api_key)
):
    """Generate week specification using LLM. Requires API key."""
    try:
        client = get_llm_client()
        spec_path = generate_week_spec_from_outline(week, client)
        return {
            "message": f"Week {week} spec generated successfully",
            "spec_path": str(spec_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/gen/weeks/{week}/role-context")
def generate_role_context_endpoint(
    week: int = PathParam(..., ge=1, le=36),
    _auth: None = Depends(require_api_key)
):
    """Generate Sparky role context using LLM. Requires API key."""
    try:
        client = get_llm_client()
        context_path = generate_role_context(week, client)
        return {
            "message": f"Week {week} role context generated successfully",
            "context_path": str(context_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/gen/weeks/{week}/assets")
def generate_assets_endpoint(
    week: int = PathParam(..., ge=1, le=36),
    _auth: None = Depends(require_api_key)
):
    """Generate week assets using LLM. Requires API key."""
    try:
        client = get_llm_client()
        asset_paths = generate_assets(week, client)
        return {
            "message": f"Week {week} assets generated successfully",
            "asset_paths": [str(p) for p in asset_paths]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/gen/weeks/{week}/days/{day}/fields")
def generate_day_fields_endpoint(
    week: int = PathParam(..., ge=1, le=36),
    day: int = PathParam(..., ge=1, le=4),
    _auth: None = Depends(require_api_key)
):
    """Generate day Flint fields using LLM. Requires API key."""
    try:
        client = get_llm_client()
        field_paths = generate_day_fields(week, day, client)
        return {
            "message": f"Week {week} Day {day} fields generated successfully",
            "field_paths": [str(p) for p in field_paths]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/gen/weeks/{week}/days/{day}/document")
def generate_day_document_endpoint(
    week: int = PathParam(..., ge=1, le=36),
    day: int = PathParam(..., ge=1, le=4),
    _auth: None = Depends(require_api_key)
):
    """Generate day document_for_sparky using LLM. Requires API key."""
    try:
        client = get_llm_client()
        doc_path = generate_day_document(week, day, client)
        return {
            "message": f"Week {week} Day {day} document generated successfully",
            "document_path": str(doc_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/gen/weeks/{week}/hydrate")
def hydrate_week_endpoint(
    week: int = PathParam(..., ge=1, le=36),
    _auth: None = Depends(require_api_key)
):
    """
    Hydrate complete week using LLM (spec, role context, assets, all days). Requires API key.

    This generates everything in order:
    1. Week spec
    2. Role context
    3. Assets
    4. All 4 days (fields + documents)
    """
    try:
        client = get_llm_client()
        results = {"week": week, "components": {}}

        # Generate week components
        spec_path = generate_week_spec_from_outline(week, client)
        results["components"]["spec"] = str(spec_path)

        role_path = generate_role_context(week, client)
        results["components"]["role_context"] = str(role_path)

        asset_paths = generate_assets(week, client)
        results["components"]["assets"] = [str(p) for p in asset_paths]

        # Generate all days
        results["components"]["days"] = []
        for day in range(1, 5):
            day_result = hydrate_day_from_llm(week, day, client)
            results["components"]["days"].append(day_result)

        # Run validation
        from .services.validator import validate_week
        validation = validate_week(week)
        results["validation"] = {
            "is_valid": validation.is_valid(),
            "summary": validation.summary(),
            "error_count": len(validation.errors),
            "warning_count": len(validation.warnings)
        }

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
