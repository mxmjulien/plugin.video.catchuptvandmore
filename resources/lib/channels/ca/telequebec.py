# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

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

import re
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common

# TO DO
# Add info LIVE TV, Replay

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

URL_ROOT = 'http://zonevideo.telequebec.tv'

URL_LIVE = 'https://player.telequebec.tv/Tq_VideoPlayer.js'

URL_EMISSIONS = URL_ROOT + '/a-z/'

URL_STREAM = 'https://mnmedias.api.telequebec.tv/m3u8/%s.m3u8'
# VideoId

def channel_entry(params):
    """Entry function of the module"""
    if 'root' in params.next:
        return root(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'live' in params.next:
        return list_live(params)
    elif 'play' in params.next:
        return get_video_url(params)
    return None

@common.PLUGIN.mem_cached(common.CACHE_TIME)
def root(params):
    """choose mode"""
    modes = []

    # Add Replay
    modes.append({
        'label': 'Replay',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='list_shows_1',
            category='%s Replay' % params.channel_name.upper(),
            window_title='%s Replay' % params.channel_name.upper()
        ),
    })

    # Add Live
    modes.append({
        'label': 'Live TV',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='live_cat',
            category='%s Live TV' % params.channel_name.upper(),
            window_title='%s Live TV' % params.channel_name.upper()
        ),
    })

    return common.PLUGIN.create_listing(
        modes,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
        category=common.get_window_title()
    )

@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    if params.next == 'list_shows_1':

        replay_categories_html = utils.get_webcontent(URL_EMISSIONS)
        replay_categories_soup = bs(replay_categories_html, 'html.parser')
        categories = replay_categories_soup.find(
            'div', class_='list').find_all('li')

        for category in categories:

            category_name = category.find('a').get_text()
            category_url = URL_ROOT + category.find(
                "a").get("href")
            shows.append({
                'label': category_name,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    category_url=category_url,
                    category_name=category_name,
                    next='list_videos_1',
                    window_title=category_name
                )
            })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []

    if params.next == 'list_videos_1':
        list_videos_html = utils.get_webcontent(
            params.category_url)
        list_videos_soup = bs(list_videos_html, 'html.parser')

        videos_data = list_videos_soup.find_all(
            'div', class_='item')

        for video in videos_data:

            title = video.find('h4').get_text()
            plot = video.find('p').get_text()
            duration = 0
            img = video.find('img').get('src')
            video_id = video.get('data-mediaid')

            info = {
                'video': {
                    'title': title,
                    'plot': plot,
                    # 'aired': aired,
                    # 'date': date,
                    'duration': duration,
                    # 'year': year,
                    'mediatype': 'tvshow'
                }
            }

            download_video = (
                _('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    video_id=video_id) + ')'
            )
            context_menu = []
            context_menu.append(download_video)

            videos.append({
                'label': title,
                'thumb': img,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='play_r',
                    video_id=video_id,
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows',
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_live(params):
    """Build live listing"""
    lives = []

    title = ''
    plot = ''
    duration = 0
    img = ''
    url_live = ''


    title = params.channel_name + ' Live TV'
    live_html = utils.get_webcontent(URL_LIVE)
    url_live = re.compile(
        r'm3U8Url:"(.*?)"').findall(live_html)[0]

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
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='play_l',
            url=url_live,
        ),
        'is_playable': True,
        'info': info
    })

    return common.PLUGIN.create_listing(
        lives,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':
        return URL_STREAM % params.video_id
    elif params.next == 'play_l':
        return params.url
