import re
from lxml import etree
import urllib2
from StringIO import StringIO

def grep_document_single(document, query):
    matches = grep_document_all(document, query)
    return matches[0] if len(matches) > 0 else None

def grep_document_all(document, query):
    pattern = re.compile(query)
    matches = pattern.findall(document)
    return matches

def do_xpath_query(document, query, namespaces={}):
    return document.xpath(query, namespaces=namespaces)

def get_data(url, postdata=''):
    USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14'
    request = urllib2.Request(url, postdata)
    request.add_header('User-Agent', USER_AGENT)
    
    response = urllib2.urlopen(request)
    raw_data = response.read()
    
    response.close() #TODO:FIXME: needed?
    
    return raw_data

def build_xml_tree(raw_data):
    raw_xml = etree.XML(raw_data)
    return raw_xml

def build_html_tree(raw_data):
    html_parser = etree.HTMLParser()
    raw_html = etree.parse(StringIO(raw_data), html_parser)
    return raw_html

def sanitize_query(query):
    query = query.lstrip()
    query = query.rstrip()
    query = query.replace(' ', '+')
    query = urllib2.unquote(query)
    return query

