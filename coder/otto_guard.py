import os
import shutil
from pathlib import Path
from html.parser import HTMLParser
import ast

BACKUP_COUNT = 10

def rotate_backups(filepath):
    path = Path(filepath)
    for i in reversed(range(BACKUP_COUNT - 1)):
        older = path.with_suffix(path.suffix + f".sic.{i}")
        newer = path.with_suffix(path.suffix + f".sic.{i + 1}")
        if older.exists():
            older.rename(newer)
    first = path.with_suffix(path.suffix + ".sic.0")
    shutil.copy2(path, first)

def is_valid_html(content):
    class SimpleHTMLValidator(HTMLParser):
        def error(self, message):
            raise Exception(message)
    try:
        parser = SimpleHTMLValidator()
        parser.feed(content)
        return True
    except Exception:
        return False

def is_valid_python(content):
    try:
        ast.parse(content)
        return True
    except Exception:
        return False

def validate_before_save(path, new_content):
    if "# ..." in new_content:
        return False, "Unzulässige Platzhalter gefunden (# ...). Nur vollständigen Code speichern, keine Code-Fragmente (keine Säge)"
    if "#" in new_content:
        return False, "Unzulässige Platzhalter gefunden (# ...). Nur vollständigen Code speichern, keine Code-Fragmente (keine Säge)"
    if path.endswith(".html") and not is_valid_html(new_content):
        return False, "Invalid HTML syntax. Nur vollständigen Code speichern, keine Code-Fragmente (keine Säge)"
    if path.endswith(".py") and not is_valid_python(new_content):
        return False, "Invalid Python syntax. Nur vollständigen Code speichern, keine Code-Fragmente (keine Säge)"
    return True, "OK"

def restore_backup(filepath, version=0):
    path = Path(filepath)
    backup = path.with_suffix(path.suffix + f".sic.{version}")
    if backup.exists():
        shutil.copy2(backup, path)
        return True
    return False