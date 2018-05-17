import os

DEBUG = False

# TTL, Refresh, Timeout in Seconds
CACHE_ESL_EVENT_TTL = 2 * 60 * 60
CACHE_ESL_EVENT_REFRESH = 60 * 60
CACHE_ESL_STREAM_TTL = 30 * 60
CACHE_ESL_STREAM_REFRESH = 5 * 60
CACHE_FACEBOOK_TTL = 30 * 60
CACHE_FACEBOOK_REFRESH = 15 * 60
CACHE_FACEBOOK_API_TTL = 2 * 60
CACHE_FACEBOOK_API_RATE_LIMIT = 2 * 60
REQUEST_ESL_TIMEOUT = 16
REQUEST_FACEBOOK_TIMEOUT = 8

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'

REDIS_HOST = 'localhost'
REDIS_PORT = '6379'
REDIS_DB = 0

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
