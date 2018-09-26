import operator
import pickle
import re
import urllib.parse
from collections import OrderedDict

import requests
from walrus import Database

import settings
from esl_events_config import ESL_EVENT_FAMILY_DICT
from cache import RefreshCache

esl_url_root = 'http://api.esl.tv/v1'
# esl_url_root = 'http://cdn1.api.esl.tv/v1'
facebook_graph_url_root = 'https://graph.facebook.com'
esl_event_url = esl_url_root + '/event/bydomainurl?livedomain={esl_event_domain}&liveurl={esl_event_path}'
esl_channel_url = esl_url_root + '/channel/eventchannels?pid={esl_event_id}&hideservice=web'
facebook_graph_page_url = facebook_graph_url_root + '/{facebook_id}?fields=link,username&access_token={facebook_app_id}|{facebook_app_secret}'
facebook_graph_page_live_videos_url = facebook_graph_url_root + '/{facebook_page_username}/live_videos?access_token={facebook_access_token}'
facebook_stream_fetch_url = 'https://www.facebook.com/video/tahoe/async/{facebook_video_id}/?originalmediaid={facebook_video_id}&playerorigin=permalink&playersuborigin=tahoe&ispermalink=true&numcopyrightmatchedvideoplayedconsecutively=0&payloadtype=primary&dpr=1'  # dpr = device pixel ratio
facebook_stream_fetch_identifier_url = 'https://www.facebook.com/video/tahoe/async/{facebook_video_id}/?originalmediaid={facebook_video_id}&playerorigin=permalink&playersuborigin=tahoe&ispermalink=true&numcopyrightmatchedvideoplayedconsecutively=0&payloadtype=all&storyidentifier={identifier}&dpr=1'
facebook_video_embed_url = 'https://www.facebook.com/embedvideo/video.php'

db = Database(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
cache = RefreshCache(db, name='cache', default_timeout=3600)

esl_event_family_dict = ESL_EVENT_FAMILY_DICT


def set_esl_event_family_dict():
    db['esl_event_family_dict'] = pickle.dumps(esl_event_family_dict, pickle.HIGHEST_PROTOCOL)


def get_esl_event_family_dict():
    global esl_event_family_dict
    esl_event_family_dict = pickle.loads(db['esl_event_family_dict'])
    return esl_event_family_dict


esl_event_family_dict[settings.DEFAULT_EVENT_FAMILY]['weight'] = 0
set_esl_event_family_dict()


@cache.conditional_cached(timeout=settings.CACHE_ESL_EVENT_TTL, refresh=settings.CACHE_ESL_EVENT_REFRESH)
def get_esl_event_core(event_family):
    esl_event_dict = esl_event_family_dict[event_family]
    esl_event_domain, esl_event_path = esl_event_dict['event_domain'], esl_event_dict['event_path']
    try:
        esl_event_json = requests.get(esl_event_url.format(
            esl_event_domain=esl_event_domain, esl_event_path=esl_event_path
        ), timeout=settings.REQUEST_ESL_TIMEOUT).json()
    except (requests.exceptions.RequestException, ValueError):
        return None, False
    try:
        event_id = esl_event_json['items'][0]['pidchannels']
        event_name = esl_event_json['items'][0]['fulltitle']
        if event_id not in esl_event_dict['event_id_list']:
            esl_event_dict['event_id_list'].append(event_id)
            set_esl_event_family_dict()
        return {
            'event_id': event_id,
            'event_name': event_name,
        }, True
    except LookupError:
        return None, False


def get_esl_event(event_family=settings.DEFAULT_EVENT_FAMILY):
    esl_event_dict = get_esl_event_family_dict().get(event_family)
    if not esl_event_dict:
        return
    event_ret = get_esl_event_core(event_family)
    if not event_ret:
        event_ret = {
            'event_id': esl_event_dict['event_id_list'][0],
            'event_name': event_family,
        }
    # if event_ret:
    event_ret['weight'] = esl_event_dict['weight']
    event_ret['twitch_primary'] = esl_event_dict.get('twitch_primary', True)
    return event_ret


def get_esl_events():
    esl_events = []
    for event_family, esl_event_dict in get_esl_event_family_dict().items():
        active = esl_event_dict.get('active', True)
        if not active:
            continue
        esl_event = get_esl_event(event_family)
        if esl_event:
            esl_event['event_family'] = event_family
            esl_events.append(esl_event)
    esl_events = sorted(esl_events, key=operator.itemgetter('weight'))
    return esl_events


@cache.conditional_cached(timeout=settings.CACHE_FACEBOOK_TTL, refresh=settings.CACHE_FACEBOOK_REFRESH)
def get_facebook_stream_url_core(facebook_video_url):
    video_stream_original = get_facebook_stream_url_embed(facebook_video_url)
    if not video_stream_original:
        video_stream_original = get_facebook_stream_url_tahoe(facebook_video_url, anon=False)
    if not video_stream_original:
        return None, False
    video_stream = facebook_stream_url_fixes(video_stream_original)
    return {
        'video_stream': video_stream,
        'video_stream_original': video_stream_original,
    }, True


def extract_facebook_stream_url_from_text(video_page_text):
    video_stream_regex = re.search(r'hd_src":"(.*?)"', video_page_text)
    if video_stream_regex:
        video_stream_probable_url_escaped = video_stream_regex.group(1)
        video_stream_probable_url = re.sub(r'\\/', r'/', video_stream_probable_url_escaped)
        video_stream_probable_url = video_stream_probable_url.encode('ascii').decode('unicode_escape')
        # video_stream_probable_url_escaped  = 'https:\\/\\/video.fhyd2-1.fna.fbcdn.net\\/hvideo-prn1\\/v\\/r-lPyUEfSbxTx9vSfr8wx\\/live-dash\\/dash-abr4\\/2004039446294233.mpd?_nc_rl=AfBNK1QRpcjuyWTi&efg=eyJxZV9ncm91cHMiOnsibGl2ZV9jYWNoZV9wcmltaW5nX3VuaXZlcnNlIjp7ImVuYWJsZWQiOiIxIiwiZm5hX2VuYWJsZWQiOiIwIn19fQ\\u00253D\\u00253D&oh=29cbb9ad717cd5b904fed979dc1c8ab0&oe=5AC9F055'
        # video_stream_probable_url = 'https://video.fhyd2-1.fna.fbcdn.net/hvideo-prn1/v/r-lPyUEfSbxTx9vSfr8wx/live-dash/dash-abr4/2004039446294233.mpd?_nc_rl=AfBNK1QRpcjuyWTi&efg=eyJxZV9ncm91cHMiOnsibGl2ZV9jYWNoZV9wcmltaW5nX3VuaXZlcnNlIjp7ImVuYWJsZWQiOiIxIiwiZm5hX2VuYWJsZWQiOiIwIn19fQ%3D%3D&oh=29cbb9ad717cd5b904fed979dc1c8ab0&oe=5AC9F055'
        if len(video_stream_probable_url) < 1024:
            return video_stream_probable_url


def get_facebook_stream_url_tahoe(facebook_video_url, anon=True):
    headers = {
        'User-Agent': settings.USER_AGENT,
    }
    identifier = None
    if anon:
        payload = {
            '__user': '0',
            '__a': '1',
            '__req': '1',
            '__be': '-1',
            '__pc': 'PHASED:DEFAULT',
        }
    else:
        headers['Cookie'] = settings.FACEBOOK_COOKIE
        try:
            dtsg_token_page_text = requests.get(facebook_video_url, headers=headers, timeout=settings.REQUEST_FACEBOOK_TIMEOUT).text
        except requests.exceptions.RequestException:
            return
        dtsg_token_regex = re.search(r'"token":"(.*?)"', dtsg_token_page_text)
        identifier_regex = re.search(r'\?ref=tahoe","(.*?)"', dtsg_token_page_text)
        if not dtsg_token_regex:
            return
        dtsg_token = dtsg_token_regex.group(1)
        if identifier_regex:
            identifier = identifier_regex.group(1)
        payload = {
            '__user': '0',
            '__a': '1',
            '__req': '3',
            '__be': '1',
            '__pc': 'PHASED:DEFAULT',
            'fb_dtsg': dtsg_token,
            '__spin_b': 'trunk',
        }
    facebook_video_id = re.search(r'videos/(\d+?)/', facebook_video_url).group(1)
    if identifier:
        facebook_stream_fetch_url_final = facebook_stream_fetch_identifier_url.format(facebook_video_id=facebook_video_id, identifier=identifier)
    else:
        facebook_stream_fetch_url_final = facebook_stream_fetch_url.format(facebook_video_id=facebook_video_id)
    video_page_text = requests.post(facebook_stream_fetch_url_final, data=payload, headers=headers, timeout=settings.REQUEST_FACEBOOK_TIMEOUT).text
    return extract_facebook_stream_url_from_text(video_page_text)


def get_facebook_stream_url_embed(facebook_video_url):
    headers = {
        'User-Agent': settings.USER_AGENT,
    }
    payload = {
        'href': facebook_video_url
    }
    video_page_text = requests.get(facebook_video_embed_url, params=payload, headers=headers, timeout=settings.REQUEST_FACEBOOK_TIMEOUT).text
    return extract_facebook_stream_url_from_text(video_page_text)


def facebook_stream_url_fixes(facebook_stream_url):
    # facebook_stream_url += '&_nc_nc=1'
    # facebook_stream_url += '&_nc_p_n=2&_nc_p_o=4&_nc_p_rid=live-md_H264&_nc_p_arid=live-md_AAC&_nc_nc=1'
    facebook_stream_url += '&_nc_p_n=2&_nc_p_o=4&_nc_p_rid=live-md-v&_nc_p_arid=live-md-a&_nc_nc=1'
    facebook_stream_url = re.sub('video(.*?).fbcdn.net', 'video.xx.fbcdn.net', facebook_stream_url)
    return facebook_stream_url


def get_video_url_from_embed_html(embed_html):
    embed_regex = re.search(r'href=(.*?)(&|$)', embed_html)
    if not embed_regex:
        return None, None
    video_url = urllib.parse.unquote(embed_regex.group(1))
    if not video_url.endswith('/'):
        video_url += '/'
    video_id = re.search(r'videos/(\d+?)/', video_url).group(1)
    return video_url, video_id


@cache.conditional_cached(timeout=settings.CACHE_ESL_STREAM_TTL, refresh=settings.CACHE_ESL_STREAM_REFRESH)
def get_esl_event_facebook_videos(esl_event_id):
    esl_facebook_videos = OrderedDict()

    try:
        esl_event_live_videos_json = requests.get(esl_channel_url.format(esl_event_id=esl_event_id), timeout=settings.REQUEST_ESL_TIMEOUT).json()
    except (requests.exceptions.RequestException, ValueError):
        return None, False

    for live_video in esl_event_live_videos_json:
        if live_video.get('service') == 'facebook':
            embed_html = live_video.get('override_embedcode')
            if not embed_html:
                continue
            video_url, video_id = get_video_url_from_embed_html(embed_html)
            if not video_id:
                continue
            video_dict = {
                'video_id': video_id,
                'video_url': video_url,
                'stream_name': live_video.get('name'),
                'esl_video_id': live_video['uid'],
            }
            esl_facebook_videos[video_id] = video_dict

    if not len(esl_facebook_videos):
        return None, False

    return {
        'esl_facebook_videos': esl_facebook_videos
    }, True


facebook_api_rate_limit = db.rate_limit('facebook_api_rate_limit', limit=1, per=settings.CACHE_FACEBOOK_API_RATE_LIMIT)


@cache.conditional_cached(timeout=settings.CACHE_FACEBOOK_API_TTL, rate_limit=facebook_api_rate_limit)
def get_facebook_page_facebook_videos(facebook_page_username):
    esl_facebook_videos = OrderedDict()

    try:
        facebook_page_live_videos_json = requests.get(facebook_graph_page_live_videos_url.format(
            facebook_page_username=facebook_page_username, facebook_access_token=settings.FACEBOOK_ACCESS_TOKEN
        ), timeout=settings.REQUEST_FACEBOOK_TIMEOUT).json()
    except (requests.exceptions.RequestException, ValueError):
        return None, False

    for live_video in facebook_page_live_videos_json.get('data', []):
        if live_video.get('status', '') == 'LIVE':
            video_url, video_id = get_video_url_from_embed_html(live_video['embed_html'])
            if not video_id:
                continue
            video_dict = {
                'video_id': video_id,
                'video_url': 'https://www.facebook.com/{facebook_page_username}/videos/{facebook_video_id}/'.format(
                    facebook_page_username=facebook_page_username, facebook_video_id=video_id
                ),
                'stream_name': live_video.get('title', '{} Live'.format(facebook_page_username)),
            }
            esl_facebook_videos[video_id] = video_dict

    if not len(esl_facebook_videos):
        return None, False

    return {
        'esl_facebook_videos': esl_facebook_videos
    }, True


def merge_order_facebook_videos(esl_event_id, esl_event):
    esl_event_facebook_videos_dict = get_esl_event_facebook_videos(esl_event_id)
    esl_facebook_streams = esl_event_facebook_videos_dict['esl_facebook_videos'] if esl_event_facebook_videos_dict else OrderedDict()
    for video_dict in esl_facebook_streams.values():
        video_dict['weight'] = 1

    if esl_event:
        event_facebook_list = esl_event.get('event_facebook_list', [])
        for event_facebook in event_facebook_list:
            facebook_page_facebook_videos_dict = get_facebook_page_facebook_videos(event_facebook)
            esl_facebook_page_videos = facebook_page_facebook_videos_dict['esl_facebook_videos'] if facebook_page_facebook_videos_dict else OrderedDict()
            for video_id, video_dict in reversed(esl_facebook_page_videos.items()):
                if video_id not in esl_facebook_streams:
                    video_dict['weight'] = 5 if settings.PRIORITIZE_FACEBOOK_EXCLUSIVE else 2
                    esl_facebook_streams[video_id] = video_dict
                else:
                    if 'main' in esl_facebook_streams[video_id].get('stream_name', '').lower():
                        esl_facebook_streams[video_id]['weight'] = 4
                    else:
                        esl_facebook_streams[video_id]['weight'] = 3

    esl_facebook_streams_ordered = OrderedDict((k, v) for k, v in sorted(esl_facebook_streams.items(), key=lambda item: item[1]['weight'], reverse=True))
    return esl_facebook_streams_ordered


def fetch_esl_event_streams(esl_event_id):
    esl_event = None
    for event_family, esl_event_dict in get_esl_event_family_dict().items():
        if esl_event_id in esl_event_dict['event_id_list']:
            esl_event = esl_event_dict
            break

    esl_facebook_streams = merge_order_facebook_videos(esl_event_id, esl_event)

    final_esl_facebook_streams = []

    for video_id, video_dict in esl_facebook_streams.items():
        stream_dict = get_facebook_stream_url_core(video_dict['video_url'])
        if stream_dict:
            video_dict.update(stream_dict)

        if 'video_stream' in video_dict:
            # if video_dict['video_stream'] in [e['video_stream'] for e in final_esl_facebook_streams]:
            #     continue
            final_stream_dict = {}
            final_stream_dict.update(video_dict)
            final_esl_facebook_streams.append(final_stream_dict)

    print(esl_facebook_streams)
    print(final_esl_facebook_streams)
    return final_esl_facebook_streams


def get_default_event_family_streams():
    default_event = get_esl_event()
    return fetch_esl_event_streams(default_event['event_id']) if default_event else None


def get_default_event_family_first_stream_url():
    default_event_family_streams = get_default_event_family_streams()
    return default_event_family_streams[0]['video_stream'] if default_event_family_streams else None


if __name__ == "__main__":
    raise SystemExit(get_default_event_family_streams())
