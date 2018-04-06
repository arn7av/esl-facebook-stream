from collections import OrderedDict

ESL_EVENT_FAMILY_DICT = OrderedDict([
    (
        'one',
        {
            'event_domain': 'live.esl-one.com',
            'event_path': '/',
            'event_id_list': [9510],
            'event_facebook_list': ['WatchESLOne'],
            'weight': 1,
        }
    ),
    (
        'proleague_csgo',
        {
            'event_domain': 'live.proleague.com',
            'event_path': '/csgo',
            'event_id_list': [4090],
            'event_facebook_list': ['ESLProLeagueCSGO'],
            'weight': 2,
        }
    ),
    (
        'iem',
        {
            'event_domain': 'live.intelextrememasters.com',
            'event_path': '/',
            'event_id_list': [8817],
            'event_facebook_list': ['WatchIEM'],
            'weight': 3,
        }
    ),
])
