from django import template
from datetime import datetime
from urllib.parse import urlparse, unquote

register = template.Library()

@register.filter
def iso_to_date(value):
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).strftime('%d.%m.%Y')
    except Exception:
        return value

@register.filter
def filesizeformat(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return "?"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if value < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"

@register.filter
def basename(value: str):
    """Return the last path component of a URL."""
    try:
        path = urlparse(value).path
        name = path.rsplit('/', 1)[-1]
        return unquote(name) or value
    except Exception:
        return value


@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key, '')
    except Exception:
        return ''
