#
# Copyright Michael Groys, 2014
#
import sys
from bin_utils import *

usage = "Usage: cat  <file>..."


if len(sys.argv) <= 1:
    files = ["-"]
elif sys.argv[1] in ["-h", "--help"]:
    print usage
    sys.exit()
else:
    files = sys.argv[1:]

reopenFileInBinMode(sys.stdout)


openMode = "rb"

for fileName in expandFiles(files):
    if fileName == "-":
        fileObj = sys.stdin
        reopenFileInBinMode(fileObj)
    else:
        try:
            fileObj = open(fileName, openMode)
        except Exception as e:
            print >> sys.stderr, str(e)
            sys.exit(1)
    copyStream(fileObj, sys.stdout)
    if fileObj != sys.stdin:
        fileObj.close()
