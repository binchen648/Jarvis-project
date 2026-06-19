from pathlib import Path

from .base import *  # noqa: F403, F401

# Use SQLite for testing — no PostgreSQL needed
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {
            'NAME': ':memory:',
        },
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# content app uses postgres-only fields in migrations; skip for test speed
MIGRATION_MODULES = {
    'content': None,
    'trajectory': None,
    'eventbus': None,
    'llm': None,
}
