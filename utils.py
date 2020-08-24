"""Utility functions."""
from datetime import timedelta


def compute_reminder_time(rem_number):
    """Returns time after which reminder will be sent."""
    if rem_number == 1:
        return timedelta(seconds=10)
    elif rem_number == 2:
        return timedelta(seconds=11)
    elif rem_number == 3:
        return timedelta(seconds=13)
    elif rem_number == 4:
        return timedelta(seconds=14)
    elif rem_number == 5:
        return timedelta(seconds=20)
    elif rem_number == 6:
        return timedelta(seconds=24)
    else:
        return None

def parse_markdown_v2(text, mode):
    special_characters = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#',
                          '+', '-', '=', '|', '{', '}', '.', '!' ]
    if mode == 'escape':
        for character in special_characters:
            text = text.replace(character, f'\{character}')
    elif mode == 'convert_back':
        for character in special_characters:
            text = text.replace(f'\{character}', f'{character}')

    return text

