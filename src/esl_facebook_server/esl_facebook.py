import requests
import re
import urllib.parse
from collections import OrderedDict
from datetime import datetime, timedelta
import operator

from esl_events_config import ESL_EVENT_FAMILY_DICT
import settings

esl_url_root = 'http://api.esl.tv/v1'
# esl_url_root = 'http://cdn1.api.esl.tv/v1'
facebook_graph_url_root = 'https://graph.facebook.com'
esl_event_url = esl_url_root + '/event/bydomainurl?livedomain={esl_event_domain}&liveurl={esl_event_path}'
esl_channel_url = esl_url_root + '/channel/eventchannels?pid={esl_event_id}&hideservice=web'
facebook_graph_page_url = facebook_graph_url_root + '/{facebook_id}?fields=link,username&access_token={facebook_app_id}|{facebook_app_secret}'
facebook_graph_page_live_videos_url = facebook_graph_url_root + '/{facebook_page_username}/live_videos?access_token={facebook_access_token}'
facebook_stream_fetch_url = 'https://www.facebook.com/video/tahoe/async/{facebook_video_id}/?chain=true&isvideo=true&originalmediaid={facebook_video_id}&playerorigin=permalink&playersuborigin=tahoe&ispermalink=true&numcopyrightmatchedvideoplayedconsecutively=0&dpr=1'  # dpr = device pixel ratio

cached_stream_urls = {}

ESL_EVENT_FAMILY_DICT[settings.DEFAULT_EVENT_FAMILY]['weight'] = 0


def get_esl_event(event_family=settings.DEFAULT_EVENT_FAMILY):
    esl_event_dict = ESL_EVENT_FAMILY_DICT.get(event_family)
    if not esl_event_dict:
        return
    esl_event_domain, esl_event_path = esl_event_dict['event_domain'], esl_event_dict['event_path']
    esl_event_json = requests.get(esl_event_url.format(esl_event_domain=esl_event_domain, esl_event_path=esl_event_path)).json()
    try:
        event_id = esl_event_json['items'][0]['pidchannels']
        event_name = esl_event_json['items'][0]['fulltitle']
        if event_id not in esl_event_dict['event_id_list']:
            esl_event_dict['event_id_list'].append(event_id)
        return {
            'event_id': event_id,
            'event_name': event_name,
            'weight': esl_event_dict['weight']
        }
    except LookupError:
        return


def get_esl_events():
    esl_events = []
    for event_family in ESL_EVENT_FAMILY_DICT:
        esl_event = get_esl_event(event_family)
        if esl_event:
            esl_event['event_family'] = event_family
            esl_events.append(esl_event)
    esl_events = sorted(esl_events, key=operator.itemgetter('weight'))
    return esl_events


def get_facebook_stream_url(facebook_video_url):
    headers = {
        'User-Agent': settings.USER_AGENT,
    }
    video_page_text = requests.get(facebook_video_url, headers=headers).text
    video_stream_regex = re.search(r'hd_src:"(.*?)"', video_page_text)
    if video_stream_regex:
        video_stream_probable_url = video_stream_regex.group(1)
        if len(video_stream_probable_url) < 1024:
            return video_stream_probable_url


def get_facebook_stream_url_new(facebook_video_url):
    headers = {
        'User-Agent': settings.USER_AGENT,
    }
    payload = {
        '__user': '0',
        '__a': '1',
        '__req': '1',
        '__be': '-1',
        '__pc': 'PHASED:DEFAULT',
    }
    facebook_video_id = re.search(r'videos/(\d+?)/', facebook_video_url).group(1)
    facebook_stream_fetch_url_final = facebook_stream_fetch_url.format(facebook_video_id=facebook_video_id)
    video_page_text = requests.post(facebook_stream_fetch_url_final, data=payload, headers=headers).text
    video_stream_regex = re.search(r'hd_src":"(.*?)"', video_page_text)
    if video_stream_regex:
        video_stream_probable_url_escaped = video_stream_regex.group(1)
        video_stream_probable_url = re.sub(r'\\/', r'/', video_stream_probable_url_escaped)
        video_stream_probable_url = video_stream_probable_url.encode('ascii').decode('unicode_escape')
        # video_stream_probable_url_escaped  = 'https:\\/\\/video.fhyd2-1.fna.fbcdn.net\\/hvideo-prn1\\/v\\/r-lPyUEfSbxTx9vSfr8wx\\/live-dash\\/dash-abr4\\/2004039446294233.mpd?_nc_rl=AfBNK1QRpcjuyWTi&efg=eyJxZV9ncm91cHMiOnsibGl2ZV9jYWNoZV9wcmltaW5nX3VuaXZlcnNlIjp7ImVuYWJsZWQiOiIxIiwiZm5hX2VuYWJsZWQiOiIwIn19fQ\\u00253D\\u00253D&oh=29cbb9ad717cd5b904fed979dc1c8ab0&oe=5AC9F055'
        # video_stream_probable_url = 'https://video.fhyd2-1.fna.fbcdn.net/hvideo-prn1/v/r-lPyUEfSbxTx9vSfr8wx/live-dash/dash-abr4/2004039446294233.mpd?_nc_rl=AfBNK1QRpcjuyWTi&efg=eyJxZV9ncm91cHMiOnsibGl2ZV9jYWNoZV9wcmltaW5nX3VuaXZlcnNlIjp7ImVuYWJsZWQiOiIxIiwiZm5hX2VuYWJsZWQiOiIwIn19fQ%3D%3D&oh=29cbb9ad717cd5b904fed979dc1c8ab0&oe=5AC9F055'
        if len(video_stream_probable_url) < 1024:
            return video_stream_probable_url


def facebook_stream_url_fixes(facebook_stream_url):
    # facebook_stream_url += '&_nc_nc=1'
    facebook_stream_url += '&_nc_p_n=2&_nc_p_o=4&_nc_p_rid=live-md_H264&_nc_p_arid=live-md_AAC&_nc_nc=1'
    facebook_stream_url = re.sub('video(.*?).fbcdn.net', 'video.xx.fbcdn.net', facebook_stream_url)
    return facebook_stream_url


def get_video_url_from_embed_html(embed_html):
    embed_regex = re.search(r'href=(.*?)&', embed_html)
    video_url = urllib.parse.unquote(embed_regex.group(1))
    video_id = re.search(r'videos/(\d+?)/', video_url).group(1)
    return video_url, video_id


def fetch_esl_event_streams(esl_event_id):
    esl_facebook_streams = OrderedDict()

    esl_event = None
    for event_family, esl_event_dict in ESL_EVENT_FAMILY_DICT.items():
        if esl_event_id in esl_event_dict['event_id_list']:
            esl_event = esl_event_dict
            break

    esl_event_json = requests.get(esl_channel_url.format(esl_event_id=esl_event_id)).json()
    for stream in esl_event_json:
        if stream.get('service') == 'facebook':
            embed_html = stream.get('override_embedcode')
            if not embed_html:
                continue
            video_url, video_id = get_video_url_from_embed_html(embed_html)
            if not video_id:
                continue
            event_dict = {
                # 'facebook_id': stream.get('account').split('-')[0],
                # 'video_id_alt': stream.get('youtube_video_id'),
                'esl_video_id': stream['uid'],
                'video_id': video_id,
                'video_url': video_url,
                'stream_name': stream.get('name'),
            }
            esl_facebook_streams[video_id] = event_dict

    if esl_event:
        event_facebook_list = esl_event.get('event_facebook_list', [])
        for event_facebook in event_facebook_list:
            facebook_page_live_videos_json = requests.get(facebook_graph_page_live_videos_url.format(
                facebook_page_username=event_facebook,
                facebook_access_token=settings.FACEBOOK_ACCESS_TOKEN)
            ).json()
            for live_video in facebook_page_live_videos_json.get('data', []):
                if live_video.get('status', '') == 'LIVE':
                    video_url, video_id = get_video_url_from_embed_html(live_video['embed_html'])
                    if not video_id:
                        continue
                    if video_id not in esl_facebook_streams:
                        event_dict = {
                            'video_id': video_id,
                            'video_url': 'https://www.facebook.com/{facebook_page_username}/videos/{facebook_video_id}/'.format(facebook_page_username=event_facebook, facebook_video_id=video_id),
                            'stream_name': live_video.get('title', '{} Live'.format(event_facebook)),
                        }
                        esl_facebook_streams[video_id] = event_dict

    final_esl_facebook_streams = []

    for stream_id, stream in esl_facebook_streams.items():
        cached_video_stream_dict = cached_stream_urls.get(stream['video_url'])
        if settings.CACHE_STREAM_URLS and cached_video_stream_dict and datetime.utcnow() - cached_video_stream_dict['dt'] < timedelta(seconds=settings.CACHE_STREAM_URLS_TTL):
            stream['video_stream'] = cached_video_stream_dict['video_stream']
            stream['video_stream_original'] = cached_video_stream_dict['video_stream_original']
            print('{} fetched from cache'.format(stream['video_url']))
        else:
            video_stream_original = get_facebook_stream_url_new(stream['video_url'])
            # if not video_stream_original:
            #     video_stream_original = get_facebook_stream_url(stream['video_url'])
            if video_stream_original:
                video_stream = facebook_stream_url_fixes(video_stream_original)
                stream['video_stream'] = video_stream
                stream['video_stream_original'] = video_stream_original
                cached_stream_urls[stream['video_url']] = {
                    'video_stream': video_stream,
                    'video_stream_original': video_stream_original,
                    'dt': datetime.utcnow(),
                }

        if 'video_stream' in stream:
            if stream['video_stream'] in [e['video_stream'] for e in final_esl_facebook_streams]:
                continue
            final_stream_dict = {}
            final_stream_dict.update(stream)
            final_esl_facebook_streams.append(final_stream_dict)

    print(esl_facebook_streams)
    print(final_esl_facebook_streams)
    return final_esl_facebook_streams


if __name__ == "__main__":
    raise SystemExit(fetch_esl_event_streams(get_esl_event()['event_id']))
