from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ICON_PATHS = {
    'home': '<path d="m3 10 9-7 9 7"/><path d="M5 9v11h14V9M9 20v-6h6v6"/>',
    'building': '<path d="M4 21V5l8-3 8 3v16"/><path d="M9 9h1m4 0h1m-6 4h1m4 0h1m-6 4h6"/>',
    'users': '<circle cx="9" cy="8" r="3"/><path d="M3 20v-2a5 5 0 0 1 5-5h2a5 5 0 0 1 5 5v2M16 4a3 3 0 0 1 0 6m2 3a4 4 0 0 1 3 4v2"/>',
    'file': '<path d="M5 2h10l4 4v16H5z"/><path d="M14 2v5h5M8 12h8m-8 4h6"/>',
    'check': '<path d="m5 12 4 4L19 6"/>',
    'bell': '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    'help': '<circle cx="12" cy="12" r="9"/><path d="M9.8 9a2.3 2.3 0 1 1 3.3 2c-1.1.5-1.1 1.2-1.1 2M12 17h.01"/>',
    'grid': '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    'search': '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    'chevron': '<path d="m9 18 6-6-6-6"/>',
    'chevron-down': '<path d="m6 9 6 6 6-6"/>',
    'arrow': '<path d="M5 12h14m-5-5 5 5-5 5"/>',
    'bed': '<path d="M3 19v-9m18 9v-6a3 3 0 0 0-3-3H8v9M3 15h18"/><path d="M8 10V7H5a2 2 0 0 0-2 2v1"/>',
    'chart': '<path d="M4 20V10m6 10V4m6 16v-7m5 7H2"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'shield': '<path d="M12 2 4 5v6c0 5 3.4 9 8 11 4.6-2 8-6 8-11V5z"/><path d="m8 12 3 3 5-6"/>',
    'menu': '<path d="M4 7h16M4 12h16M4 17h16"/>',
    'close': '<path d="m6 6 12 12M18 6 6 18"/>',
    'logout': '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4m7 14 5-5-5-5m5 5H9"/>',
    'download': '<path d="M12 3v12m-4-4 4 4 4-4"/><path d="M4 19h16"/>',
    'filter': '<path d="M3 5h18l-7 8v6l-4 2v-8z"/>',
    'spark': '<path d="m12 3 1.2 4.2L17 9l-3.8 1.8L12 15l-1.2-4.2L7 9l3.8-1.8z"/><path d="m19 15 .7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7z"/>',
    'more': '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
    'pin': '<path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0"/><circle cx="12" cy="10" r="2.5"/>',
    'book': '<path d="M4 4h12a3 3 0 0 1 3 3v13H7a3 3 0 0 1-3-3z"/><path d="M7 4v16"/>',
    'settings': '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    'clipboard': '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2h6v2M9 10h6m-6 4h6"/>',
    'list': '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
}

@register.simple_tag
def icon(name, size=18):
    path_data = ICON_PATHS.get(name, '')
    svg = f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{path_data}</svg>'
    return mark_safe(svg)

@register.simple_tag
def logo_icon(size=36):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{size}" height="{size}" role="img" aria-label="Nestora" style="display: block; border-radius: 10px; overflow: hidden; flex-shrink: 0;">
    <rect width="64" height="64" rx="16" fill="#24493B"/>
    <path d="M11 30 L32 10 L53 30 V50 Q53 54 49 54 H15 Q11 54 11 50 Z" fill="#D4F56B" stroke="#D4F56B" stroke-width="3" stroke-linejoin="round"/>
    <circle cx="25" cy="34" r="5" fill="#24493B"/>
    <path d="M15.5 52 Q15.5 42.5 25 42.5 Q34.5 42.5 34.5 52 Z" fill="#24493B"/>
    <circle cx="39.5" cy="34" r="5" fill="#24493B" stroke="#D4F56B" stroke-width="2.2"/>
    <path d="M30 52 Q30 42.5 39.5 42.5 Q49 42.5 49 52 Z" fill="#24493B" stroke="#D4F56B" stroke-width="2.2" stroke-linejoin="round"/>
</svg>'''
    return mark_safe(svg)
