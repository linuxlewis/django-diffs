from django.conf import settings

DEFAULTS = {
    'redis': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
    },
    'max_element_age': 60*60,
    'use_transactions': True,
    'test_mode': False
}

USER_SETTINGS = getattr(settings, 'DIFFS_SETTINGS', None)


def merge_settings(defaults, user_settings):

    merged = {}
    merged.update(defaults)

    if not user_settings:
        return merged

    for setting in ('max_element_age', 'use_transactions', 'test_mode'):
        if setting in user_settings:
            merged[setting] = user_settings[setting]

    if 'redis' in user_settings:
        merged['redis'].update(user_settings['redis'])

    return merged

diffs_settings = merge_settings(DEFAULTS, USER_SETTINGS)
