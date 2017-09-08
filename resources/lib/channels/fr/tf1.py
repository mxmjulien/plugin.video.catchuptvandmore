# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Original work (C) JUL1EN094, SPM, SylvainCecchetto
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import json
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common

# TO DO
# Rework QUALITY
# Replay LCI (Add date, aired, year, fix some elements)

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.addon.initialize_gettext()

URL_ROOT = "http://www.tf1.fr/"
URL_TIME = 'http://www.wat.tv/servertime2/'
URL_TOKEN = 'http://api.wat.tv/services/Delivery'
URL_LIVE_TV = 'https://www.tf1.fr/%s/direct'
URL_LIVE_INFO = 'https://api.mytf1.tf1.fr/live/2/%s'
URL_API_IMAGE = 'http://api.mytf1.tf1.fr/image'

URL_LCI_REPLAY = "http://www.lci.fr/emissions"
URL_LCI_ROOT = "http://www.lci.fr"

SECRET_KEY = 'W3m0#1mFI'
APP_NAME = 'sdk/Iphone/1.0'
VERSION = '2.1.3'
HOSTING_APPLICATION_NAME = 'com.tf1.applitf1'
HOSTING_APPLICATION_VERSION = '7.0.4'
IMG_WIDTH = 640
IMG_HEIGHT = 360


def channel_entry(params):
    """Entry function of the module"""
    if 'root' in params.next:
        return root(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos_categories' in params.next:
        return list_videos_categories(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'live' in params.next:
        return list_live(params)
    elif 'play' in params.next:
        return get_video_url(params)
    return None

#@common.plugin.cached(common.cache_time)
def root(params):
    """Add Replay and Live in the listing"""
    modes = []

    # Add Replay
    modes.append({
        'label' : 'Replay',
        'url': common.plugin.get_url(
            action='channel_entry',
            next='list_shows_1',
            category='%s Replay' % params.channel_name.upper(),
            window_title='%s Replay' % params.channel_name.upper()
        ),
    })

    # Add Live
    if params.channel_name != 'tfou' and params.channel_name != 'xtra':
        modes.append({
            'label' : _('Live TV'),
            'url': common.plugin.get_url(
                action='channel_entry',
                next='live_cat',
                category='%s Live TV' % params.channel_name.upper(),
                window_title='%s Live TV' % params.channel_name.upper()
            ),
        })

    return common.plugin.create_listing(
        modes,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
    )

#@common.plugin.cached(common.cache_time)
def list_shows(params):
    """Build categories listing"""
    shows = []

    if params.channel_name == 'lci':

        file_path = utils.download_catalog(
            URL_LCI_REPLAY,
            params.channel_name + '.html')
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        if params.next == 'list_shows_1':
            programs_soup = root_soup.find(
                'ul',
                attrs={'class': 'topic-chronology-milestone-component'})
            for program in programs_soup.find_all('li'):
                program_url = URL_LCI_ROOT + program.find('a')['href'].encode('utf-8')
                program_name = program.find(
                    'h2',
                    class_='text-block').get_text().encode('utf-8')
                img = program.find_all('source')[0]
                try:
                    img = img['data-srcset'].encode('utf-8')
                except:
                    img = img['srcset'].encode('utf-8')

                img = img.split(',')[0].split(' ')[0]

                shows.append({
                    'label': program_name,
                    'thumb': img,
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        program_url=program_url,
                        next='list_videos',
                        window_title=program_name
                    )
                })
    else:
        url = ''.join((
            URL_ROOT,
            params.channel_name,
            '/programmes-tv'))
        file_path = utils.download_catalog(
            url,
            params.channel_name + '.html')
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        if params.next == 'list_shows_1':
            categories_soup = root_soup.find(
                'ul',
                attrs={'class': 'filters_2 contentopen'})
            for category in categories_soup.find_all('a'):
                category_name = category.get_text().encode('utf-8')
                category_url = category['data-target'].encode('utf-8')

                shows.append({
                    'label': category_name,
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        category=category_url,
                        next='list_shows_2',
                        window_title=category_name
                    )
                })

        elif params.next == 'list_shows_2':
            programs_soup = root_soup.find(
                'ul',
                attrs={'id': 'js_filter_el_container'})
            for program in programs_soup.find_all('li'):
                category = program['data-type'].encode('utf-8')
                if params.category == category or params.category == 'all':
                    program_url = program.find(
                        'div',
                        class_='description')
                    program_url = program_url.find('a')['href'].encode('utf-8')
                    program_name = program.find(
                        'p',
                        class_='program').get_text().encode('utf-8')
                    img = program.find('img')
                    try:
                        img = img['data-srcset'].encode('utf-8')
                    except:
                        img = img['srcset'].encode('utf-8')

                    img = 'http:' + img.split(',')[-1].split(' ')[0]

                    shows.append({
                        'label': program_name,
                        'thumb': img,
                        'url': common.plugin.get_url(
                            action='channel_entry',
                            program_url=program_url,
                            next='list_videos_categories',
                            window_title=program_name
                        )
                    })

    return common.plugin.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )


#@common.plugin.cached(common.cache_time)
def list_videos_categories(params):
    """Build videos categories listing"""
    videos_categories = []
    url = ''.join((
        params.program_url,
        '/videos'))
    program_html = utils.get_webcontent(url)
    program_soup = bs(program_html, 'html.parser')

    filters_1_soup = program_soup.find(
        'ul',
        class_='filters_1')
    for li in filters_1_soup.find_all('li'):
        category_title = li.get_text().encode('utf-8')
        category_id = li.find('a')['data-filter'].encode('utf-8')
        videos_categories.append({
            'label': category_title,
            'url': common.plugin.get_url(
                action='channel_entry',
                program_url=params.program_url,
                next='list_videos',
                window_title=category_title,
                category_id=category_id
            )
        })
    return common.plugin.create_listing(
        videos_categories,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )


#@common.plugin.cached(common.cache_time)
def list_videos(params):
    """Build videos listing"""
    videos = []

    if params.channel_name == 'lci':
        program_html = utils.get_webcontent(params.program_url)
        program_soup = bs(program_html, 'html.parser')

        list_replay = program_soup.find_all(
            'a',
            class_='topic-emission-extract-block-image trackXiti')

        for replay in list_replay:

            title = replay.find_all('img')[0].get('alt').encode('utf-8')
            duration = 0
            img = replay.find_all('source')[0]
            try:
                img = img['data-srcset'].encode('utf-8')
            except:
                img = img['srcset'].encode('utf-8')

            img = img.split(',')[0].split(' ')[0]
            program_id = URL_LCI_ROOT + replay.get('href').encode('utf-8')

            info = {
                'video': {
                    'title': title,
                    #'plot': stitle,
                    #'aired': aired,
                    #'date': date,
                    'duration': duration,
                    #'year': int(aired[:4]),
                    'mediatype': 'tvshow'
                }
            }

            context_menu = []
            download_video = (
                _('Download'),
                'XBMC.RunPlugin(' + common.plugin.get_url(
                    action='download_video',
                    program_id=program_id) + ')'
            )
            context_menu.append(download_video)

            videos.append({
                'label': title,
                'thumb': img,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    next='play_r',
                    program_id=program_id,
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })

    else:
        url = ''.join((
            params.program_url,
            '/videos/',
            '?filter=',
            params.category_id))
        program_html = utils.get_webcontent(url)
        program_soup = bs(program_html, 'html.parser')

        grid = program_soup.find(
            'ul',
            class_='grid')

        for li in grid.find_all('li'):
            video_type_string = li.find(
                'div', class_='description').find('a')['data-xiti-libelle'].encode('utf-8')
            video_type_string = video_type_string.split('-')[0]

            if 'Playlist' not in video_type_string:
                title = li.find(
                    'p',
                    class_='title').get_text().encode('utf-8')

                try:
                    stitle = li.find(
                        'p',
                        class_='stitle').get_text().encode('utf-8')
                except:
                    stitle = ''

                try:
                    duration_soup = li.find(
                        'p',
                        class_='uptitle').find(
                            'span',
                            class_='momentDate')
                    duration = int(duration_soup.get_text().encode('utf-8'))
                except:
                    duration = 0

                img = li.find('img')
                try:
                    img = img['data-srcset'].encode('utf-8')
                except:
                    img = img['srcset'].encode('utf-8')

                img = 'http:' + img.split(',')[-1].split(' ')[0]

                try:
                    date_soup = li.find(
                        'div',
                        class_='text').find(
                            'p',
                            class_='uptitle').find('span')

                    aired = date_soup['data-date'].encode('utf-8').split('T')[0]
                    day = aired.split('-')[2]
                    mounth = aired.split('-')[1]
                    year = aired.split('-')[0]
                    date = '.'.join((day, mounth, year))
                    # date : string (%d.%m.%Y / 01.01.2009)
                    # aired : string (2008-12-07)

                except:
                    date = ''
                    aired = ''
                    year = 0

                program_id = li.find('a')['href'].encode('utf-8')

                info = {
                    'video': {
                        'title': title,
                        'plot': stitle,
                        'aired': aired,
                        'date': date,
                        'duration': duration,
                        'year': int(aired[:4]),
                        'mediatype': 'tvshow'
                    }
                }

                context_menu = []
                download_video = (
                    _('Download'),
                    'XBMC.RunPlugin(' + common.plugin.get_url(
                        action='download_video',
                        program_id=program_id) + ')'
                )
                context_menu.append(download_video)

                videos.append({
                    'label': title,
                    'thumb': img,
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        next='play_r',
                        program_id=program_id,
                    ),
                    'is_playable': True,
                    'info': info,
                    'context_menu': context_menu
                })

    return common.plugin.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_DURATION,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows')

#@common.plugin.cached(common.cache_time)
def list_live(params):
    """Build live listing"""
    lives = []

    file_path = utils.download_catalog(
        URL_LIVE_INFO % params.channel_name,
        '%s_info_live.json' % (params.channel_name)
    )
    file_info_live = open(file_path).read()
    json_parser = json.loads(file_info_live)

    title = json_parser["current"]["title"].encode('utf-8') + ' - ' \
        + json_parser["current"]["episode"].encode('utf-8')
    if "description" in json_parser["current"]:
        plot = json_parser["current"]["humanStartDate"].encode('utf-8') + ' - ' \
            + json_parser["current"]["humanEndDate"].encode('utf-8') \
            + '\n ' + json_parser["current"]["description"].encode('utf-8')
    else:
        plot = json_parser["current"]["humanStartDate"].encode('utf-8') + ' - ' \
            + json_parser["current"]["humanEndDate"].encode('utf-8')

    duration = 0
    #duration = json_parser["videoJsonPlayer"]["videoDurationSeconds"]

    # Get Image (Code java found in a Forum)
    id_image = json_parser["current"]["image"].encode('utf-8')
    value_md5 = common.sp.md5(str(IMG_WIDTH) + str(IMG_HEIGHT) + id_image \
        + 'elk45sz6ers68').hexdigest()
    value_md5 = value_md5[:6]
    try:
        img = URL_API_IMAGE + '/' + str(IMG_WIDTH)  + '/' + str(IMG_HEIGHT) + '/' \
            + id_image + '/' + str(value_md5)
    except:
        img = ''

    info = {
        'video': {
            'title': title,
            'plot': plot,
            'duration': duration
        }
    }

    lives.append({
        'label': title,
        'fanart': img,
        'thumb': img,
        'url' : common.plugin.get_url(
            action='channel_entry',
            next='play_l',
        ),
        'is_playable': True,
        'info': info
    })


    return common.plugin.create_listing(
        lives,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )

#@common.plugin.cached(common.cache_time)
def get_video_url(params):
    """Get video URL and start video player"""

    if params.next == 'play_r' or params.next == 'download_video':
        if "http" not in params.program_id:
            if params.program_id[0] == '/':
                params.program_id = params.program_id[1:]
            url = URL_ROOT + params.program_id
        else:
            url = params.program_id
        video_html = utils.get_webcontent(url)
        video_html_soup = bs(video_html, 'html.parser')

        iframe_player_soup = video_html_soup.find(
            'div',
            class_='iframe_player')

        if params.channel_name == 'lci':
            video_id = iframe_player_soup['data-watid'].encode('utf-8')
        else:
            data_src = iframe_player_soup['data-src'].encode('utf-8')
            video_id = data_src[-8:]

        timeserver = str(utils.get_webcontent(URL_TIME))

        auth_key = '%s-%s-%s-%s-%s' % (
            video_id,
            SECRET_KEY,
            APP_NAME,
            SECRET_KEY,
            timeserver
        )

        auth_key = common.sp.md5(auth_key).hexdigest()
        auth_key = auth_key + '/' + timeserver

        post_data = {
            'appName': APP_NAME,
            'method': 'getUrl',
            'mediaId': video_id,
            'authKey': auth_key,
            'version': VERSION,
            'hostingApplicationName': HOSTING_APPLICATION_NAME,
            'hostingApplicationVersion': HOSTING_APPLICATION_VERSION
        }

        url_video = utils.get_webcontent(
            url=URL_TOKEN,
            request_type='post',
            post_dic=post_data)
        url_video = json.loads(url_video)
        url_video = url_video['message'].replace('\\', '')

        desired_quality = common.plugin.get_setting('quality')

        if desired_quality == 'BEST' or desired_quality == 'DIALOG':
            try:
                url_video = url_video.split('&bwmax')[0]
            except:
                pass

        return url_video

    elif params.next == 'play_l':

        # Video_ID 'L_%CHANNEL_NAME%'
        video_id = 'L_%s' % params.channel_name.upper()
        real_channel = params.channel_name

        timeserver = str(utils.get_webcontent(URL_TIME))

        auth_key = '%s-%s-%s-%s-%s' % (
            video_id,
            SECRET_KEY,
            APP_NAME,
            SECRET_KEY,
            timeserver
        )

        auth_key = common.sp.md5(auth_key).hexdigest()
        auth_key = auth_key + '/' + timeserver

        post_data = {
            'appName': APP_NAME,
            'method': 'getUrl',
            'mediaId': video_id,
            'authKey': auth_key,
            'version': VERSION,
            'hostingApplicationName': HOSTING_APPLICATION_NAME,
            'hostingApplicationVersion': HOSTING_APPLICATION_VERSION
        }

        url_video = utils.get_webcontent(
            url=URL_TOKEN,
            request_type='post',
            post_dic=post_data)
        url_video = json.loads(url_video)
        url_video = url_video['message'].replace('\\', '')

        desired_quality = common.plugin.get_setting('quality')

        if desired_quality == 'BEST' or desired_quality == 'DIALOG':
            try:
                url_video = url_video.split('&bwmax')[0]
            except:
                pass

        return url_video
