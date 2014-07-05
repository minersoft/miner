"""
Set of utility functions:
  floor(value, step, start=0)
  ceil(value, step, start=0)
  gmtime2a(unixtime)
  a2gmtime(s)
  dtime2a(dtime)
  a2dtime(s)
  dtimems2a(dtime)
  a2dtimems(s)
  num2h(num)
  bytes2h(num)
  loadFromPickle(fileName)
  saveToPickle(obj, fileName)
  loadFromJson(fileName)
  saveToJson(obj, fileName)
  num2ip(num)
  ip2num(ipStr)
  class DistinctTimes(delta)
  class DistinctRanges(delta=0)
  getMyPath()
"""
import re
import operator
import time
import m.common as common
import math

def floor(value, step, start=0):
    """floor(value, step, start=0): Returns the largest number smaller or equal to <value> in the steps of <step> starting from <start>"""
    rel = value - start
    intDiv = int(rel / step)
    restored = intDiv * step
    if isinstance(restored, int) or isinstance(restored, long):
        return restored+start
    # Handle float numbers
    if abs(rel-restored-step)<step*1e-14:
        # consider errors of floating point arithmetics
        return (intDiv+1)*step + start
    else:
        return restored + start

def ceil(value, step, start=0):
    """ceil(value, step, start=0): Returns smallest number grater or equal to <value> in the steps of <step> starting from <start>"""
    rel = value - start
    restored = (rel // step) * step
    if isinstance(restored, int) or isinstance(restored, long):
        return value if rel == restored else (restored+step+start)
    # Handle float numbers
    if abs(rel-restored)<1e-15:
        return restored + start
    else:
        return restored + step + start

def gmtime2a(unixtime):
    """Converts unix time to GMT time in format '2011-12-11 09:00:21'"""
    tm = time.gmtime(int(unixtime))
    s = time.strftime("%Y-%m-%d %H:%M:%S", tm)
    return s

def gmtime2ams(unixtime):
    """Converts float unix time to GMT time in format '2011-12-11 09:00:21.555'"""
    msec = int((unixtime%1)*1000)
    tm = time.gmtime(int(unixtime))
    s = time.strftime("%Y-%m-%d %H:%M:%S", tm)
    return s + (".%03d"%msec)

_TIME_REXP = re.compile(r"(\d+)-(\d+)-(\d+)( (\d+):(\d+)(:(\d+))?)?")

def a2gmtime(s):
    """Converts time string in format '2011-12-11 09:00:21' (time part is optional) to GMT epoch time"""
    matches = _TIME_REXP.match(s)
    if not matches:
        return 0
    tm_year = int(matches.group(1))
    tm_mon  = int(matches.group(2))
    tm_mday = int(matches.group(3))

    if matches.group(4):
        tm_hour = int(matches.group(5))
        tm_min  = int(matches.group(6))
        tm_sec  = 0 if not matches.group(8) else int(matches.group(8))
    else:
        tm_hour = 0
        tm_min  = 0
        tm_sec  = 0
    return int(time.mktime( (tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, 0, 0, 0) )) - time.timezone


def dtime2a(dtime):
    """Converts time in seconds to 'HH:MM:SS'"""
    dtime = int(dtime)
    sec = dtime % 60
    dtime /= 60
    minute = dtime % 60
    dtime /= 60
    hour = dtime
    return "%d:%02d:%02d" % (hour, minute, sec)

def a2dtime(s):
    """Converts 'HH:MM:SS' to seconds"""
    tokens = s.split(':')
    l = len(tokens)
    if l==0:
        return 0
    elif l==1:
        return int(tokens[0])
    elif l==2:
        return int(tokens[0])*60 + int(tokens[1])
    else:
        return int(tokens[0])*3600 + int(tokens[1])*60 + int(tokens[2])

def dtimems2a(dtime):
    """Converts time in milli-seconds to 'HH:MM:SS.mmm'"""
    dtime = int(dtime)
    msec = dtime % 1000
    dtime /= 1000
    sec = dtime % 60
    dtime /= 60
    minute = dtime % 60
    dtime /= 60
    hour = dtime
    if hour > 0:
        return "%d:%02d:%02d.%03d" % (hour, minute, sec, msec)
    elif minute>0:
        return "%d:%02d.%03d" % (minute, sec, msec)
    else:
        return "%d.%03d" % (sec, msec)


def a2dtimems(s):
    """Converts 'HH:MM:SS.mmm' to milli-seconds"""
    tokens = s.split('.')
    if len(tokens) == 0:
        return 0
    elif len(tokens) == 1:
        return int(tokens[0])
    else:
        s = tokens[0]
        msec = int(tokens[1])

    tokens = s.split(':')

    l = len(tokens)
    if l==0:
        return 0
    elif l==1:
        sec = int(tokens[0])
    elif l==2:
        sec = int(tokens[0])*60 + int(tokens[1])
    else:
        sec = int(tokens[0])*3600 + int(tokens[1])*60 + int(tokens[2])

    return sec*1000 + msec

def a2hex(s):
    """Converts strin to hex representation: ff:00:ff:00 ..."""
    return ':'.join(x.encode('hex') for x in s)

MEM_1KB = 1024
MEM_1MB = 1024*MEM_1KB
MEM_1GB = 1024*MEM_1MB
MEM_1TB = 1024*MEM_1GB

def bytes2h(num):
    """Bytes to human readable string conversion"""
    anum = abs(num)
    if anum == 0:
        s = "0B"
    elif anum >= MEM_1TB:
        s = "%.1fTB" % (float(num)/MEM_1TB)
    elif anum >= MEM_1GB:
        s = "%.1fGB" % (float(num)/MEM_1GB)
    elif anum >= MEM_1MB:
        s = "%.1fMB" % (float(num)/MEM_1MB)
    elif anum >= MEM_1KB:
        s = "%.1fKB" % (float(num)/MEM_1KB)
    else:
        s = "%dB" % num
    return s

def num2h(num):
    """Number to human readable string conversion"""
    anum = abs(num)
    if num == 0:
        s = "0"
    elif anum > 1e12:
        s = "%.2fT" % (num/1e12)
    elif anum > 1e9:
        s = "%.2fG" % (num/1e9)
    elif anum > 1e6:
        s = "%.2fM" % (num/1e6)
    elif anum > 1e4:
        s = "%.2fK" % (num/1e3)
    elif anum >= 1 and (isinstance(num, int) or isinstance(num, long)):
        s = "%d" % num
    elif anum >= 0.1:
        s = "%.2f" % num
    elif anum > 2e-3:
        s = "%.3f" % num
    else:
        s = "%.2fu" % (num/1e-6)
    return s

def loadFromPickle(fileName):
    """Loads python object from pickle file"""
    import pickle
    try:
        handler = open(fileName, "rb")
        try:
            obj = pickle.load(handler)
        except:
            raise
            obj = None
        handler.close()
        return obj
    except:
        raise
        return None

def saveToPickle(obj, fileName):
    """Saves python object to pickle file"""
    import pickle
    try:
        handler = open(fileName, "wb")
        try:
            pickle.dump(obj, handler)
        except:
            print "Failed to save to file", fileName
            raise
        handler.close()
    except:
        print "Failed to open file:", fileName
        raise

def loadFromJson(fileName):
    """Loads python object from json file"""
    import json
    try:
        handler = open(fileName, "rb")
        try:
            obj = json.load(handler)
        except:
            obj = None
        handler.close()
        return obj
    except:
        return None

def saveToJson(obj, fileName):
    """Saves python object to json file"""
    import json
    try:
        handler = open(fileName, "wb")
        try:
            json.dump(obj, handler)
        except:
            print "Failed to save to file", fileName
        handler.close()
    except:
        print "Failed to open file:", fileName

def num2ip(num):
    """Converts local number to ipv4 string"""
    ip1 = num&0xFF;
    ip2 = (num>>8)&0xFF;
    ip3 = (num>>16)&0xFF;
    ip4 = (num>>24)&0xFF;
    return "%d.%d.%d.%d" % (ip4,ip3,ip2,ip1)

def ip2num(ipStr):
    """Converts ipv4 string representation to local number format"""
    import socket
    import struct
    return struct.unpack("!I", socket.inet_aton(ipStr))[0]
    
class DistinctTimes:
    """
Used for accumulation of events that happenen in approximate same time e.g.:
    SET distinctTimes=runtime.DistinctTimes(1m)
    ...|FOR DISCTINCT distinctTimes.value(dateTime, clientIp) as distinct SELECT sum(volume) | SELECT distinct[0] as clientIp, distinct[1] as dateTime, volume | ...
    """
    def __init__(self, delta):
        self.distincts = {}
        self.delta = delta
    def value(self, timeValue, distinct):
        import bisect
        if distinct not in self.distincts:
            self.distincts[distinct] = [timeValue]
            return (timeValue, distinct)
        else:
            times = self.distincts[distinct]
            pos = bisect.bisect_right(times, timeValue)
            if pos > 0 and (timeValue-times[pos-1]<=self.delta):
                return (times[pos-1], distinct)
            elif pos < len(times) and (times[pos]-timeValue<=self.delta):
                return (times[pos], distinct)
            else:
                times.insert(pos,timeValue)
                return (timeValue, distinct)
    def clear(self):
        self.distincts.clear()

class DistinctRanges:
    """
Used for accumulation of events that happenen in approximate same time e.g.:
    SET distinctTimes=runtime.DistinctRanges(1m)
    ...|FOR DISCTINCT distinctTimes.value(clientIp, dateTime) as distinct SELECT sum(volume) | SELECT distinct[0] as clientIp, distinct[1] as dateTime, volume | ...
    """
    def __init__(self, delta=0):
        self.distincts = {}
        self.delta = delta
    def value(self, start, size, *distinct):
        import bisect
        if distinct not in self.distincts:
            self.distincts[distinct] = [[start, start, start+size]]
            return (start, ) + tuple(distinct)
        else:
            ranges = self.distincts[distinct]
            pos = bisect.bisect_right(ranges, start)
            if pos > 0 and (start-ranges[pos-1][2]<=self.delta):
                ranges[pos-1][2] = start+size
                return (ranges[pos-1][1],) + tuple(distinct)
            elif pos < len(ranges) and (ranges[pos][0]-start-size<=self.delta):
                ranges[pos-1][0] = start
                return (ranges[pos][1],) + tuple(distinct)
            else:
                ranges.insert(pos, [start, start, start+size])
                return (start,) + tuple(distinct)
    def clear(self):
        self.distincts.clear()

def getMyPath():
    """returns path of current script"""
    from miner_globals import getCurrentScriptPath
    return getCurrentScriptPath()

def isParameterDefined(paramName):
    """returns true if parameter is defined"""
    from miner_globals import isScriptParameterDefined as mg_isScriptParameterDefined
    return mg_isScriptParameterDefined(paramName)

def getToolVersion(toolName):
    """returns version of installed miner tool or None if it doesn't exist"""
    from miner_globals import getToolVersion as mg_getToolVersion
    return mg_getToolVersion(toolName)

def getToolPath(toolName):
    """returns path of installed tool"""
    from miner_globals import getToolPath as mg_getToolPath
    return mg_getToolPath(toolName)

def ip4_subnet_c(ip):
    """returns C subnet of ipv4 address e.g.: 1.2.3.4 -> 1.2.3.0"""
    return ".".join(ip.split(".")[:-1]) + ".0"

def splitRange(start, size, segmentSize, aligned=True):
    """splitRange(start, size, segmentSize, aligned=True)
Splits single range to multiple segments, either aligned or not"""
    if size == 0:
        return [(start, 0)]
    if aligned:
        startBlock = start/segmentSize
        endBlock = (start+size-1)/segmentSize
        if startBlock == endBlock:
            return [(start, size)]
        segments = [(start, segmentSize-start%segmentSize)]
        for s in range(startBlock+1, endBlock):
            segments.append( (s*segmentSize, segmentSize) )
        segments.append( (endBlock*segmentSize, start+size - endBlock*segmentSize) )
        return segments
    else:
        if size <= segmentSize:
            return [(start, size)]
        segments = []
        cur = start
        end = start + size
        while cur + segmentSize <= end:
            segments.append( (cur, segmentSize) )
            cur += segmentSize
        if cur < end:
            segments.append( (cur, end-cur) )
        return segments

class lru_cache:
    """lru_cache is class that allows to manage cache in python with fixed number of elements
The number of element can't be modified in run time
# basic usage
    cache = lru_cache(miss_function, maxsize, hit_function=None)
    value = cache(x)
# attributes
    cache.maxsize
    cache.num_hits
    cache.num_misses
# methods
    cache.clear(maxsize=0)
    key in cache
    lru_cache.unit_test()
    """
    def __init__(self, maxsize, miss_function, hit_function=None):
        # Link layout:     [PREV, NEXT, KEY, RESULT]
        self.miss_function = miss_function
        self.hit_function = hit_function
        self.maxsize = maxsize
        self.clear()

    def __call__(self, key, *creation_params, **argv):
        cache = self.cache
        root = self.root
        link = cache.get(key)
        if link is not None:
            link_prev, link_next, _, result = link
            link_prev[1] = link_next
            link_next[0] = link_prev
            last = root[0]
            last[1] = root[0] = link
            link[0] = last
            link[1] = root
            self.num_hits += 1
            if self.hit_function:
                # result is not updated, we just allow hit function to return something different
                result = self.hit_function(key, result, *creation_params, **argv)
            return result
        result = self.miss_function(key, *creation_params, **argv)
        root[2] = key
        root[3] = result
        oldroot = root
        root = self.root = root[1]
        root[2], oldkey = None, root[2]
        root[3], oldvalue = None, root[3]
        del cache[oldkey]
        cache[key] = oldroot
        self.num_misses += 1
        return result

    @property
    def num_total(self):
        return self.num_hits + self.num_misses
    
    def __len__(self):
        return len(self.cache)
    
    def __contains__(self, key):
        return key in self.cache 
    
    def clear(self, maxsize=0):
        if maxsize:
            self.maxsize = maxsize
        self.root = [None, None, None, None]
        self.cache = cache = {}

        root = self.root
        last = root
        for i in range(self.maxsize):
            key = object()
            cache[key] = last[1] = last = [last, root, key, None]
        root[0] = last
        self.num_hits = 0;
        self.num_misses = 0

    @staticmethod
    def default_hit_func(key, result, *creation_params, **argv):
        return result
    @staticmethod
    def unit_test(maxsize=3):
        p = lru_cache(ord, maxsize=maxsize)
        for c in 'abcdecaeaa':
            print(c, p(c))
        print "hits=%d misses=%d" % (p.num_hits, p.num_misses)

def order(a, b):
    """order(a, b)
Returns ordered tuple made of a and b"""
    return (a, b) if a<b else (b, a)
