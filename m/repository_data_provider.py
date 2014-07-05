from file_data_provider import *
import miner_globals
import repository_path
import re

class RepositoryDataProvider(FileDataProvider):
    # returns name of current dataProvider
    def getDataProviderName(self):
        return "repository"

    def __init__(self, uriList, streamType, moreVars):
        self.repositoryPathObj = repository_path.RepositoryPath()
        fileNamePatterns = []
        if len(uriList) == 0:
            raise NoFilesSpecified()
        for f in uriList:
            if f.startswith("repository://"):
                fileNamePatterns.append(f[13:])
            else:
                fileNamePatterns.append(f)

        self.sourceType = self.repositoryPathObj.getSourceType(fileNamePatterns[0])

        targetList = miner_globals.getAllTargetList()
        if self.sourceType not in targetList:
            # support plural case, e.g. coals, frecords
            if self.sourceType.endswith("s"):
                self.sourceType = self.sourceType[:-1]
                if self.sourceType not in  targetList:
                    raise UnknownTarget(self.sourceType)
        files = []
        for pattern in fileNamePatterns:
            if pattern.endswith("/"):
                pattern = pattern[:-1]
            if "/" in pattern:
                prefix, lastPart = pattern.rsplit("/", 1)
                prefix = self.repositoryPathObj.expand(prefix)
                times = lastPart.split(",")
                for t in times:
                    files += self.extractFiles(prefix, t)
            else:
                prefix = self.repositoryPathObj.expand(pattern)
                files += self.extractFiles(prefix, "")
        if not files:
            raise InvalidRepositoryPath(uriList)
        FileDataProvider.__init__(self, files, self.sourceType, moreVars, expandPatterns=False)

    TIME_COMPONENT_RE_STR = r"(\d{4})-?((\d\d)(-?(\d\d)(-\d\d(\d\d(\d\d)?)?)?)?)?"
    TIME_RANGE_RE = re.compile("^"+TIME_COMPONENT_RE_STR+"--"+TIME_COMPONENT_RE_STR+"$")
    LIST_RANGE_RE = re.compile(r"^(\d*|-\d+):(\d*|-\d+)$")
    TIME_COMPONENT_RE = re.compile("^"+TIME_COMPONENT_RE_STR+"$")
    LOG_FILE_STAMP_RE = re.compile(r"-\d\d\d\d\.(\d{8}-\d{6}(\.\d\d\d)?)")
    def extractFiles(self, prefix, timeRange):
        if RepositoryDataProvider.TIME_RANGE_RE.search(timeRange):
            match = RepositoryDataProvider.TIME_RANGE_RE.search(timeRange)
            fromTime,toTime = RepositoryDataProvider.getRangeFromMatch(match)
            #print "Matched time range", fromTime, toTime
            if len(fromTime) != len(toTime):
                raise "'from' time and 'to' time should be of the same precision"
        elif RepositoryDataProvider.TIME_COMPONENT_RE.search(timeRange):
            match = RepositoryDataProvider.TIME_COMPONENT_RE.search(timeRange)
            fromTime = RepositoryDataProvider.getTimestampFromMatch(match)
            #print "Matched time element", fromTime
            toTime = None
        elif RepositoryDataProvider.LIST_RANGE_RE.search(timeRange):
            match = RepositoryDataProvider.LIST_RANGE_RE.search(timeRange)
            fromStr, toStr = match.groups()
            if not fromStr:
                fromIndex = 0
            else:
                fromIndex = int(fromStr)
            if toStr:
                toIndex = int(toStr)
            files = self.getFilesFromDir(prefix, None, None)
            if toStr:
                return files[fromIndex:toIndex]
            else:
                return files[fromIndex:]
        else:
            #print "Search regular files", timeRange
            return self.getFilesFromDir(os.path.join(prefix, timeRange), None, None)
        dirs = self.getDirsForRange(prefix, fromTime, toTime)
        if not dirs:
            #print fromTime, toTime
            files = self.getFilesFromDir(prefix, fromTime, toTime)
        else:
            files = []
            for d in sorted(dirs):
                files += self.getFilesFromDir(os.path.join(prefix, d), fromTime, toTime)
        return files
    @staticmethod
    def getTimestampFromMatch(match):
        return match.group(1)+(match.group(3) if match.group(3) else "")+(match.group(5) if match.group(5) else "")+\
               (match.group(6) if match.group(6) else "")
     
    @staticmethod
    def getRangeFromMatch(match):
        fromTS = match.group(1)+(match.group(3) if match.group(3) else "")+(match.group(5) if match.group(5) else "")+\
               (match.group(6) if match.group(6) else "")
        toTS =   match.group(9)+(match.group(11) if match.group(11) else "")+(match.group(13) if match.group(13) else "")+\
               (match.group(14) if match.group(14) else "")
        return (fromTS, toTS)
    
    def getDirsForRange(self, prefix, fromTime, toTime):
        dirs = []
        try:
            listed = os.listdir(os.path.expanduser(prefix))
        except OSError as e:
            raise InvalidPattern(str(e))
        for d in listed:
            if fromTime is None:
                dirs.append(d)
            else:
                match = RepositoryDataProvider.TIME_COMPONENT_RE.search(d)
                if match:
                    timeStamp = RepositoryDataProvider.getTimestampFromMatch(match)
                    if RepositoryDataProvider.compareTimeStamp(timeStamp, fromTime, toTime):
                        dirs.append(d)
                    continue
                match = RepositoryDataProvider.TIME_RANGE_RE.search(d)
                if match:
                    dFromTime,dToTime = RepositoryDataProvider.getRangeFromMatch(match)
                    if (toTime and RepositoryDataProvider.checkIntersect(dFromTime, dToTime, fromTime, toTime)) \
                               or RepositoryDataProvider.compareTimeStamp(fromTime, dFromTime, dToTime):
                        dirs.append(d)
                    continue
        #print "dirs", dirs
        return sorted(dirs)

    def getFilesFromDir(self, parentDir, fromTime, toTime):
        """Returns list of files from the tree that match provided pattern, sorted by the file name"""
        fileRegeEx, groupId, archiveSelector = miner_globals.getRepositoryFilePattern(self.sourceType)
        #print "sourceType", self.sourceType,  "regExStr", fileRegeEx.pattern
        fileTuples = []
        parentDir = os.path.expanduser(parentDir)
        #print "parentDir", parentDir
        for dirTuple in os.walk(parentDir, followlinks=True):
            for f in dirTuple[2]:
                match = fileRegeEx.search(f)
                if match:
                    timeStamp = match.group(groupId)
                    #print "------matched ",f, timestamp 
                    if RepositoryDataProvider.compareTimeStamp(timeStamp, fromTime, toTime):
                        fileTuples.append( (timeStamp, f, dirTuple[0]) )
        fileTuples.sort()
        return [(os.path.join(t[2],t[1])+archiveSelector) for t in fileTuples]

    @staticmethod
    def compareTimeStamp(timeStamp, fromTime, toTime):
        if fromTime is None:
            return True
        if len(fromTime)<len(timeStamp):
            if timeStamp.startswith(fromTime):
                return True
        else:
            if fromTime.startswith(timeStamp):
                return True
        
        if toTime is not None:
            if len(toTime)<len(timeStamp):
                if timeStamp.startswith(toTime):
                    return True
            else:
                if toTime.startswith(timeStamp):
                    return True
        
        if timeStamp < fromTime:
            return False
        
        if toTime is not None:
            return (timeStamp < toTime)
        else:
            return False

    @staticmethod
    def checkIntersect(from1, to1, from2, to2):
        if RepositoryDataProvider.compareTimeStamp(from2, from1, to1) or RepositoryDataProvider.compareTimeStamp(to2, from1, to1):
            return True
        
        return (from2<from1 and to1<to2)
