import m.runtime as runtime
import types
import math
import sys
from miner_globals import getScriptParameter

def _identityConvertFunc(val):
    s = str(val)
    if s.find(',') != -1:
        s = '"' + s + '"'
    return s

def _defaultConvertFunc(val):
    if isinstance(val, int) or isinstance(val, float) or isinstance(val, long):
        s = runtime.num2h(val)
    else:
        s = str(val)
        if s.find(',') != -1:
            s = '"' + s + '"'
    return s

def _floatConvertFunc(val):
    return float(val)

def _intConvertFunc(val):
    return int(val)

def _bytesConvertFunc(val):
    return runtime.bytes2h(val)

def _percentConvertFunc(val):
    return "%.1f%%" % (val*100)

def _boolConvertFunc(val):
    return "True" if val else "False"

class oStdout:
    def __init__(self, fileName, variableNames, **formats):
        if fileName == "stdout":
            self.filehandle = sys.stdout
        else:
            self.filehandle = open(fileName, "w")
        self.myVars = variableNames
        self.myWidths = [max(len(v), 8) for v in variableNames]
        self.nVars = len(self.myVars)
        self.myConvertFuncs = []
        self.myFormats = []
        self.myWidths = []
        defaultFormatValue = formats.get("_")
        if not defaultFormatValue:
            defaultFormatValue = getScriptParameter("DEFAULT_STDOUT_FORMAT", "*")
        self.defaultFormat = self.getFormat(defaultFormatValue)
        for i in range(self.nVars):
            convertFunc, width, format = self.getFormat(formats.get(self.myVars[i], None))
            self.myConvertFuncs.append(convertFunc)
            self.myFormats.append(format)
            self.myWidths.append(max(len(self.myVars[i]), width))
        self.myFormatsDefined = False
        self.headerWasPrinted = False
    
    def printHeader(self):
        fullWidth = sum(self.myWidths)+2*len(self.myVars)
        print >>self.filehandle, "="*fullWidth
        printVars = []
        i = 0
        for v in self.myVars:
            printVars.append("{0:<{width}s}".format(v, width=self.myWidths[i]))
            i+=1
        print >>self.filehandle, ", ".join(printVars)
        print >>self.filehandle, "-"*fullWidth
        self.headerWasPrinted = True
    
    def getFormat(self, format):
        if format is None:
            return self.defaultFormat
        elif isinstance(format, types.FunctionType):
            return (format, 8, None)
        elif isinstance(format, long) or isinstance(format, int):
            width = abs(format)
            if format>0:
                sFormat = "{0:<{width}s}"
            else:
                sFormat = "{0:>{width}s}"
            return (_identityConvertFunc, width, sFormat)
        elif isinstance(format, float):
            sFormat = "{0:>{width}.%df}" % math.ceil((format%1)*10)
            return (_floatConvertFunc, int(format), sFormat)
        elif format == "*":
            return (_defaultConvertFunc, 8, None)
        elif format == "%":
            return (_percentConvertFunc, 8, "{0:>{width}s}")
        elif format == "i":
            return (_intConvertFunc, 8, "{0:>{width}d}")
        elif format == "B":
            return (_bytesConvertFunc, 8, "{0:>{width}s}")
        elif format == "b":
            return (_boolConvertFunc, 6, "{0:<{width}s}")
        elif format == "x":
            return (_intConvertFunc, 10, "0x{0:>08x}")
        elif format == "xx":
            return (_intConvertFunc, 18, "0x{0:>016x}")
        elif format == "ip":
            return (runtime.num2ip, 16, "{0:<{width}s}")
        elif format == "T":
            return (runtime.gmtime2a, 19, "{0:<{width}s}")
        elif format == "t":
            return (runtime.dtime2a, 8, "{0:>{width}s}")
        elif format == "s":
            return (_identityConvertFunc, 8, "{0:<{width}s}")
        elif format == "<":
            return (_identityConvertFunc, 8, "{0:<{width}s}")
        elif format == ">":
            return (_identityConvertFunc, 8, "{0:>{width}s}")
        elif format == "Tm":
            return (runtime.gmtime2ams, 23, "{0:<{width}s}")
        elif format == "mt":
            return (runtime.dtimems2a, 8, "{0:>{width}s}")
        elif format == "hex":
            return (runtime.a2hex, 12, "{0:>{width}s}")
        else:
            return self.defaultFormat
            
    def save(self, record):
        if not self.myFormatsDefined:
            i = 0
            for val in record:
                if self.myFormats[i] is None:
                    if isinstance(val, int) or isinstance(val, float) or isinstance(val, long):
                        self.myFormats[i] = "{0:>{width}s}"
                    else:
                        self.myFormats[i] = "{0:<{width}s}"
                i += 1
            self.myFormatsDefined = True
        values = []
        i = 0
        for e in record:
            values.append(self.toStr(e, i))
            i += 1
        if not self.headerWasPrinted:
            for i in range(len(values)):
                if self.myWidths[i] < len(values[i]) <=30:
                    self.myWidths[i] = len(values[i])
            self.printHeader()
        try:
            print >>self.filehandle, ", ".join(values)
        except IOError:
            raise KeyboardInterrupt

    def toStr(self, val, i):
        if i>=len(self.myFormats):
            return ""
        width=self.myWidths[i]
        s = self.myConvertFuncs[i](val)
        if isinstance(s, str) and len(s) > width:
            # make it 4 byte align:
            width = (len(s)+3)/4*4
        return self.myFormats[i].format(s, width=width)

    def close(self):
        if not self.headerWasPrinted:
            self.printHeader()
        if self.filehandle is not sys.stdout:
            self.filehandle.close()

import subprocess
class oLess(oStdout):
    def __init__(self, fileName, variableNames, **formats):
        oStdout.__init__(self, "stdout", variableNames, **formats)
        self.lessHandler = subprocess.Popen(["less", "-M"], stdin=subprocess.PIPE)
        self.filehandle = self.lessHandler.stdin
    def close(self):
        oStdout.close(self)
        self.lessHandler.wait()

