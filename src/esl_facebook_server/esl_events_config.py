from collections import OrderedDict

ESL_EVENT_FAMILY_DICT = OrderedDict([
    (
        'one',
        {
            'event_domain': 'live.esl-one.com',
            # 'event_path': '/',
            'event_path': '/birmingham',
            'event_id_list': [11092],
            'event_facebook_list': ['WatchESLOne'],
            'weight': 1,
        }
    ),
    (
        'one_alt',
        {
            'event_domain': 'live.esl-one.com',
            'event_path': '/cologne',
            'event_id_list': [11224],
            'event_facebook_list': ['WatchESLOne'],
            'weight': 2,
        }
    ),
    (
        'proleague_csgo',
        {
            'event_domain': 'live.proleague.com',
            'event_path': '/csgo',
            'event_id_list': [4090],
            'event_facebook_list': ['ESLProLeagueCSGO'],
            'weight': 3,
        }
    ),
    (
        'iem',
        {
            'event_domain': 'live.intelextrememasters.com',
            'event_path': '/',
            'event_id_list': [11062],
            'event_facebook_list': ['WatchIEM'],
            'weight': 4,
        }
    ),
])
