#
# Copyright Michael Groys, 2014
#
import optparse
import sys
import hashlib
from bin_utils import reopenFileInBinMode, expandFiles


usage = "Usage: %prog [<options>] <file>..."
parser = optparse.OptionParser(usage=usage, version="1.0", prog="md5sum")
def parseOptions():
    parser.add_option("-b", "--binary", dest="binary", action="store_true",
                      help="read files in binary mode (default)")
    parser.add_option("-t", "--text", dest="binary", action="store_false",
                      help="read files in text mode")
    parser.set_defaults(binary=True)

    (options, files) = parser.parse_args()
    return (options, files)

def md5sum(fileObj, name):
    READ_BUF_SIZE = 128*1024
    md5Obj = hashlib.md5()
    while True:
        buf = fileObj.read(READ_BUF_SIZE)
        if not buf:
            break
        md5Obj.update(buf)
    print md5Obj.digest().encode("hex") + "\t" + name

(options, files) = parseOptions()
files = expandFiles(files)

if not files:
    if options.binary:
        reopenFileInBinMode(sys.stdin)
    md5sum(sys.stdin, "stdin")
    sys.exit()

def openFile(options):
    if options.file:
        try:
            out = open(options.file, "wb")
        except Exception as e:
            print >>sys.stderr, "Failed to open %s for writing" % options.file
            print str(e)
            sys.exit(1)
    else:
        out = sys.stdout
    return out


openMode = "rb" if options.binary else "r"

ec = 0
for fileName in files:
    try:
        fileObj = open(fileName, openMode)
    except Exception as e:
        print >> sys.stderr, str(e)
        ec = 1
        continue
    md5sum(fileObj, fileName)
    fileObj.close()
    ec = 0

sys.exit(ec)
