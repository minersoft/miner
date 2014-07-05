#
# Copyright Qwilt, 2012
#
# The code contained in this file may not be used by any other entities without explicit written permission from Qwilt.
#
# Author: michaelg
# 

#
# This file contains implementation of various aggregation commands
# That can be used in mining FOR SELECT or FOR DISTINCT ... SELECT ... commands
#

from miner_globals import addAggregator

class Base:
    def add(self, value):
        raise NotImplementedError
    def getValue(self):
        raise NotImplementedError
    def merge(self, other):
        raise NotImplementedError

class Sum(Base):
    def __init__(self):
        self.mySum = 0
    def add(self, value):
        self.mySum += value
    def getValue(self):
        return self.mySum
    def merge(self, other):
        self.mySum += other.mySum

class SumIf(Base):
    def __init__(self):
        self.mySum = 0
    def add(self, cond, value):
        if cond:
            self.mySum += value
    def getValue(self):
        return self.mySum
    def merge(self, other):
        self.mySum += other.mySum

class Rate(Sum):
    def __init__(self, period):
        Sum.__init__(self)
        self.myPeriod = period
    def getValue(self):
        return float(Sum.getValue(self))/self.myPeriod

class RateIf(SumIf):
    def __init__(self, period):
        SumIf.__init__(self)
        self.myPeriod = period
    def getValue(self):
        return float(SumIf.getValue(self))/self.myPeriod

class FractionSum(Base):
    def __init__(self):
        self.mySum = 0
        self.myTotal = 0
    def add(self, cond, value):
        if cond:
            self.mySum += value
        self.myTotal += value
    def getValue(self):
        return float(self.mySum)/self.myTotal if self.myTotal!=0 else 0.
    def merge(self, other):
        self.mySum += other.mySum
        self.myTotal += other.myTotal

class Ratio(Base):
    def __init__(self):
        self.myNom = 0
        self.myDenom = 0
    def add(self, nom, denom):
        self.myNom += nom
        self.myDenom += denom
    def getValue(self):
        if self.myDenom == 0:
            return 0.
        return float(self.myNom)/self.myDenom
    def merge(self, other):
        self.myNom += other.myNom
        self.myDenom += other.myDenom

class Avg(Base):
    def __init__(self):
        self.mySum = 0
        self.myCnt = 0
    def add(self, value):
        self.mySum += value
        self.myCnt += 1
    def getValue(self):
        return float(self.mySum)/self.myCnt if self.myCnt > 0 else 0.
    def merge(self, other):
        self.mySum += other.mySum
        self.myCnt += other.myCnt

class AvgIf(Avg):
    def __init__(self):
        Avg.__init__(self)
    def add(self, cond, value):
        if cond:
            Avg.add(self, value)

class Count(Base):
    def __init__(self):
        self.myCount = 0
    def add(self, value):
        if value:
            self.myCount += 1
    def getValue(self):
        return self.myCount
    def merge(self, other):
        self.myCount += other.myCount

class Fraction(Base):
    def __init__(self):
        self.myCount = 0
        self.myTotal = 0
    def add(self, value):
        if value:
            self.myCount += 1
        self.myTotal += 1
    def getValue(self):
        return float(self.myCount)/self.myTotal if self.myTotal!=0 else 0.
    def merge(self, other):
        self.myTotal += other.myTotal
        self.myCount += other.myCount

class Number(Base):
    def __init__(self):
        self.mySet = set()
    def add(self, value):
        self.mySet.add(value)
    def getValue(self):
        return len(self.mySet)
    def merge(self, other):
        self.mySet |= other.mySet

class NumberIf(Number):
    def __init__(self):
        Number.__init__(self)
    def add(self, condition, value):
        if condition:
            Number.add(self, value)

class Min(Base):
    def __init__(self):
        self.myMin = None
    def add(self, value):
        if (self.myMin is None) or value < self.myMin:
            self.myMin = value
    def getValue(self):
        return self.myMin
    def merge(self, other):
        self.myMin = min(self.myMin, other.myMin)

class Max(Base):
    def __init__(self):
        self.myMax = None
    def add(self, value):
        if (self.myMax is None) or value > self.myMax:
            self.myMax = value
    def getValue(self):
        return self.myMax
    def merge(self, other):
        self.myMax = max(self.myMax, other.myMax)

class Stats(Base):
    """Aggregates statistical information on data"""
    def __init__(self):
        self.myMax = None
        self.myMin = None
        self.myNum = 0
        self.mySum = 0
        self.mySum2 = 0
    def add(self, value, numTimes=1):
        self.myNum += numTimes
        self.mySum += numTimes * value
        self.mySum2+= numTimes * (value*value) 
        if (self.myMin is None) or value < self.myMin:
            self.myMin = value
        if (self.myMax is None) or value > self.myMax:
            self.myMax = value
    def getValue(self):
        return self
    def merge(self, other):
        self.myMax = max(self.myMax, other.myMax)
        self.myMin = min(self.myMax, other.myMax)
        self.myNum += other.myNum
        self.mySum += other.mySum
        self.mySum2+= other.mySum2
    @property
    def sigma(self):
        import math
        if self.myNum==0:
            return 0.
        a = self.avg
        return math.sqrt(float(self.mySum2)/self.myNum - a*a)
    @property
    def sample_sigma(self):
        import math
        if self.myNum==0 or self.myNum==1:
            return 0.
        a = self.avg
        return math.sqrt(float(self.mySum2 - a*a * self.myNum)/(self.myNum-1) )
    @property
    def min(self):
        return self.myMin
    @property
    def max(self):
        return self.myMax
    @property
    def avg(self):
        if self.myNum:
            return float(self.mySum)/self.myNum
        else:
            return 0
    @property
    def sum(self):
        return self.mySum
    @property
    def sum_squares(self):
        return self.mySum2
    @property
    def num(self):
        return self.myNum
    
    def __str__(self):
        sd = self.sample_sigma
        x = self.avg
        s = "[%f<%f<%f <%f:%d> %f>%f>%f]" % (self.myMin, x-2*sd, x-sd, x, self.myNum, x+sd,x+2*sd, self.myMax)
        return s

class StatsIf(Stats):
    def __init__(self):
        Stats.__init__(self)
    def add(self, condition, value):
        if condition:
            Stats.add(self, value)

class ValueAtMin(Base):
    def __init__(self):
        self.myMin = None
        self.myStored = None
    def add(self, value, store):
        if not self.myMin or value < self.myMin:
            self.myMin = value
            self.myStored = store
    def getValue(self):
        return self.myStored
    def merge(self, other):
        if (other.myMin is not None) and other.myMin < self.myMin:
            self.myMin = other.myMin
            self.myStored = other.myStored

class ValueAtMax(Base):
    def __init__(self):
        self.myMax = None
        self.myStored = None
    def add(self, value, store):
        if not self.myMax or value > self.myMax:
            self.myMax = value
            self.myStored = store
    def getValue(self):
        return self.myStored
    def merge(self, other):
        if (other.myMax is not None) and other.myMax > self.myMax:
            self.myMax = other.myMax
            self.myStored = other.myStored

class Superset(Base):
    def __init__(self):
        self.mySet = set()
    def add(self, value):
        if isinstance(value,set):
            self.mySet |= value
        elif isinstance(value, list):
            for val in value:
                self.mySet.add(val)
        else:
            self.mySet.add(value)
    def getValue(self):
        return self.mySet
    def merge(self, other):
        self.mySet |= other.mySet

class First(Base):
    def __init__(self):
        self.myVal = None
    def add(self, value):
        if self.myVal is None:
            self.myVal = value
    def getValue(self):
        return self.myVal
    def merge(self, other):
        if self.myVal is None:
            self.myVal = other.myVal

class Last(Base):
    def __init__(self):
        self.myVal = None
    def add(self, value):
        if value is not None:
            self.myVal = value
    def getValue(self):
        return self.myVal
    def merge(self, other):
        if other.myVal is not None:
            self.myVal = other.myVal

class Append(Base):
    def __init__(self):
        self.myVal = []
    def add(self, value):
        self.myVal.append(value)
    def getValue(self):
        return self.myVal
    def merge(self, other):
        self.myVal.extent(other.myVal)

class Concat(Base):
    def __init__(self):
        self.myVal = []
    def add(self, value):
        self.myVal.extend(value)
    def getValue(self):
        return self.myVal
    def merge(self, other):
        self.myVal.extent(other.myVal)

class Segments(Base):
    """
    Aggregates multiple segments into one object:
    Properties:
      ranges   - list of tuples of format [(start, next), ..]
      segments - list of tuples of format [(start, size), ...]
    Methods:
      __len__   - number of segments
      getSize() - get size of all segments including gaps in between
      getNetSize() - size of segments without gaps
      getSizeOfBlocks(blockSizeInBytes) - size of segments if stored on block device
    """
    def __init__(self, maxSegments=99999999):
        # segments[] is an array of segments. Each segment is an array with 2 entries:[start-offset, end-offset].
        # Note that end-offset is one PAST the last byte in the segment. So a segment of 6 bytes, from 
        # offset 0 to offset 5, is [0,6]
        self._segments=[]

        # Max amount of segments we are allowed to use
        self.maxSegments=maxSegments

    def __str__ (self):
        return str(self._segments)

    def _canAddSegment (self):
        return len(self._segments) < self.maxSegments

    def add(self, start, size):
        import bisect
        if size == 0:
            return
        segments=self._segments
        l=len(segments)
        if size < 0:
            raise RuntimeError("size < 0: start=%s, size=%s" % (start, size))
        end = start+size
        trSeg=[start,end]
        acquiredBytes = 0

        # Special case #1: list is empty
        if l == 0:
            if self._canAddSegment():
                segments.append(trSeg)
            return

        # Special case #2 (Quite common): Continue last segment
        if start == segments[l-1][1]:
            segments[l-1][1] = end
            return

        # Special case #3: Isolated before first segment
        if end < segments[0][0]:
            if self._canAddSegment():
                segments.insert(0, trSeg)
                acquiredBytes = size
            return

        # Special case #4: Isolated after last segment
        if start > segments[l-1][1]:
            if self._canAddSegment():
                segments.append(trSeg)
                acquiredBytes = size
            return

        # find segment ending at start, or containing start, or beginning after start
        # If there is a segment beginning with start, i will point to it. Otherwise, i will point to the 
        #   first segment starting after start
        i=bisect.bisect(segments, [start])
        # Do I merge with the prev segment ?
        if (i > 0) and (segments[i-1][1] >= start):
            if segments[i-1][1] >= end:
                return
            # Calc overlap between my start and end of segment
            # Extend segment
            segments[i-1][1] = end
            # Merge with following segments
            self.mergeAsNeeded(segments, i-1)
            return

        # Now we are sure that I have nothing to do with segment i-1
        
        # Am I isolated from segment i (Which may not exist) ?
        if (i == l) or (end < segments[i][0]):
            if self._canAddSegment():
                segments.insert(i, trSeg)
            return

        # Now we know that I have an overlap with segment i
        # Remember: start<=segments[i][0]

        # Am I fully contained in it ?
        if (start ==  segments[i][0]) and (end <=segments[i][1]):
            return

        # Calc overlap between my start and end of segment
        # Merge with segment i
        if start < segments[i][0]:
            numPrefixBytesInCache = 0
            acquiredBytes = segments[i][0] - start
            segments[i][0] = start
        else:
            numPrefixBytesInCache = min(end, segments[i][1]) - start

        # Merge with segment i
        if end > segments[i][1]:
            acquiredBytes += end - segments[i][1]
            segments[i][1] = end
        # Merge with following segments
        self.mergeAsNeeded(segments, i)

    def mergeAsNeeded (self, segments, i):
        """
        Segment i was recently enlarged to the right (i.e. the end was enlarged),
        need to swallow the following segments as needed.

        Returns amount of overlap that was canceled
        """
        overLap=0

        l = len(segments)
        j = i+1
        while (j < len(segments)) and (segments[i][1] >= segments[j][0]):
            overLap += min(segments[i][1], segments[j][1]) - segments[j][0]
            j = j+1

        if j != i+1:
            segments[i][1]=max(segments[i][1], segments[j-1][1])
            segments[i+1:j] = []

        return overLap

    def getSize (self):
        if len(self._segments)==0:
            return 0
        return self._segments[-1][1]

    def getNetSize (self):
        sum = 0
        for seg in self._segments:
            sum += seg[1]-seg[0]
        return sum

    def getSizeOfBlocks(self, blockSizeInBytes):
        l = len(self._segments)
        if l == 0:
            return 0
        numBlocks = 0
        i = 0
        while i < l:
            s = self._segments[i]
            # sanity check
            if s[1]-s[0] == 0:
                # some error - empty segment
                i += 1
                continue
            # computes disk size space by this segment (aligned by block size)
            startBlock = s[0]/blockSizeInBytes;
            endBlock = (s[1]-1)/blockSizeInBytes;
            i += 1
            while i<l:
                s = self._segments[i]
                # sanity check
                if s[1]-s[0] == 0:
                    continue;

                if s[0]/blockSizeInBytes != endBlock:
                    break

                endBlock = (s[1]-1)/blockSizeInBytes;
                i += 1
            
            numBlocks += endBlock-startBlock+1;
    
        return numBlocks * blockSizeInBytes;

    def __len__(self):
        return len(self._segments)

    @property
    def ranges(self):
        return [tuple(s) for s in self._segments]

    @property
    def segments(self):
        return [(s[0], s[1]-s[0]) for s in self._segments]

    def getValue(self):
        return self

    def merge(self, other):
        """Merges all segments from another Segments object"""
        for seg in other._segments:
            self.add(seg[0], seg[1]-seg[0])

    def isRangeIn(self, start, size):
        """
        If cacheThis is True, updates self.segments according to start and size

        Returns (inCache, numPrefixBytesInCache, wasCached):
          inCache: True if transaction is fully in cache, False if not
          numPrefixBytesInCache: If inCache is False, returns num of bytes at the beginning of the segment which were in cache
          acquiredBytes: Num of bytes added to cache (Always 0 if cacheThis is False)
        """
        import bisect
        segments=self._segments
        l=len(segments)
        if size < 0:
            raise RuntimeError("size < 0: start=%s, size=%s" % (start, size))
        end = start+size
        trSeg=[start,end]
        acquiredBytes = 0

        # Special case #1: list is empty
        if l == 0:
            return False

        # Special case #2 (Quite common): After last segment
        if start >= segments[l-1][1]:
            return False

        # Special case #3: Isolated before first segment
        if end <= segments[0][0]:
            return False

        # find segment ending at start, or containing start, or beginning after start
        # If there is a segment beginning with start, i will point to it. Otherwise, i will point to the 
        #   first segment starting after start
        i=bisect.bisect(segments, [start])
        if (i < l) and (segments[i][0] == start):
            return (end<=segments[i][1])
        # Do I merge with the prev segment ?
        if (i > 0) and (segments[i-1][1] >= start):
            return (end<=segments[i-1][1])
        
        return False
