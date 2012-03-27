# -*- coding: utf-8 -*-

# core imports
import os
import sys

# xbmc imports
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# create Addon object in order to get addon metadata in a 'safe'/preferred way.
Addon = xbmcaddon.Addon('plugin.video.livestreams')

# locate libraries and add them to the pythonpath
ROOT_DIR = Addon.getAddonInfo('path')
LIB_DIR = xbmc.translatePath(os.path.join(ROOT_DIR, 'resources', 'lib')).decode("utf-8")
sys.path.append(LIB_DIR)

# addon imports
from parser import Own3dParser
own3dparser = Own3dParser()

# actions
ACTION_GET_LIVE_STREAMS = "get_live_streams"
ACTION_PLAY_LIVE_STREAM = "play_live_stream"

def get_base_query():
    ''' plugin://plugin.video.livestreams/ '''
    return sys.argv[0]

def get_handle():
    ''' handle for various XBMC-api calls '''
    return int(sys.argv[1])
    
def get_query_string():
    return sys.argv[2]

def parse_query(query_string):
    ''' 
        converts a query string of the form "query?param=foo&key=value"
        into a dictionary of param_keys and param_values
    '''
    parameter_dict = {}
    
    parameter_list = query_string[query_string.find('?')+1:].split('&')
    for parameter in parameter_list:
        parameter = parameter.split('=')
        if len(parameter) == 2:
            key = parameter[0]
            value = parameter[1]
            parameter_dict[key] = value

    return parameter_dict

def get_parameters():
    ''' shortcut for getting the parameter_dict '''
    return parse_query(get_query_string())

def create_list_item(name, query_string, isFolder=True, thumbnailImage=None):
    '''
        Creates a new XBMC list item
    '''
    if isFolder:
        iconImage = 'DefaultFolder.png'
    else:
        iconImage = 'DefaultVideo.png'
        
    if not thumbnailImage:
        thumbnailImage = iconImage

    url = get_base_query() + query_string
    
    listitem = xbmcgui.ListItem(name, iconImage=iconImage, thumbnailImage=thumbnailImage)
    xbmcplugin.addDirectoryItem(handle=get_handle(), url=url, listitem=listitem, isFolder=isFolder)

def play_live_stream(stream_id):
    xbmc.log("attempting to play live stream for stream id : %d" % int(stream_id))
    
    stream_object = own3dparser.get_rtmp_url(stream_id)
    xbmc.log("stream object : " + str(stream_object))
    
    item = xbmcgui.ListItem("Livestream")
    item.setInfo(
        type="Video", 
        infoLabels = {
            "Title" : stream_object.title,
            "Plot" : stream_object.description,
            "TVShowTitle" : stream_object.title,
            "Description": stream_object.description
        }
    )
    """
        stream_object.rtmp_url example (Dyrus, stream_id : 37905):
            rtmp://fml.2010.edgecastcdn.net:1935/202010?o8p-solomid_37905 pageUrl=http://www.own3d.tv/SoloMid Playpath=o8p-solomid_37905 swfUrl=http://static.ec.own3d.tv/player/Own3dPlayerV2_86.swf swfVfy=True Live=True
    
        available player cores:
            xbmc.PLAYER_CORE_AUTO
            xbmc.PLAYER_CORE_DVDPLAYER
            xbmc.PLAYER_CORE_MPLAYER
            xbmc.PLAYER_CORE_PAPLAYER
    """
    xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(stream_object.rtmp_url, item)
    return 1

def get_live_streams(game):
    streams = own3dparser.get_live_streams(game)
    
    for stream in streams:
        query_string = "?action=%s&stream_id=%d" % (ACTION_PLAY_LIVE_STREAM, int(stream.stream_id))
        
        create_list_item(stream.title, query_string, isFolder=False, thumbnailImage=stream.thumbnail_url)
        
    xbmcplugin.endOfDirectory(get_handle())

def list_games():
    # copy pasted 'most popular' list directly from 'Games' hover element. @27.03.2012
    games_list = [
        'Counter-Strike',
        'Defense of the Ancients',
        'Dota 2',
        'Heroes of Newerth',
        'League of Legends',
        'Lineage II',
        'Minecraft',
        'Quake Live',
        'RuneScape',
        'Star Wars: The Old Republic',
        'StarCraft II',
        'World of Warcraft',
    ]
    
    for game in games_list:
        query_string = '?action=%s&game=%s' % (ACTION_GET_LIVE_STREAMS, game)
        create_list_item(game, query_string, isFolder=True)
        
    xbmcplugin.endOfDirectory(get_handle())

if __name__ == '__main__':
    base_query = get_base_query()
    xbmc.log('base_query : %s' % str(base_query))

    handle = get_handle()
    xbmc.log('handle : %d' % handle)

    parameters = get_parameters()
    xbmc.log('parameters : %s' % str(parameters))

    action = parameters.get('action')

    if action is None:
        list_games()
    else:
        xbmc.log('action : %s' % action)
        if action == ACTION_GET_LIVE_STREAMS:
            game = parameters.get('game')
            get_live_streams(game)
        elif action == ACTION_PLAY_LIVE_STREAM:
            stream_id = int(parameters.get('stream_id'))
            play_live_stream(stream_id)

