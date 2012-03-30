# -*- coding: utf-8 -*-

import urllib2
from lxml import etree

from StringIO import StringIO

from beaker.cache import CacheManager
from beaker.cache import cache_regions, cache_region
from beaker.util import parse_cache_config_options

CACHE_DATA_DIR = '/tmp/plugin.video.livestream/cache/data'
CACHE_LOCK_DIR = '/tmp/plugin.video.livestream/cache/lock'


#TODO: FIXME: add a more regions (forever, weekly, daily, yearly), get_game_list for example could probably be cached
#             for a substantial length of time (yearly, monthly at most) -> fine tuning
#             add functions for invalidating to force refresh
cache_regions.update({
    'short_term':{
        'expire' : 60,
        'type' : 'memory',
        'key_length' : 250,
        'data_dir' : CACHE_DATA_DIR,
        'lock_dir' : CACHE_LOCK_DIR
    },
    'long_term':{
        'expire' : 1800,
        'type' : 'file',
        'key_length' : 250,
        'data_dir' : CACHE_DATA_DIR,
        'lock_dir' : CACHE_LOCK_DIR
    }
})

#cache_opts = {
#    'cache.type': 'file',
#    'cache.data_dir': CACHE_DATA_DIR,
#    'cache.lock_dir': CACHE_LOCK_DIR,
#    'key_length' : 250
#}
#cache = CacheManager(**parse_cache_config_options(cache_opts))

class StreamObject(object):
    '''
        Datacontainer representing a stream item
        TODO:FIXME: create a complete standardized (non-site specific set of fields)
    '''
    
    def __init__(self):
        super(StreamObject, self).__init__()
        self.title = None
        self.description = None
        self.game = None
        self.viewers = None
        self.thumbnail_url = None
        self.stream_url = None
        self.stream_id = None
        self.rtmp_url = None
    
    def __str__(self):
        return "<StreamObject : %s, stream_id : %s, game : %s>" % (self.title, str(self.stream_id), self.game)

class Parser(object):
    '''
        Base class for parsers

        Provides utility functions for scraping and parsing
    '''

    USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14'

    def __init__(self):
        super(Parser, self).__init__()

    @cache_region('short_term', 'get_response_data')
    def get_response_data(self, url, postdata = ''):
        request = urllib2.Request(url, postdata)
        request.add_header('User-Agent', self.USER_AGENT)
        
        response = urllib2.urlopen(request)
        raw_data = response.read()
        
        response.close() #TODO:FIXME: needed?
        
        return raw_data

class Own3dParser(Parser):
    '''
        Parser for Own3d.tv

        Provides functions for getting live streams (RTMP) 
        and archive videos (MPEG4) using the own3d.tv api
        
        TODO:FIXME: Should be extracted to a separate module since it's gotten pretty lengthy now.
    '''

    #TODO:FIXME: Should find a better method to represent these static values, enums or something (or just classes with static fields)
    LIST_LIVE_STREAMS_URL = 'http://api.own3d.tv/live'
    LIST_GAMES_URL = 'http://www.own3d.tv/browse' 
    LIST_ARCHIVE_URL = 'http://api.own3d.tv/api.php'
    
    LIVE_STREAM_CONFIG_URL = 'http://www.own3d.tv/livecfg/%d'
    ARCHIVE_VIDEO_URL = 'http://www.own3d.tv/video/%d'
    
    TYPE_ALL = 'all'
    TYPE_LIVE = 'live'
    TYPE_VIDEOS = 'videos'

    SYSTEM_PS3 = 'Sony Playstation 3'
    SYSTEM_PC = 'PC'
    SYSTEM_WII = 'Nintendo Wii'
    SYSTEM_XBOX_360 = 'Microsoft XBOX 360'

    #TODO:FIXME: This is where an enum/static data class would be nice.
    SYSTEM_IDS = {
        SYSTEM_PS3 : 3,
        SYSTEM_PC : 1,
        SYSTEM_WII : 5,
        SYSTEM_XBOX_360 : 2
    }

    GENRE_ADVENTURE = 'Adventure'
    GENRE_MMORPG = 'MMORPG'
    GENRE_MOBA = 'MOBA'
    GENRE_RACING = 'Racing'
    GENRE_ROLE_PLAYING = 'Role Playing'
    GENRE_SHOOTER = 'Shooter'
    GENRE_SIMULATION = 'Simulation'
    GENRE_SPORTS = 'Sports'
    GENRE_STRATEGY = 'Strategy'

    GENRE_IDS = {
        GENRE_ADVENTURE : 2,
        GENRE_MMORPG : 10,
        GENRE_MOBA : 14,
        GENRE_RACING : 9,
        GENRE_ROLE_PLAYING : 4,
        GENRE_SHOOTER : 1,
        GENRE_SIMULATION : 6,
        GENRE_SPORTS : 5,
        GENRE_STRATEGY : 7
    }

    TIME_ANYTIME = 'anytime'
    TIME_TODAY = 'today'
    TIME_WEEK = 'week'
    TIME_MONTH = 'month'

    SORT_METHOD_VIEWS = 'views'
    SORT_METHOD_RELEVANCE = 'relevance'
    SORT_METHOD_DATE = 'date'
    
    def __init__(self):
        super(Own3dParser, self).__init__()

    def get_archive_videos(self, archive_type=TYPE_VIDEOS, game_name=None, date=TIME_ANYTIME, sort_by=SORT_METHOD_VIEWS, genre_name=None, system_name=None):
        game_list = self.get_game_list()
        if not game_list.has_key(game_name):
            #TODO:FIXME: create a NoSuchGame/GameNotSupported Exception class
            raise KeyError('No game found for game name : %s' % game_name)

        system_id = None
        if system_name:
            try:
                system_id = SYSTEM_IDS[system_name]
            except KeyError, e:
                message = 'Could not find system id for system name : %s , exception : %s' % (system_name, str(e))
                #log.warn(message)
                #log.error(message, e)
                print message

        return self._get_archive_videos(archive_type, game_name, date, sort_by, genre_name, system_id)

    @cache_region('short_term', 'get_archive_videos')
    def _get_archive_videos(self, archive_type, game_name, date, sort_by, genre_name, system_id):
        query = '?search=&type=%s&time=%s&sort=%s' % (archive_type, date, sort_by)
        
        if system_id:
            query += '&system=%d' % system_id
        
        if game_name:
            #TODO:FIXME: refactor to a util class, 'sanitize_for_request' or something
            game_name = game_name.lstrip()
            game_name = game_name.rstrip()
            game_name = game_name.replace(' ', '+')
            game_name = urllib2.unquote(game_name)
            
            query += '&search_game=%s' % game_name

        if genre_name:
            query += '&genre_id=%s' % GENRE_IDS[genre_name]

        url = self.LIST_ARCHIVE_URL + query
        print 'url : %s' % url
        
        raw_xml = self.get_response_data(url)
        xml_root = etree.XML(raw_xml)
        items_xpath = etree.XPath('//item')

        return raw_xml

    @cache_region('short_term', 'get_archive_video_url')
    def get_archive_video_url(self, video_id):
        raw_html = self.get_response_data(self.ARCHIVE_VIDEO_URL % video_id)

        import re
        #TODO:FIXME: extract regex search to a utility function in Parser
        # queryString : escape('?7418afca70ba1dc09fb6b6e37c287072169117b285d7dfcce5f8d90b455933d780e9&ec_seek=${start}&ec_rate=350&ec_prebuf=5')
        query_pattern = re.compile('escape\(\'\?(.+?)&')
        # HQUrl: 'videos/SD/318000/318858_4edc05c491748_HQ.mp4'
        hqurl_pattern = re.compile('HQUrl: \'(videos/.*?\\.mp4)\'')
        # HDUrl: 'videos/HD/227000/227488_4e8ce41b8e3f8_HD.mp4'
        hdurl_pattern = re.compile('HDUrl: \'(videos/.*?\\.mp4)\'')
        
        query_string = query_pattern.findall(raw_html)
        query_string = query_string[0] if len(query_string) > 0 else None
        
        hqurl = hqurl_pattern.findall(raw_html)
        hqurl = hqurl[0] if len(hqurl) > 0 else None

        hdurl = hdurl_pattern.findall(raw_html)
        hdurl = hdurl[0] if len(hdurl) > 0 else None

        print 'hqurl : %s , hdurl : %s ' % (hqurl, hdurl)
        mpeg4_url = hdurl if hdurl else hqurl
        print 'mpeg4_url : %s' % mpeg4_url
        if not mpeg4_url:
            #TODO:FIXME: implement logging
            #log.warn('Could not find video for id : %d' % video_id)
            return None

        video_url = 'http://vodcdn.ec.own3d.tv/%s?%s' % (mpeg4_url, query_string)
        return video_url

    @cache_region('long_term', 'get_game_list')
    def get_game_list(self):
        #TODO: FIXME: maybe parse the category anchors as well, will be able to browse by letter/number
        raw_html = self.get_response_data(self.LIST_GAMES_URL)
        
        html_parser = etree.HTMLParser()
        html_tree = etree.parse(StringIO(raw_html), html_parser)

        game_links = html_tree.xpath('//a[re:test(string(@href), "^/game/[\w+]*$", "i")]', namespaces={'re' : 'http://exslt.org/regular-expressions'})
        
        game_list = { game_link.text : 'http://www.own3d.tv' + game_link.attrib['href'] for game_link in game_links }
        return game_list

    @cache_region('short_term', 'get_live_streams')
    def get_live_streams(self, game):
        raw_xml = self.get_response_data(self.LIST_LIVE_STREAMS_URL)
        xml_root = etree.XML(raw_xml)
        
        stream_list = []
        #TODO:FIXME: all such xpath searches should be done in a utility function
        channels_xpath = etree.XPath('//item[misc[@game = "%s"]]' % game)
        for items in channels_xpath(xml_root):
            stream_object = StreamObject()
            for item in list(items):
                if item.tag == 'title':
                    stream_object.title = item.text
                if item.tag == 'misc':
                    stream_object.game = item.get('game')
                    stream_object.viewers = int(item.get('viewers'))
                if item.tag == 'description':
                    stream_object.description = item.text
                if item.tag == 'thumbnail':
                    stream_object.thumbnail_url = item.text
                if item.tag == 'embed':
                    stream_url = item.text
                    stream_object.stream_url = stream_url
                    stream_object.stream_id = stream_url.split('/')[-1]
            stream_list.append(stream_object)
        
        return stream_list

    @cache_region('short_term', 'get_rtmp_url')
    def get_rtmp_url(self, stream_id):
        raw_xml =  self.get_response_data(self.LIVE_STREAM_CONFIG_URL % stream_id)
        xml_root = etree.XML(raw_xml)

        channel_xpath = etree.XPath('//channel')
        channel_element = channel_xpath(xml_root)[0]

        channel_info = {}
        channel_info['name'] = channel_element.attrib.get('name')
        channel_info['description'] = channel_element.attrib.get('description')
        channel_info['owner'] = channel_element.attrib.get('owner')
        channel_info['nameLink'] = channel_element.attrib.get('nameLink')
        channel_info['descriptionLink'] = channel_element.attrib.get('descriptionLink')
        channel_info['ownerLink'] = channel_element.attrib.get('ownerLink')

        items_xpath = etree.XPath('//item')
        item = items_xpath(channel_element)[0]
        
        stream_item_xpath = etree.XPath('//stream')
        stream_item = stream_item_xpath(item)[0]
        
        
        '''
            possible rtmp servers
            rtmp://own3duslivefs.fplive.net/own3duslive-live <- almost never works, even though specified in livecfg.
            rtmp://own3deulivefs.fplive.net/own3deulive-live <- almost never works, even though specified in livecfg.
            rtmp://fml.2010.edgecastcdn.net:1935/202010 <- pretty stable.
            rtmp://owned.fc.llnwd.net:1935/owned <- pretty stable.
            
            problem is masked servers (${cdn1}, ${cdn2}), right now just guessing on one random edgecast cdn
            
            could probably retry on all known servers, but that would be really slow.
            
            from http://bogy.mine.nu/sc2/stream2vlc.php , with channel id : 33356 (chaox) , hoster : own3d.tv
            "C:\rtmpdump-2.3\rtmpdump.exe" -r "rtmp://own3duslivefs.fplive.net/own3duslive-live" -f "WIN 11,1,102,55" -W "http://static.ec.own3d.tv/player/Own3dPlayerV2_86.swf" -p "http://www.own3d.tv/live/33356" --live -y "own3d.aonempatic_33356"
            
            -r|--rtmp     url     URL (e.g. rtmp://host[:port]/path)
            -f|--flashVer string  Flash version string (default: "WIN 10,0,32,18")
            -W|--swfVfy   url     URL to player swf file, compute hash/size automatically
            -p|--pageUrl  url     Web URL of played programme
            -v|--live             Save a live stream, no --resume (seeking) of live streams possible
            -y|--playpath path    Overrides the playpath parsed from rtmp url
        '''
        rtmp = item.attrib.get('base')
        
        # override if unknown
        if '${cdn1}' in rtmp:
            rtmp = 'rtmp://fml.2010.edgecastcdn.net:1935/202010'
        elif '${cdn2}' in rtmp:
            rtmp = 'rtmp://owned.fc.llnwd.net:1935/owned'
        
        flashVer = 'WIN 11,1,102,55'
        #swfVfy   = 'http://static.ec.own3d.tv/player/Own3dPlayerV2_86.swf'
        pageUrl  = 'http://www.own3d.tv/live/%d' % stream_id
        #live     = 'True'
        playpath = stream_item.attrib.get('name')
        
        stream_url = '%s pageUrl=%s Playpath=%s swfUrl=http://static.ec.own3d.tv/player/Own3dPlayerV2_86.swf swfVfy=True Live=True' % (rtmp, pageUrl, playpath)
        
        stream_object = StreamObject()
        stream_object.title = channel_info['name']
        stream_object.game = channel_info['description']
        stream_object.description = channel_info['description']
        stream_object.stream_id = stream_id
        stream_object.rtmp_url = stream_url
        
        return stream_object

own3d_parser = Own3dParser()
def test_game_list():
    game_list = own3d_parser.get_game_list()
    print game_list

def test_archive_videos():
    # def get_archive_videos(self, archive_type=TYPE_VIDEOS, game_name=None, date=TIME_ANYTIME, sort_by=SORT_METHOD_VIEWS, genre_name=None, system_name=None)
    archive_videos = own3d_parser.get_archive_videos(game_name='Age of Conan')
    print archive_videos

def test_archive_video():
    video_id1 = 318858 # TheOddOne_Maokai_Commentary_Game
    video_id2 = 318000 # Tarilariran [id:11369] Archive (2011-12-04 12:31:20 - 12:59:55)
    video_id3 = 227488 # [HD] GC vs Monkey - DOTA 2 - Donkey Kong - Match 2 
    
    video_url1 = own3d_parser.get_archive_video_url(video_id1)
    print video_url1
    
    video_url2 = own3d_parser.get_archive_video_url(video_id2)
    print video_url2
    
    video_url3 = own3d_parser.get_archive_video_url(video_id3)
    print video_url3

if __name__ == '__main__':
    #test_game_list()
    test_archive_videos()
    #test_archive_video()
