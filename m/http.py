#
# Copyright Michael Groys, 2012-2014
#

#
# This file implements HTTP request and response parser
# It uses python package mimetools to implement the logic
#

import urlparse
import mimetools
from StringIO import StringIO
import m.common as common

class HttpCommon:
    def _parseHeaders(self, headers):
        self.headers = mimetools.Message(StringIO(headers))

class HttpRequest(HttpCommon):
    def __init__(self, data):
        if not data:
            raise common.MiningError("Empty request")
        try:
            request, headers = data.split('\r\n', 1)
        except:
            raise common.MiningError("Failed to split request header: %s" % data)
          
        #print "====Start headers==="
        #print headers
        #print "--------------------"
        self._parseHeaders(headers)
        try:
            self.method, self.path, self.httpVersion = request.split(' ')
        except:
            raise common.MiningError("Failed to parse http request line: '%s'" % request)
        self.userAgent = self.headers.get("user-agent", None)
        self._parseUrl()

    def _parseUrl(self):
        self.parsedUrl = urlparse.urlparse(self.path, "http")
        self.host = self.headers.get("Host", "")
        self.fullUrl = "http://" + self.host + self.path
        self.paramLists = urlparse.parse_qs(self.parsedUrl.query, keep_blank_values=True)
        self.params = {}
        for name, pList in self.paramLists.iteritems():
            self.params[name] = pList[-1]
    def __str__(self):
        s = self.method + " http://"+ (self.host if self.host else "?.?.?.?") + self.path 
        range = self.headers.get("range")
        if range:
            s += " range=" + range
        return s

class HttpResponse(HttpCommon):
    def __init__(self, data):
        if not data:
            raise common.MiningError("Empty response")
        try:
            response, headers = data.split('\r\n', 1)
        except:
            raise common.MiningError("Failed to split response header: %s" % data)
            
        self._parseHeaders(headers)

        elements = response.split(' ', 2)
        if len(elements) < 2:
            raise common.MiningError("Failed to parse http response status line: %s" % response)
        self.httpVersion = elements[0]
        
        statusCodeStr = elements[1]
        self.statusString = elements[2] if len(elements)>2 else ""
            
        self.statusCode = int(statusCodeStr)
        cl = self.headers.get("content-length", "")
        cl = cl.strip()
        if cl.isdigit():
            self.length = int(cl)
        else:
            self.length = -1
        self.contentType = self.headers.gettype()
    def __str__(self):
        s = "%d %s clen=%d ctype=%s" % (self.statusCode, self.statusString, self.length, self.contentType)
        range = self.headers.get("content-range")
        if range:
            s += " range=" + range
        return s

class Uri:
    def __init__(self, data):
        self.parsedUrl = urlparse.urlparse(data, "http")
        self.host = self.parsedUrl.netloc
        self.paramLists = urlparse.parse_qs(self.parsedUrl.query, keep_blank_values=True)
        self.params = {}
        for name, pList in self.paramLists.iteritems():
            self.params[name] = pList[-1]
    def __str__(self):
        s = "host=%s path=%s params=[" % (self.host, self.parsedUrl.path)
        s += " ".join("%s=%s" % (param,value) for (param,value)  in self.params.iteritems())
        s += "]"
        return s

