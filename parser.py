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
        items = items_xpath(channel_element)

        rtmp_infos = []

        for item in items:
            rtmp_info = {}
            rtmp_url = item.attrib.get('base')
            if rtmp_url == '${cdn1}' or rtmp_url == '${cdn2}':
                rtmp_url = 'rtmp://fml.2010.edgecastcdn.net:1935/202010'

            stream_items_xpath = etree.XPath('//stream')
            for stream_item in stream_items_xpath(item):
                cdn_path = stream_item.attrib.get('name')
                rtmp_info[stream_item.attrib.get('label')] = '%s?%s' % (rtmp_url, cdn_path)
            rtmp_infos.append(rtmp_info)

        rtmp_url = rtmp_infos[0]['HD']
        
        stream_url = '%s pageUrl=%s Playpath=%s swfUrl=http://static.ec.own3d.tv/player/Own3dPlayerV2_86.swf swfVfy=True Live=True' % (rtmp_url, channel_info['ownerLink'], rtmp_url.split('?',1)[1])
        
        stream_object = StreamObject()
        stream_object.title = channel_info['name']
        stream_object.game = channel_info['description']
        stream_object.description = channel_info['description']
        stream_object.stream_id = stream_id
        stream_object.rtmp_url = stream_url
        
        return stream_object

