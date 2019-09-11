# The MIT License (MIT)
#
# Copyright (c) 2019 Drew Webber (mcdruid)
# Copyright (c) 2019 John Bartkiw
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
import requests
import pafy
from bs4 import BeautifulSoup

from mycroft.audio.services.vlc import VlcService

from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft.skills.core import intent_file_handler
from mycroft.util.log import LOG

from mycroft.audio import wait_while_speaking

# Static values for search requests
base_url = "https://www.youtube.com/results?search_query="

class YoutubeSkill(CommonPlaySkill):

    def __init__(self):
        super().__init__(name="YoutubeSkill")

        self.audio_state = "stopped"  # 'playing', 'stopped'
        self.station_name = None
        self.stream_url = None
        self.mpeg_url = None
        self.process = None
        self.regexes = {}
        self.mediaplayer = VlcService(config={'low_volume': 10, 'duck': True})
        self.audio_state = "stopped"  # 'playing', 'stopped'

    def CPS_match_query_phrase(self, phrase):
        # Look for regex matches starting from the most specific to the least

        # Play <data> internet radio on tune in
        #match = re.search(self.translate_regex('internet_radio_on_tunein'), phrase)
        #if match:
        #    data = re.sub(self.translate_regex('internet_radio_on_tunein'), '', phrase)
        #    LOG.debug("CPS Match (internet_radio_on_tunein): " + data)
        #    return phrase, CPSMatchLevel.EXACT, data
        #
        # Play <data> radio on tune in
        #match = re.search(self.translate_regex('radio_on_tunein'), phrase)
        #if match:
        #    data = re.sub(self.translate_regex('radio_on_tunein'), '', phrase)
        #    LOG.debug("CPS Match (radio_on_tunein): " + data)
        #     return phrase, CPSMatchLevel.EXACT, data

        # Play <data> on youtube
        match = re.search(self.translate_regex('on_youtube'), phrase)
        if match:
            data = re.sub(self.translate_regex('on_youtube'), '', phrase)
            LOG.debug("CPS Match (on_youtube): " + data)
            return phrase, CPSMatchLevel.EXACT, data

        # Play <data> internet radio
        #match = re.search(self.translate_regex('internet_radio'), phrase)
        #if match:
        #    data = re.sub(self.translate_regex('internet_radio'), '', phrase)
        #    LOG.debug("CPS Match (internet_radio): " + data)
        #    return phrase, CPSMatchLevel.CATEGORY, data
        #
        ## Play <data> radio
        #match = re.search(self.translate_regex('radio'), phrase)
        #if match:
        #    data = re.sub(self.translate_regex('radio'), '', phrase)
        #    LOG.debug("CPS Match (radio): " + data)
        #    return phrase, CPSMatchLevel.CATEGORY, data

        return phrase, CPSMatchLevel.GENERIC, phrase

    def CPS_start(self, phrase, data):
        LOG.debug("CPS Start: " + data)
        self.search_youtube(data)

    # Attempt to find the first result matching the query string
    def search_youtube(self, search_term):
        tracklist = []
        res = requests.get(base_url + search_term)
        # TODO: check status code etc...
        html = res.content
        soup = BeautifulSoup(html, 'html.parser')
        vids = soup.findAll(attrs={'class':'yt-uix-tile-link'})
        for vid in vids:
            self.vid_url = vid['href']
            self.vid_name = vid.string
            self.stream_url = self.get_stream_url(self.vid_url)
            self.audio_state = "playing"
            self.speak_dialog("now.playing", {"station": self.vid_name} )
            wait_while_speaking()
            LOG.debug("Found stream URL: " + self.vid_url)

            tracklist.append(self.stream_url)
            self.mediaplayer.add_list(tracklist)
            self.mediaplayer.play()

            return

        # We didn't find any playable stations
        self.speak_dialog("not.found")
        wait_while_speaking()
        LOG.debug("Could not find any results with the query term: " + search_term)

    def get_stream_url(self, youtube_url):
        LOG.debug('pafy processing: https://www.youtube.com' + youtube_url)
        video = pafy.new('https://www.youtube.com' + youtube_url)
        bestaudio = video.getbestaudio()
        return bestaudio.url

    def stop(self):
        if self.audio_state == "playing":
            self.mediaplayer.stop()
            self.mediaplayer.clear_list()
            LOG.debug("Stopping stream")
        self.audio_state = "stopped"
        self.station_name = None
        self.station_id = None
        self.stream_url = None
        return True

# these don't work (yet?)
#
#   def pause(self, message=None):
#       self.mediaplayer.pause()
#
#   def resume(self, message=None):
#       self.mediaplayer.pause()
#
#   def next_track(self, message):
#       self.mediaplayer.next()
#
#   def prev_track(self, message):
#       self.mediaplayer.previous()

    def shutdown(self):
        if self.audio_state == 'playing':
            self.mediaplayer.stop()
            self.mediaplayer.clear_list()

    # Get the correct localized regex
    def translate_regex(self, regex):
        if regex not in self.regexes:
            path = self.find_resource(regex + '.regex')
            if path:
                with open(path) as f:
                    string = f.read().strip()
                self.regexes[regex] = string
        return self.regexes[regex]

def create_skill():
    return YoutubeSkill()
