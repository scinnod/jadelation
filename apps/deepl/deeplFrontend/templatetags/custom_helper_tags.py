import os
import markdown
from pathlib import Path
from django.conf import settings
from django.template import Library
from django.urls import translate_url
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

register = Library()

@register.simple_tag(takes_context=True)
def change_lang(context, lang=None, *args, **kwargs):
    path = context['request'].path
    return translate_url(path,lang)


@register.simple_tag
def load_about_content():
    """
    Load and render markdown content for the 'About' section.
    Looks for language-specific files (e.g., about_en.md, about_de.md)
    in the ABOUT_CONTENT_DIR directory.
    Falls back to about_en.md if language-specific file not found.
    """
    # Get current language (e.g., 'en', 'de')
    lang = get_language()
    if lang:
        lang = lang.split('-')[0]  # Convert 'en-us' to 'en'
    else:
        lang = 'en'
    
    # Get content directory from settings
    # Default: /app/data/abou
    content_dir = Path('/app/data/about')
    
    # Try language-specific file first
    md_file = content_dir / f'about_{lang}.md'
    
    # Fall back to English if language-specific file doesn't exist
    if not md_file.exists():
        md_file = content_dir / 'about_en.md'
    
    # If still not found, return a default message
    if not md_file.exists():
        return mark_safe(
            '<p><em>About content not configured. '
            f'Please create {md_file} to customize this section.</em></p>'
        )
    
    try:
        # Read and render markdown
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['extra', 'nl2br', 'sane_lists']
        )
        
        return mark_safe(html_content)
    except Exception as e:
        return mark_safe(
            f'<p><em>Error loading about content: {e}</em></p>'
        )
