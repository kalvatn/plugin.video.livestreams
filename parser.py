# -*- coding: utf-8 -*-

import urllib2
from lxml import etree

class StreamObject(object):
    """docstring for StreamObject"""
    
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
    """docstring for Parser"""
    USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14'
    def __init__(self):
        super(Parser, self).__init__()

    def get_xml(self, url, postdata = ''):
        request = urllib2.Request(url, postdata)
        request.add_header('User-Agent', self.USER_AGENT)
        
        response = urllib2.urlopen(request)
        raw_xml = response.read()
        response.close()
        return raw_xml

class Own3dParser(Parser):
    """docstring for Own3dParser"""
    STREAM_LIST_LIVE_URL = "http://api.own3d.tv/live"
    STREAM_CONFIG_URL = "http://www.own3d.tv/livecfg/%d"
    
    def __init__(self):
        super(Own3dParser, self).__init__()
        
    def get_live_streams(self, game):
        
        raw_xml = self.get_xml(self.STREAM_LIST_LIVE_URL)
        xml_root = etree.XML(raw_xml)
        
        stream_list = []
        
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

    def get_rtmp_url(self, stream_id):
        raw_xml =  self.get_xml(self.STREAM_CONFIG_URL % stream_id)
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


        

