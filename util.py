"""Utility functions for Menjin integration."""

from pypinyin import lazy_pinyin


def to_pinyin(text: str) -> str:
    """Convert Chinese text to pinyin with underscores."""
    return "_".join(lazy_pinyin(text))


def to_initials(text: str) -> str:
    """Convert Chinese text to first letter of each character's pinyin."""
    pinyin_list = lazy_pinyin(text)
    return "".join([p[0] for p in pinyin_list if p])


def generate_entity_id(device_name: str, divide_name: str) -> str:
    """Generate entity ID with pinyin conversion.
    
    - divide_name: converted to initials (first letter of each character)
    - device_name: converted to full pinyin
    """
    divide_initials = to_initials(divide_name)
    device_pinyin = to_pinyin(device_name)
    return f"gate_{divide_initials}_{device_pinyin}"
