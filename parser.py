# -*- coding: utf-8 -*-

if __name__ == '__main__':
    # if run from the commandline on systems that do not have the librariees
    # installed
    import os, sys
    ROOT_DIR = os.getcwd()
    LIB_DIR = os.path.join(ROOT_DIR, 'resources', 'lib')
    sys.path.append(LIB_DIR)

from beaker.cache import cache_regions, cache_region

import utils

CACHE_DATA_DIR = '/tmp/plugin.video.livestream/cache/data'
CACHE_LOCK_DIR = '/tmp/plugin.video.livestream/cache/lock'


#TODO: FIXME: 
# add a more regions (forever, weekly, daily, yearly), get_game_list for
# example could probably be cached for a substantial length of time (yearly,
# monthly at most) -> fine tuning add functions for invalidating to force
# refresh
cache_regions.update({
    'five_minutes':{
        'expire' : 60*5,
        'type' : 'memory',
        'key_length' : 250,
        'data_dir' : CACHE_DATA_DIR,
        'lock_dir' : CACHE_LOCK_DIR
    },
    'daily' : {
        'expire' : 60*60*24,
        'type'   : 'file',
        'key_length' : 250,
        'data_dir' : CACHE_DATA_DIR,
        'lock_dir' : CACHE_LOCK_DIR
    },
    'annual' : {
        'expire' : 60*60*24*365,
        'type'   : 'file',
        'key_length' : 250,
        'data_dir' : CACHE_DATA_DIR,
        'lock_dir' : CACHE_LOCK_DIR
    }
})

class Enum(object):
    '''
        Simple enum emulation
    '''
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Enum id : %d , name : %s>' % (self.id, self.name)

class StreamObject(object):
    '''
        Datacontainer representing a stream item
        TODO:FIXME: create a complete standardized (non-site specific set of
        fields)
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
        return 'stream_id : %d, game : %s, title : %s' % (self.stream_id, 
                                                          self.game, 
                                                          self.title)

    def __repr__(self):
        return "<StreamObject stream_id : %d, title : %s, game : %s>" % (self.stream_id,
                                                                         self.title,
                                                                         self.game)

class Parser(object):
    '''
        Base class for parsers

        Provides utility functions for scraping and parsing
    '''

    def __init__(self):
        super(Parser, self).__init__()

    def get_response_data(self, url, postdata = ''):
        raw_data = utils.get_data(url, postdata=postdata) 
        return raw_data

class Own3dParser(Parser):
    '''
        Parser for Own3d.tv

        Provides functions for getting live streams (RTMP) and archive videos
        (MPEG4) using the own3d.tv api
        
        TODO:FIXME: Should be extracted to a separate module since it's gotten
        pretty lengthy now.
    '''

    LIST_LIVE_STREAMS_URL   = 'http://api.own3d.tv/live'
    LIST_GAMES_URL          = 'http://www.own3d.tv/browse' 
    LIST_ARCHIVE_URL        = 'http://api.own3d.tv/api.php'
    
    LIVE_STREAM_CONFIG_URL  = 'http://www.own3d.tv/livecfg/%d'
    ARCHIVE_VIDEO_URL       = 'http://www.own3d.tv/video/%d'

    class Type(object):
        All     = Enum(0, 'all')
        Live    = Enum(1, 'live')
        Archive = Enum(2, 'videos')

    class System(object):
        PS3         = Enum(3, 'Sony Playstation 3')
        PC          = Enum(1, 'PC')
        NintendoWii = Enum(5, 'Nintendo Wii')
        XBOX360     = Enum(2, 'Microsoft XBOX 360')

    class Genre(object):
        Adventure   = Enum(2, 'Adventure')
        MMORPG      = Enum(10, 'MMORPG')
        MOBA        = Enum(14, 'MOBA')
        Racing      = Enum(9, 'Racing')
        RolePlaying = Enum(4, 'Role Playing')
        Shooter     = Enum(1, 'Shooter')
        Simulation  = Enum(6, 'Simulation')
        Sports      = Enum(5, 'Sports')
        Strategy    = Enum(7, 'Strategy')

    class Date(object):
        Anytime     = Enum(0, 'anytime')
        Today       = Enum(1, 'today')
        ThisWeek    = Enum(2, 'week')
        ThisMonth   = Enum(3, 'month')

    class SortMethod(object):
        Views       = Enum(0, 'views')
        Relevance   = Enum(1, 'relevance')
        Date        = Enum(2, 'date')
    

    def __init__(self):
        super(Own3dParser, self).__init__()


    @cache_region('annual', 'get_game_list')
    def get_game_list(self):
        # TODO: FIXME: 
        # maybe parse the category anchors as well, will be able to browse by
        # letter/number
        raw_data = self.get_response_data(self.LIST_GAMES_URL)
        html_tree = utils.build_html_tree(raw_data)

        game_links = utils.do_xpath_query(
            html_tree, 
            '//a[re:test(string(@href), "^/game/[\w+]*$", "i")]', 
            namespaces={
                're' : 'http://exslt.org/regular-expressions'
            }
        )
        game_list = { 
            game_link.text : 'http://www.own3d.tv' + game_link.attrib['href'] for game_link in game_links 
        }
        return game_list

    def build_stream_object(self, item):
        stream_object = StreamObject()
        for stream_item in list(item):
            if stream_item.tag == 'title':
                stream_object.title = stream_item.text

            elif stream_item.tag == 'misc':
                stream_object.game = stream_item.get('game')
                viewers = stream_item.get('viewers')

                stream_object.viewers = int(viewers) if viewers else 0

            elif stream_item.tag == 'description':
                stream_object.description = stream_item.text

            elif stream_item.tag == 'thumbnail':
                stream_object.thumbnail_url = stream_item.text

            elif stream_item.tag == 'embed':
                stream_url = stream_item.text
                if stream_url[-1] == '/':
                    stream_url = stream_url[0:-2]
                stream_id = stream_url.split('/')[-1]

                stream_object.stream_url = stream_url
                stream_object.stream_id = int(stream_id)

        return stream_object

    def build_stream_object_list(self, items):
        stream_object_list = []
        for item in items:
            stream_object = self.build_stream_object(item)
            stream_object_list.append(stream_object)
        return stream_object_list

    def get_archive_videos(self, type=Type.Archive, 
                                 game_name=None, 
                                 date=Date.Anytime, 
                                 sort_by=SortMethod.Views, 
                                 genre=None, 
                                 system=None):
        if game_name:
            game_list = self.get_game_list()
            if not game_list.has_key(game_name):
                message = 'Could not find game : %s' % game_name
                raise KeyError(message)
            game_name = utils.sanitize_query(game_name) 
        
        if type not in [Own3dParser.Type.Archive]:
            message = 'Only archive supported, given : %s' % type.get_name()
            raise KeyError(message)

        type = type.get_name()
        date = date.get_name()
        sort_by = sort_by.get_name()
        system_id = system.get_id() if system else None
        genre_id = genre.get_id() if genre else None

        return self._get_archive_videos(type, game_name, date, sort_by, genre_id, system_id)

    @cache_region('daily', 'get_archive_videos')
    def _get_archive_videos(self, type, game_name, date, sort_by,genre_id, system_id):   
        query = '?search=&type=%s&time=%s&sort=%s' % (type, date, sort_by)
        
        if system_id:
            query += '&system=%d' % system_id
        
        if game_name:
            query += '&search_game=%s' % game_name

        if genre_id:
            query += '&genre_id=%d' % genre_id

        raw_data = self.get_response_data(self.LIST_ARCHIVE_URL + query)
        xml_doc = utils.build_xml_tree(raw_data)
        items = utils.do_xpath_query(xml_doc, '//item')
        return self.build_stream_object_list(items) 

    @cache_region('five_minutes', 'get_live_streams')
    def get_live_streams(self, game):
        raw_data = self.get_response_data(self.LIST_LIVE_STREAMS_URL)
        xml_doc = utils.build_xml_tree(raw_data)
        items = utils.do_xpath_query(xml_doc, '//item[misc[@game = "%s"]]' % game)
        return self.build_stream_object_list(items)

    @cache_region('daily', 'get_archive_video_url')
    def get_archive_video_url(self, video_id):
        raw_data = self.get_response_data(self.ARCHIVE_VIDEO_URL % video_id)

        # queryString : escape('?7418afca70ba1dc09fb6b6e37c287072169117b285d7dfcce5f8d90b455933d780e9&ec_seek=${start}&ec_rate=350&ec_prebuf=5')
        query_string = utils.grep_document_single(raw_data, 'escape\(\'\?(.+?)&')
        # HQUrl: 'videos/SD/318000/318858_4edc05c491748_HQ.mp4'
        hqurl = utils.grep_document_single(raw_data, 'HQUrl: \'(videos/.*?\\.mp4)\'')
        # HDUrl: 'videos/HD/227000/227488_4e8ce41b8e3f8_HD.mp4'
        hdurl = utils.grep_document_single(raw_data, 'HDUrl: \'(videos/.*?\\.mp4)\'')
        
        mpeg4_url = hdurl if hdurl else hqurl

        if not mpeg4_url or not query_string:
            print 'hqurl : %s, hdurl : %s' % (hqurl, hdurl)
            print 'mpeg4_url : %s' % mpeg4_url
            print 'query_string : %s' % query_string
            #log.warn('Could not find video for id : %d' % video_id)
            return None

        return 'http://vodcdn.ec.own3d.tv/%s?%s' % (mpeg4_url, query_string)

    @cache_region('daily', 'get_rtmp_url')
    def get_rtmp_url(self, stream_id):
        '''
            possible rtmp servers
            rtmp://own3duslivefs.fplive.net/own3duslive-live <- almost never
            rtmp://own3deulivefs.fplive.net/own3deulive-live <- almost never

            rtmp://fml.2010.edgecastcdn.net:1935/202010 <- pretty stable.
            rtmp://owned.fc.llnwd.net:1935/owned <- pretty stable.
            
            problem is masked servers (${cdn1}, ${cdn2}), right now just
            guessing on one random edgecast cdn
            
            could probably retry on all known servers, but that would be really
            slow.
            
            from http://bogy.mine.nu/sc2/stream2vlc.php , with channel id :
                33356 (chaox) , hoster : own3d.tv
            "C:\rtmpdump-2.3\rtmpdump.exe" 
                -r "rtmp://own3duslivefs.fplive.net/own3duslive-live" 
                -f "WIN 11,1,102,55" 
                -W "http://static.ec.own3d.tv/player/Own3dPlayerV2_86.swf" 
                -p "http://www.own3d.tv/live/33356" 
                --live 
                -y "own3d.aonempatic_33356"
            
            -r|--rtmp     url     URL (e.g. rtmp://host[:port]/path)
            -f|--flashVer string  Flash version string (default: "WIN 10,0,32,18")
            -W|--swfVfy   url     URL to player swf file, compute hash/size automatically
            -p|--pageUrl  url     Web URL of played programme
            -v|--live             Save a live stream, no --resume (seeking) of live streams possible
            -y|--playpath path    Overrides the playpath parsed from rtmp url
        '''
        raw_data = self.get_response_data(self.LIVE_STREAM_CONFIG_URL % stream_id)
        xml_doc = utils.build_xml_tree(raw_data)

        channel = utils.do_xpath_query(xml_doc, '//channel')[0]
        item = utils.do_xpath_query(channel, '//item')[0]
        stream_item = utils.do_xpath_query(item, '//stream')[0]

        rtmp = item.attrib.get('base')
        
        # override if unknown
        if '${cdn1}' in rtmp:
            rtmp = 'rtmp://fml.2010.edgecastcdn.net:1935/202010'
        elif '${cdn2}' in rtmp:
            rtmp = 'rtmp://owned.fc.llnwd.net:1935/owned'
        
        #flashVer = 'WIN 11,1,102,55'
        #swfVfy   = 'http://static.ec.own3d.tv/player/Own3dPlayerV2_86.swf'
        pageUrl  = 'http://www.own3d.tv/live/%d' % stream_id
        #live     = 'True'
        playpath = stream_item.attrib.get('name')
        
        stream_url = '%s pageUrl=%s Playpath=%s swfUrl=http://static.ec.own3d.tv/player/Own3dPlayerV2_86.swf swfVfy=True Live=True' % (rtmp, pageUrl, playpath)
        
        stream_object = StreamObject()
        stream_object.title = channel.attrib.get('name')
        stream_object.game = channel.attrib.get('description')
        stream_object.description = channel.attrib.get('description')
        stream_object.stream_id = stream_id
        stream_object.rtmp_url = stream_url
        
        return stream_object

own3d_parser = Own3dParser()
def test_game_list():
    game_list = own3d_parser.get_game_list()
    print game_list

def test_archive_videos():
    archive_videos = own3d_parser.get_archive_videos(game_name='Age of Conan')

    for video in archive_videos:
        print video
        print own3d_parser.get_archive_video_url(video.stream_id)

def test_live_streams():
    live_streams = own3d_parser.get_live_streams('League of Legends')
    print live_streams

if __name__ == '__main__':
    #test_game_list()
    test_archive_videos()
    test_live_streams()
