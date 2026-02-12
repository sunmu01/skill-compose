"""File browser API endpoints for browsing project files."""
import io
import mimetypes
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.config import get_settings, Settings

router = APIRouter(prefix="/browser", tags=["Browser"])

# File extensions considered as text
TEXT_EXTENSIONS = {
    '.md', '.txt', '.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.yaml', '.yml',
    '.sh', '.bash', '.css', '.html', '.xml', '.csv', '.toml', '.ini', '.cfg',
    '.conf', '.env', '.gitignore', '.dockerfile', '.sql', '.go', '.rs', '.java',
    '.c', '.cpp', '.h', '.hpp', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
    '.vue', '.svelte', '.astro', '.prisma', '.graphql', '.proto', '.makefile',
}

# Image extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.bmp'}

# Directories to hide from browser
HIDDEN_DIRS = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv', '.env',
    '.idea', '.vscode', '.DS_Store', '.pytest_cache', '.mypy_cache',
    '.tox', '.eggs', '*.egg-info', 'dist', 'build', '.next', '.nuxt',
}

# Files to hide
HIDDEN_FILES = {
    '.env', '.env.local', '.env.production', '.env.development',
    'credentials.json', 'secrets.json', '.npmrc', '.pypirc',
}


class FileEntry(BaseModel):
    """Single file or directory entry."""
    name: str
    path: str  # Relative path from project root
    type: Literal["file", "directory"]
    size: Optional[int] = None
    modified_at: datetime
    extension: Optional[str] = None
    is_text: bool = False
    is_image: bool = False


class DirectoryContents(BaseModel):
    """Directory listing response."""
    path: str
    parent_path: Optional[str]
    entries: list[FileEntry]
    breadcrumbs: list[dict]  # [{name, path}, ...]


def get_project_root(settings: Settings = Depends(get_settings)) -> Path:
    """Get project root directory."""
    return Path(settings.project_dir).resolve()


def validate_path(path: str, project_root: Path) -> Path:
    """Validate and resolve path, preventing traversal attacks."""
    # Normalize the path
    if not path:
        return project_root

    # Remove leading slashes
    clean_path = path.lstrip('/')

    # Resolve the full path
    full_path = (project_root / clean_path).resolve()

    # Ensure it's within project root
    try:
        full_path.relative_to(project_root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path: traversal detected")

    return full_path


def is_hidden(path: Path) -> bool:
    """Check if path should be hidden."""
    name = path.name

    # Check hidden files
    if name in HIDDEN_FILES:
        return True

    # Check hidden directories
    if name in HIDDEN_DIRS:
        return True

    # Check if starts with . (except .env files which are already handled)
    if name.startswith('.') and name not in {'.gitignore', '.dockerignore', '.editorconfig'}:
        return True

    return False


def get_file_info(path: Path, project_root: Path) -> FileEntry:
    """Get file/directory info."""
    stat = path.stat()
    relative_path = str(path.relative_to(project_root))

    is_dir = path.is_dir()
    extension = None if is_dir else path.suffix.lower()

    return FileEntry(
        name=path.name,
        path=relative_path,
        type="directory" if is_dir else "file",
        size=None if is_dir else stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        extension=extension,
        is_text=extension in TEXT_EXTENSIONS if extension else False,
        is_image=extension in IMAGE_EXTENSIONS if extension else False,
    )


def build_breadcrumbs(path: str) -> list[dict]:
    """Build breadcrumb navigation from path."""
    if not path or path == '.':
        return [{"name": "Root", "path": ""}]

    breadcrumbs = [{"name": "Root", "path": ""}]
    parts = path.split('/')
    current_path = ""

    for part in parts:
        if part:
            current_path = f"{current_path}/{part}" if current_path else part
            breadcrumbs.append({"name": part, "path": current_path})

    return breadcrumbs


@router.get("/list", response_model=DirectoryContents)
async def list_directory(
    path: str = Query("", description="Directory path relative to project root"),
    project_root: Path = Depends(get_project_root),
):
    """List contents of a directory."""
    full_path = validate_path(path, project_root)

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    if not full_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    entries = []
    try:
        for item in sorted(full_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if is_hidden(item):
                continue
            try:
                entries.append(get_file_info(item, project_root))
            except (PermissionError, OSError):
                # Skip files we can't access
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    relative_path = str(full_path.relative_to(project_root))
    if relative_path == '.':
        relative_path = ""

    # Calculate parent path
    parent_path = None
    if relative_path:
        parent = Path(relative_path).parent
        parent_path = str(parent) if str(parent) != '.' else ""

    return DirectoryContents(
        path=relative_path,
        parent_path=parent_path,
        entries=entries,
        breadcrumbs=build_breadcrumbs(relative_path),
    )


@router.get("/preview")
async def preview_file(
    path: str = Query(..., description="File path relative to project root"),
    project_root: Path = Depends(get_project_root),
):
    """Get file content for preview (text files only)."""
    full_path = validate_path(path, project_root)

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    # Check file size (limit to 1MB for preview)
    stat = full_path.stat()
    if stat.st_size > 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large for preview (max 1MB)")

    extension = full_path.suffix.lower()

    # For images, return base64 encoded data
    if extension in IMAGE_EXTENSIONS:
        async with aiofiles.open(full_path, 'rb') as f:
            content = await f.read()
        import base64
        mime_type = mimetypes.guess_type(str(full_path))[0] or 'application/octet-stream'
        return {
            "type": "image",
            "mime_type": mime_type,
            "content": base64.b64encode(content).decode('utf-8'),
        }

    # For text files, return content
    if extension in TEXT_EXTENSIONS or not extension:
        try:
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return {
                "type": "text",
                "content": content,
                "extension": extension.lstrip('.') if extension else None,
            }
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File is not a text file")

    raise HTTPException(status_code=400, detail="File type not supported for preview")


@router.get("/download")
async def download_file(
    path: str = Query(..., description="File path relative to project root"),
    project_root: Path = Depends(get_project_root),
):
    """Download a single file."""
    full_path = validate_path(path, project_root)

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    mime_type = mimetypes.guess_type(str(full_path))[0] or 'application/octet-stream'

    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type=mime_type,
    )


@router.get("/download-zip")
async def download_folder_as_zip(
    path: str = Query(..., description="Folder path relative to project root"),
    project_root: Path = Depends(get_project_root),
):
    """Download a folder as a zip file."""
    full_path = validate_path(path, project_root)

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")

    if not full_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a folder")

    # Create zip in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in full_path.rglob('*'):
            if file_path.is_file() and not is_hidden(file_path):
                # Check if any parent is hidden
                skip = False
                for parent in file_path.relative_to(full_path).parents:
                    if is_hidden(full_path / parent):
                        skip = True
                        break
                if skip:
                    continue

                arcname = str(file_path.relative_to(full_path))
                zip_file.write(file_path, arcname)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{full_path.name}.zip"'
        }
    )


@router.post("/upload")
async def upload_file(
    path: str = Query("", description="Target directory path relative to project root"),
    file: UploadFile = File(...),
    project_root: Path = Depends(get_project_root),
):
    """Upload a file to the specified directory."""
    target_dir = validate_path(path, project_root)

    if not target_dir.exists():
        raise HTTPException(status_code=404, detail="Target directory not found")

    if not target_dir.is_dir():
        raise HTTPException(status_code=400, detail="Target path is not a directory")

    # Sanitize filename
    filename = file.filename or "uploaded_file"
    safe_name = "".join(c if c.isalnum() or c in ".-_ " else "_" for c in filename)

    target_path = target_dir / safe_name

    # Check if file already exists
    if target_path.exists():
        raise HTTPException(status_code=409, detail="File already exists")

    # Save file
    async with aiofiles.open(target_path, 'wb') as f:
        while chunk := await file.read(8192):
            await f.write(chunk)

    return get_file_info(target_path, project_root)


@router.delete("/delete")
async def delete_file(
    path: str = Query(..., description="File or directory path to delete"),
    project_root: Path = Depends(get_project_root),
):
    """Delete a file or empty directory."""
    full_path = validate_path(path, project_root)

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    # Prevent deleting project root
    if full_path == project_root:
        raise HTTPException(status_code=400, detail="Cannot delete project root")

    if full_path.is_file():
        full_path.unlink()
        return {"message": "File deleted successfully"}
    elif full_path.is_dir():
        # Only allow deleting empty directories for safety
        if any(full_path.iterdir()):
            raise HTTPException(status_code=400, detail="Directory is not empty")
        full_path.rmdir()
        return {"message": "Directory deleted successfully"}

    raise HTTPException(status_code=400, detail="Unknown path type")
