import os

DEBUG = False
CACHE_STREAM_URLS = True
CACHE_STREAM_URLS_TTL = 30 * 60  # Seconds
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'

# FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID')
# FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET')
# FACEBOOK_ACCESS_TOKEN = os.environ.get('FACEBOOK_ACCESS_TOKEN')

DEFAULT_EVENT_FAMILY = 'one'

try:
    from local_settings import *
except ImportError:
    pass
else:
    print('imported local settings')
