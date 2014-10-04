#
# Copyright Michael Groys, 2014
#
import optparse
import os
import sys
import gzip

READ_BUF_SIZE = 128*1024
GZ_EXTENSION = ".gz"

usage = """Usage: gzip [<options>] files ... - compress files
       gunzip files... - uncompress files
       zcat files... - dumps content of compressed files to stdout"""

parser = optparse.OptionParser(usage=usage, version="1.0", prog="gzip")
def parseOptions():
    parser.add_option("-a", "--ascii", dest="ascii", action="store_true",
                      help="convert end-of-lines using local conventions")
    parser.add_option("-c", "--stdout", "--to-stdout", dest="stdout", action="store_true",
                      help="Write output on standard output")
    parser.add_option("-d", "--decompress", "--uncompress", dest="decompress", action="store_true",
                      help="Decompress")
    parser.add_option("-f", "--force", dest="force", action="store_true",
                      help="Force compression or decompression even if the corresponding file already exists")
    parser.add_option("--fast", action="store_const", const=1, dest="compression",
                      help="Fastest speed of compression")
    parser.add_option("--best", action="store_const", const=9, dest="compression",
                      help="Slowest speed, best of compression")
    parser.add_option("-#", action="store", type="int", dest="compresslevel",
                      help="1-fastest speed & less compression, 9-slowest speed & max compression")
    parser.set_defaults(compresslevel=6)
    (options, files) = parser.parse_args()
    return (options, files)

def forceUnlink(path):
    import stat
    # try to change permissions to readwrite and retry the function
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        os.unlink(path)
    except Exception as e:
        print >>sys.stderr, str(e)
        sys.exit(1)

def deleteFile(path):
    try:
        os.unlink(path)
    except:
        forceUnlink(path)
    
def reopenFileInBinMode(fileobj):
    if sys.platform == "win32":
        import msvcrt
        msvcrt.setmode(fileobj.fileno(), os.O_BINARY)
    
def copyStream(inStream, outStream):
    while True:
        buf = inStream.read(READ_BUF_SIZE)
        if not buf:
            return
        outStream.write(buf)

def compress(options, files):
    if not files:
        reopenFileInBinMode(sys.stdout)
        inStream = sys.stdin
        try:
            gzipStream = gzip.open(fileobj=sys.stdout, mode="w", compresslevel=options.compresslevel)
            copyStream(inStream, gzipStream)
            gzipStream.close()
        except Exception as e:
            print >>sys.stderr, str(e)
    else:
        if options.ascii:
            mode = "r"
        else:
            mode = "rb"
        for fileName in files:
            outFileName = fileName + GZ_EXTENSION
            if os.path.exists(outFileName):
                if options.force:
                    deleteFile(outFileName)
                else:
                    print >>sys.stderr, "File %s exists skipped (use -f option to force)" % outFileName
                    continue
            try:
                gzipStream = gzip.open(outFileName, mode="wb", compresslevel=options.compresslevel)
            except Exception as e:
                print >>sys.stderr, str(e)
                continue
            try:    
                inStream = open(fileName, mode=mode)
            except Exception as e:
                print >>sys.stderr, str(e)
            else:
                copyStream(inStream, gzipStream)
                inStream.close()
                deleteFile(fileName)
            gzipStream.close()
            
            

def decompress(options, files):
    if options.ascii:
        mode = "r"
    else:
        mode = "rb"
    if not files:
        reopenFileInBinMode(sys.stdin)
        try:
            gzipStream = gzip.open(fileobj=sys.stdin, mode="rb", compresslevel=options.compresslevel)
        except Exception as e:
            print >>sys.stderr, str(e)
            return
        if not options.ascii:
            reopenFileInBinMode(sys.stdout)
        outStream = sys.stdout
        copyStream(gzipStream, outStream)
        gzipStream.close()
    else:
        if options.ascii:
            mode = "w"
        else:
            mode = "wb"
        for fileName in files:
            if options.stdout:
                if not options.ascii:
                    reopenFileInBinMode(sys.stdout)
                outStream = sys.stdout
                try:
                    gzipStream = gzip.open(fileName, mode="rb", compresslevel=options.compresslevel)
                    copyStream(gzipStream, outStream)
                    gzipStream.close()
                except Exception as e:
                    print >>sys.stderr, str(e)
                    continue
            else:
                if not fileName.endswith(GZ_EXTENSION):
                    print >>sys.stderr, "File %s doesn't end with %s don't know how to rename, skipped" % (fileName, GZ_EXTENSION)
                    continue
                outFileName = fileName[:-len(GZ_EXTENSION)]
                if os.path.exists(outFileName):
                    if options.force:
                        deleteFile(outFileName)
                    else:
                        print >>sys.stderr, "File %s exists skipped (use -f option to force)" % outFileName
                        continue
                        
                try:
                    outStream = open(outFileName, mode=mode)
                except Exception as e:
                    print >>sys.stderr, str(e)
                    continue
                try:
                    gzipStream = gzip.open(fileName, mode="rb", compresslevel=options.compresslevel)
                except Exception as e:
                    print >>sys.stderr, str(e)
                else:
                    copyStream(gzipStream, outStream)
                    gzipStream.close()
                    deleteFile(fileName)
                outStream.close()

(options, files) = parseOptions()

if options.decompress:
    decompress(options, files)
else:
    compress(options, files)
