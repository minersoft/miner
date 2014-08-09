import common

class DataProvider:
    _dataProviderClasses = {}
    @staticmethod
    def createDataProvider(uriList, streamType, moreVars):
        if len(uriList) == 0:
            raise common.NoFilesInPattern("")
        colonLoc = uriList[0].find("://")
        if colonLoc==-1:
            dataProviderName = "file"
        else:
            dataProviderName = uriList[0][:colonLoc]
            if not dataProviderName.isalpha():
                # fallback to "file" data provider
                dataProviderName = "file"
                
        klass = DataProvider._dataProviderClasses.get(dataProviderName)
        if not klass:
            raise common.UnknownDataProvider(dataProviderName)
        return klass(uriList, streamType, moreVars)
    @staticmethod
    def registerDataProvider(dataProviderName, dataProviderClass):
        DataProvider._dataProviderClasses[dataProviderName] = dataProviderClass
    
    def __init__(self, streamType=None, moreVars=None):
        self._streamType = streamType
        self._moreVars = moreVars if moreVars else {}

    def getStreamType(self):
        return self._streamType
    def getMoreVars(self):
        return self._moreVars
    
    ############################
    # Data provider abstract API
    ############################
    
    # Constructor signature
    #def __init__(self, uriList, streamType, moreVars):
    #    DataProvider.__init__(self, streamType, moreVars)

    # returns name of current dataProvider
    def getDataProviderName(self):
        raise NotImplemented
    
    # returns iterator over pairs of (name, handle)
    # of all expanded objects
    # used at runtime
    def iterateHandles(self):
        raise NotImplemented
    
    # peek first (name,handle)
    # used during compilation stage to get Variable list
    def peekFirstHandle(self):
        raise NotImplemented
    
    # returns number of sources (handles) that will be created by data provider
    # should return -1 if unknown 
    def size(self):
        return -1
    
    # maps input for N different chunks
    # used by MAP-REDUCE command
    def map(self, n):
        raise NotImplemented
