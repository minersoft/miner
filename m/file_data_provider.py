from data_provider import DataProvider
import os.path
from _runtime import expandFiles
from common import *
import io_targets
import math

class FileDataProvider(DataProvider):
    # returns name of current dataProvider
    def getDataProviderName(self):
        return "file"

    def __init__(self, uriList, streamType, moreVars, expandPatterns=True):
        DataProvider.__init__(self, streamType, moreVars)
        self.expandPatterns = expandPatterns
        if "expandPatterns" in moreVars:
            if self.expandPatterns=="False" or self.expandPatterns=="false":
                self.expandPatterns = False
            del moreVars["expandPatterns"]
        
        if self.expandPatterns:
            fileNamePatterns = []
            for f in uriList:
                if f.startswith("file://"):
                    fileNamePatterns.append(f[7:])
                else:
                    fileNamePatterns.append(f)
        else:
            fileNamePatterns = uriList
        if len(fileNamePatterns) == 0:
            raise NoFilesSpecified()
        self.myFileNames = [name for name in expandFiles(fileNamePatterns, shouldOpen=False, checkPattern=self.expandPatterns) ]

        if not self._streamType:
            name = self.myFileNames[0].split(":",1)[0]
            ext = os.path.splitext(name)[1]
            if ext == ".gz":
                # try to get prev extension before gzip
                ext = os.path.splitext(os.path.splitext(name)[0])[1]
            self._streamType = io_targets.getTypeByExtension(ext)
            if not self._streamType:
                raise UnknownExtensionType(name)

    # returns iterator over pairs of (name, handle)
    # of all expanded objects
    # used at runtime
    def iterateHandles(self):
        return iter(expandFiles(self.myFileNames, shouldOpen=True, checkPattern=False))
    
    # peek first (name,handle)
    # used during compilation stage to get Variable list
    def peekFirstHandle(self):
        openedFileGenerator = expandFiles([self.myFileNames[0]], shouldOpen=True, checkPattern=False)
        try:
            return openedFileGenerator.next()
        except StopIteration:
            raise NoFilesInPattern(" ".join(self.myFileNames))

    # returns number of sources (handles) that will be created by data provider
    # should return -1 if unknown 
    def size(self):
        return len(self.myFileNames)

    # maps input for N different chunks
    # used by MAP-REDUCE command
    def map(self, n):
        l = len(self.myFileNames)
        if l < n:
            n = l
            chunkSize = 1
        else:
            chunkSize = int(math.ceil(float(l)/n))
        dataProviders = []
        for p in range(n):
            curFiles = self.myFileNames[(chunkSize*p):(chunkSize*(p+1))]
            #print "maped files chunk %d: %s" % (p, curFiles)
            dp = FileDataProvider(curFiles, self._streamType, self._moreVars)
            dataProviders.append(dp)
        return dataProviders
