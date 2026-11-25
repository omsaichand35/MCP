import datetime
import stat
from pathlib import Path
import shutil

WORKSPACE = (Path(__file__).parent / "workspace").resolve()

def safe_path(relative_path) -> Path:
    """
    Converts a user path into an absolute path inside the workspace.
    Prevents directory traversal attacks.
    """
    path = (WORKSPACE / relative_path).resolve()

    try:
        path.relative_to(WORKSPACE)
    except ValueError:
        raise ValueError("Access outside workspace is not allowed")
    return path

def list_files(relative_path: str = ".") -> list[Path]:
    """
    Returns a list of all files and folders in the workspace.
    """
    path = safe_path(relative_path)

    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    if not path.is_dir():
        raise NotADirectoryError(f"{path} is not a directory")

    return [item.name for item in path.iterdir()]

def read_file(relative_path: str = ".") -> str:
    """
    Reads the contents of a file inside the workspace.
    """

    path = safe_path(relative_path)

    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    if not path.is_file():
        raise ValueError("File does not exist")
    return path.read_text(encoding="utf-8")

def write_file(relative_path: str = ".", data: str = "") -> None:
    """
    Write contents to a file inside the workspace.
    """
    path = safe_path(relative_path)

    if path.exists() and not path.is_file():
        raise ValueError("Path is not a file")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")

def create_directory(relative_path: str) ->  None:
    """
    Creates a directory inside the workspace.
    """
    path = safe_path(relative_path)

    if path.exists():
        raise FileExistsError(f"Directory already exists")

    path.mkdir(parents=True, exist_ok=True)

def delete_file(relative_path: str) -> None:
    """
    Deletes a file or directories inside the workspace.
    """
    path = safe_path(relative_path)

    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)

def tree(relative_path: str) -> str:
    """
    Returns a directory tree inside the workspace.
    """
    path = safe_path(relative_path)
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    if not path.is_dir():
        raise NotADirectoryError(f"{path} is not a directory")

    lines = []
    def build_tree(current_path: Path, prefix: str = ""):
        children = sorted(current_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

        for idx, child in enumerate(children):
            is_last = idx == len(children) - 1
            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + child.name)
            if child.is_dir():
                new_prefix = prefix + ("    " if is_last else "|    ")
                build_tree(child, new_prefix)
    lines.append(path.name)
    build_tree(path)
    return "\n".join(lines)

def rename(source_pth: str, destination_pth: str) -> None:
    """
    Renames a file or directories inside the workspace.
    """
    source = safe_path(source_pth)
    destination = safe_path(destination_pth)

    if not source.exists():
        raise FileNotFoundError(f"{source} does not exist")
    if destination.exists():
        raise FileExistsError(f"{destination} already exists.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    source.rename(destination)

def copy(source_pth: str, destination_pth: str) -> None:
    """
    Copies a file or directories to another location inside the workspace.
    """
    source = safe_path(source_pth)
    destination = safe_path(destination_pth)

    if not source.exists():
        raise FileNotFoundError(f"{source} does not exist")
    if destination.exists():
        raise FileExistsError(f"{destination} already exists.")

    if source.is_dir() and destination.is_relative_to(source):
        raise ValueError("Cannot copy a directory into itself")

    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)

def search(pattern: str, relative_path: str = ".") -> list[str]:
    """
    Searches recursively for files and directories.
    Matching a glob pattern.
    """
    path = safe_path(relative_path)

    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    if not path.is_dir():
        raise ValueError("Path is not a directory")
    matches = []

    for item in path.rglob(pattern):
        matches.append(str(item.relative_to(WORKSPACE)))
    return matches

def search_content(
    query: str,
    relative_path: str = "."
) -> list[str]:
    """
    Recursively searches text files for a query.
    Returns matching file paths and line numbers.
    """

    path = safe_path(relative_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Path '{relative_path}' does not exist."
        )

    if not path.is_dir():
        raise ValueError(
            "Search path is not a directory."
        )

    matches = []

    for file_path in path.rglob("*"):

        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text(
                encoding="utf-8"
            )
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(
            content.splitlines(),
            start=1
        ):
            if query.lower() in line.lower():

                relative_file = file_path.relative_to(
                    WORKSPACE
                )

                matches.append(
                    f"{relative_file}:{line_number}: {line.strip()}"
                )

    return matches

def file_info(relative_path: str) -> dict:
    """
    Returns metadata about a file or a directory inside the workspace
    """
    path = safe_path(relative_path)

    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    stats = path.stat()

    return {
        "name": path.name,
        "path": str(path.relative_to(WORKSPACE)),
        "type": "directory" if path.is_dir() else "file",
        "size": stats.st_size,
        "extension": path.suffix if path.is_file() else "",
        "created": datetime.datetime.fromtimestamp(stats.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
        "modified": datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }
