from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile
from datetime import date, datetime
from pydantic import BaseModel
from graph import verify_api_key, get_graph_token

router = APIRouter(prefix="/sharepoint", tags=["Sharepoint"])

@router.get("/projekte/{short}/dateien/{filename}/inhalt", dependencies=[Depends(verify_api_key)], tags=["SharePoint"])
async def get_file_content(short: str, filename: str):
    token = await get_graph_token()
    headers = {"Authorization": f"Bearer {token}"}
    path = f"{FOLDER.rstrip('/')}/{short}:/children"
    url = f"{GRAPH_URL}/sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{path}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        files = response.json().get("value", [])
        match = next((f for f in files if f["name"] == filename), None)
        if not match:
            raise HTTPException(status_code=404, detail="Datei nicht gefunden")

        download_url = match.get("@microsoft.graph.downloadUrl")
        file_ext = filename.lower().split('.')[-1]

        download = await client.get(download_url)
        content = download.content

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            if file_ext == "docx":
                return {"text": extract_docx(tmp_path)}
            elif file_ext == "pdf":
                return {"text": extract_pdf(tmp_path)}
            elif file_ext == "xlsx":
                return {"text": extract_xlsx(tmp_path)}
            elif file_ext == "txt":
                return {"text": extract_txt(tmp_path)}
            elif file_ext == "eml":
                return {"text": extract_eml(content)}
            else:
                raise HTTPException(status_code=415, detail="Nicht unterstützter Dateityp")
        finally:
            os.unlink(tmp_path)

@router.get("/projekte/{short}/dateien", dependencies=[Depends(verify_api_key)], tags=["SharePoint"])
async def list_project_files(short: str):
    token = await get_graph_token()
    path = f"{FOLDER.rstrip('/')}/{short}:/children"
    url = f"{GRAPH_URL}/sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{path}"

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        items = response.json().get("value", [])
        return [
            {
                "name": f["name"],
                "url": f["webUrl"],
                "size": f.get("size"),
                "lastModified": f.get("lastModifiedDateTime")
            }
            for f in items if "file" in f
        ]

@router.post("/projekte/{short}/dateien", dependencies=[Depends(verify_api_key)], tags=["SharePoint"])
async def upload_file_to_sharepoint(short: str, file: UploadFile = File(...)):
    token = await get_graph_token()
    if not token:
        raise HTTPException(status_code=500, detail="Kein Zugriffstoken erhalten")

    headers = {
        "Authorization": f"Bearer {token}"
    }
    path = f"{FOLDER.rstrip('/')}/{short}/{file.filename}"
    url = f"{GRAPH_URL}/sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{path}:/content"

    content = await file.read()
    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, content=content)
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Upload erfolgreich", "filename": file.filename}

def extract_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_pdf(path):
    doc = fitz.open(path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text

def extract_xlsx(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    return "\n".join(
        "\t".join(str(cell) if cell else "" for cell in row)
        for sheet in wb for row in sheet.iter_rows(values_only=True)
    )

def extract_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_eml(content_bytes):
    msg = BytesParser(policy=policy.default).parsebytes(content_bytes)
    parts = []
    if msg["subject"]:
        parts.append(f"Subject: {msg['subject']}")
    if msg["from"]:
        parts.append(f"From: {msg['from']}")
    if msg["to"]:
        parts.append(f"To: {msg['to']}")
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                parts.append(part.get_content())
    else:
        parts.append(msg.get_content())
    return "\n".join(parts)