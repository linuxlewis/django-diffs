SECRET_KEY = 'dog'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'diffs',
    }
}

MIDDLEWARE_CLASSES = []

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'diffs',
    'example'
)

DIFFS_SETTINGS = {
    'use_transactions': False,
    'test_mode': True
}
