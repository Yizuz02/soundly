from django import template

register = template.Library()

@register.filter
def format_duration_ms(duration_ms):
    if duration_ms:
        seconds = duration_ms // 1000
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"
    return "0:00"
