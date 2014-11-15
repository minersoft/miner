# 
# Copyright Michael Groys, 2014
#

import sys
import os

def reopenFileInBinMode(fileobj):
    if sys.platform == "win32":
        import msvcrt
        msvcrt.setmode(fileobj.fileno(), os.O_BINARY)

def copyStream(inStream, outStream, bufSize = 128*1024):
    if inStream == sys.stdin:
        bufSize = 16*1024
    try:
        while True:
            buf = inStream.read(bufSize)
            if not buf:
                return
            outStream.write(buf)
    except KeyboardInterrupt:
        pass

def expandFiles(files):
    if sys.platform == "win32":
        import glob
        expandedFiles = []
        for file in files:
            expandedFiles.extend(glob.glob(file))
        return expandedFiles
    else:
        return files
