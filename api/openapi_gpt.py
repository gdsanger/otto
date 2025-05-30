from fastapi.openapi.utils import get_openapi
from fastapi import APIRouter, Request

router = APIRouter()

SCOPES = {
    "projekte": ["Projekt", "Task"],
    "kalender": ["Kalender", "Tagesplan"],
    "meetings": ["Meeting"],
    "dateien": ["SharePoint"],
    "personen": ["Personen"]
}

@router.get("/openapi-gpt.json")
def get_openapi_subset(request: Request, scope: str = "projekte"):
    full_spec = get_openapi(
        title="OttoCore API (GPT) Scope",
        version="1.0.0",
        description=f"Reduzierte API-Spec für GPT-Scope: {scope}",
        routes=request.app.routes,
    )

    allowed_tags = SCOPES.get(scope, [])
    filtered_paths = {}

    for path, methods in full_spec["paths"].items():
        for method, details in methods.items():
            if any(tag in allowed_tags for tag in details.get("tags", [])):
                if path not in filtered_paths:
                    filtered_paths[path] = {}
                filtered_paths[path][method] = details

    full_spec["paths"] = filtered_paths
    full_spec["servers"] = [{
        "url": "https://otto.isarlabs.de",
        "description": "Produktivserver"
    }]

    return full_spec