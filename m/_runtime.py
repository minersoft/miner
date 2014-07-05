"""
This file contains
classes and functions used by internal miner runtime engine
"""
import re
from m.common import *
from miner_globals import isScriptParameterDefined, getScriptParameter
import os.path
import os
import operator
import types

class Counter:
    """In command counter"""
    def __init__(self):
        self.val = 0
    def preIncr(self):
        self.val += 1
        return self.val
    def postIncr(self):
        res = self.val
        self.val += 1
        return res
    def preDecr(self):
        self.val -= 1
        return self.val
    def postDecr(self):
        res = self.val
        self.val -= 1
        return res
    def add(self, val):
        self.val += val
        return self.val
    def sub(self, val):
        self.val -= val
        return self.val
    def diff(self, val):
        d = val - self.val
        self.val = val
        return d

class Matcher:
    """Wrapper over regular expression match"""
    def __init__(self, reStr):
        self.myRegexp = re.compile(reStr)
        self.myMatches = None
    def getGroupNames(self):
        return [ groupAndId[0] for groupAndId in sorted(self.myRegexp.groupindex.items(), key=operator.itemgetter(1))]
    def match(self, s):
        self.myMatches = self.myRegexp.search(s)
        return self.myMatches is not None
    def __len__(self):
        return len(self.myRegexp.groupindex)
    def __getitem__(self, key):
        return self.myMatches.group(key)


class Reorderer(object):
    """
    Reorders records according to the value specified
    Aggregates elements within specified range divided on the bins.
    The precision of reorderer is bin size
    """
    def __init__(self, valueRange, binSize):
        self.valueRange = valueRange
        self.binSize = binSize
        self.currentTopBin = None
        self.numBins = int(float(self.valueRange)/self.binSize)
        self.hash = {}
    
    def _insertToBin(self, bin, record):
        binValues = self.hash.get(bin, None)
        if binValues:
            binValues.append(record)
        else:
            self.hash[bin] = [ record ]

    def _pop(self, fromBin, toBin):
        removedValues = []
        for bin in range(fromBin, toBin):
            binValues = self.hash.get(bin, None)
            if binValues:
                removedValues.extend(binValues)
                del self.hash[bin]
        return removedValues

    def push(self, value, record):
        removedValues = []
        binNumber = int(float(value)/self.binSize)
        if not self.currentTopBin:
            self.currentTopBin = binNumber
        if binNumber <= self.currentTopBin-self.numBins:
            print "Reorderer: Element is too old %s (current value %s, range=%s)" % \
                                     (str(value), str(self.currentTopBin*self.binSize), self.valueRange)
            return []
        self._insertToBin(binNumber, record)
        removedValues = []
        if self.currentTopBin < binNumber:
            removedValues = self._pop(self.currentTopBin-self.numBins, binNumber-self.numBins+1)
            self.currentTopBin = binNumber
        return removedValues            
    
    def flush(self):
        return self._pop(self.currentTopBin-self.numBins, self.currentTopBin+1)

def regularFileReader(fileName, itemSelector):
    return (fileName, open(fileName, "rb"))

import subprocess
class PopenFileObject(object):
    def __init__(self, args, bufsize=0, stderrToNull=False):
        if stderrToNull:
            self.devNull = open("/dev/null", "wb")
        else:
            self.devNull = None
        
        self.p = subprocess.Popen(args, bufsize=bufsize,stdout=subprocess.PIPE, stderr=self.devNull, close_fds=True)
    
    def read(self, size):
        return self.p.stdout.read(size)
    def readline(self):
        return self.p.stdout.readline()
    def close(self):
        self.p.stdout.close()
        if self.devNull:
            self.devNull.close()
        if self.p.poll():
            # process has finished
            return
        try:
            self.p.terminate()
        except:
            pass
        del self.p
        #self.p.wait()    

GLOB_CHARS_REGEX = re.compile(r'[\[\]?*]')
def zipFileReader(zipFileName, itemSelector):
    args = ["unzip", "-p", zipFileName]
    if itemSelector:
        if GLOB_CHARS_REGEX.search(itemSelector):
            if "/" in itemSelector:
                # we have explicit file pattern so
                args.append("-W")
                if itemSelector.startsWith("/"):
                    itemSelector = itemSelector[1:]
        args.append(itemSelector)
    p = PopenFileObject(args, bufsize=1024*1024)
    return (zipFileName+":"+itemSelector, p)
    
def gzFileReader(zipFileName, itemSelector):
    args = ["gunzip", "-c", zipFileName]
    p = PopenFileObject(args, bufsize=1024*1024, stderrToNull=True)
    return (zipFileName, p)
    
def pythonTarFileReader(tarFileName, itemSelector):
    import tarfile
    import fnmatch
    tar = tarfile.open(tarFileName, "r", bufsize=128*1024)
    if "," in itemSelector:
        items = set(itemSelector.split(","))
        for tarinfo in tar:
            if tarinfo.isreg() and tarinfo.name in items:
                yield ("%s:%s" % (tarFileName, tarinfo.name), tar.extractfile(tarinfo))
    else:
        for tarinfo in tar:
            if tarinfo.isreg() and fnmatch.fnmatch(tarinfo.name, itemSelector):
                yield ("%s:%s" % (tarFileName, tarinfo.name), tar.extractfile(tarinfo))
    
def tarFileReader(tarFileName, itemSelector):
    if itemSelector:
        return (tarFileName, (pair for pair in pythonTarFileReader(tarFileName, itemSelector)))
    args = ["tar", "-O", "-xf", tarFileName]
    p = PopenFileObject(args, bufsize=1024*1024, stderrToNull=True)
    return (tarFileName, p)
    
readersFuncMap = {
    "zip": zipFileReader,
    "gz":  gzFileReader,
    "tar": tarFileReader,
    "tgz": tarFileReader,
}

def findFilesInTree(parentDir, pattern):
    """Returns list of files from the tree that match provided pattern, sorted by the file name"""
    import fnmatch
    if not parentDir:
        parentDir = "."
    if not pattern:
        raise NoFilesInPattern("<empty>")
    fileTuples = []
    for dirTuple in os.walk(parentDir, followlinks=True):
        fileTuples += [(f, dirTuple[0]) for f in fnmatch.filter(dirTuple[2], pattern)]
    fileTuples.sort()
    return [os.path.join(t[1],t[0]) for t in fileTuples]
    
def expandFiles(fileNamePatterns, shouldOpen=True, checkPattern=True):
    import glob
    import sys
    fileNames = []
    abortOnError = not isScriptParameterDefined("IGNORE_FILE_OPEN_ERROR")
    #print "checkPattern", checkPattern, "fileNamePatterns", fileNamePatterns, "abortOnError", abortOnError
    if checkPattern:
        for p in fileNamePatterns:
            patternParts = p.split(':', 1)
            pattern = os.path.expanduser(patternParts[0])
            if len(patternParts) > 1:
                itemSelector = patternParts[1]
            else:
                itemSelector = ""
            # check if needed recursive search of files
            posOf3Dots = pattern.find(".../")
            if posOf3Dots != -1:
                files = findFilesInTree(pattern[:posOf3Dots], pattern[posOf3Dots+4:])
            else:
                if GLOB_CHARS_REGEX.search(pattern):
                    fs = glob.glob(pattern)
                    files = sorted(fs)
                    if not files:
                        raise NoFilesInPattern(pattern)
                else:
                    files = [pattern]
                    if abortOnError and not os.path.isfile(pattern):
                        raise FileDoesntExist(pattern)
            fileNames += [ (f, itemSelector) for f in files ]
    else:
        fileNames = []
        for f in fileNamePatterns:
            if ":" in f:
                parts = f.rsplit(":", 1)
                fileNames.append( (parts[0], parts[1]) )
            else:
                fileNames.append( (f, "") )
    if not shouldOpen:
        for name,item in fileNames:
            yield name + ":" + item
        return
    for (fileName, itemSelector) in fileNames:
        if fileName.endswith("tar.gz"):
            # handle explicitly
            readerFunc = tarFileReader
        else:
            parts = fileName.rsplit(".", 1)
            if len(parts) == 2:
                readerFunc = readersFuncMap.get(parts[1], regularFileReader)
            else:
                readerFunc = regularFileReader
        try:
            pair = readerFunc(fileName, itemSelector)
            if isinstance(pair[1], types.GeneratorType):
                for p in pair[1]:
                    yield p
            else:
                yield pair
        except:
            if abortOnError:
                raise

def isVerbose():
    val = getScriptParameter("verbose", True)
    if val == True:
        return True
    return val not in ["", "False", "0", "no"]

def mergeDictionaryItems(d1, d2):
    for key in d1.iterkeys():
        d1[key].merge(d2[key])
    return d1

def mergeDictionaryItemsToList(dlist):
    out = {}
    allKeys = set()
    for d in dlist:
        allKeys = d.viewkeys() | allKeys
    for key in allKeys:
        l = []
        for d in dlist:
            val = d.get(key)
            if val:
                l.append(val)
        out[key] = l
    return out

    