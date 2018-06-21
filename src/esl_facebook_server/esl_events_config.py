from collections import OrderedDict

ESL_EVENT_FAMILY_DICT = OrderedDict([
    (
        'one_dota',
        {
            'event_domain': 'live.esl-one.com',
            'event_path': '/birmingham',
            'event_id_list': [11092],
            'event_facebook_list': ['WatchESLOne'],
            'weight': 1,
            'active': False,
            'twitch_primary': True,
        }
    ),
    (
        'one_csgo',
        {
            'event_domain': 'live.esl-one.com',
            'event_path': '/cologne',
            'event_id_list': [11224],
            'event_facebook_list': ['ESLOneCSGO'],
            'weight': 2,
            'active': True,
            'twitch_primary': True,
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
            'active': False,
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
            'active': False,
        }
    ),
])
