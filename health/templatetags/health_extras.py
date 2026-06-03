from django import template
from datetime import datetime

register = template.Library()


@register.filter
def get_item(mapping, key):
    if hasattr(mapping, "get"):
        return mapping.get(key)
    return None


@register.filter
def is_date_field(field_name):
    if not field_name:
        return False

    normalized = str(field_name).strip().lower()
    return any(keyword in normalized for keyword in ("data", "retorno", "vencimento", "vencem"))


@register.filter
def to_date_input(value):
    if not value:
        return ""

    text = str(value).strip()
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, pattern).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return text
