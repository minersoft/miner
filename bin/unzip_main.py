#
# Copyright Michael Groys, 2015
#
import zipfile
import argparse
import sys
import os
from bin_utils import *

MEM_EXTRACT_LIMIT = 16*1024

def parseOptions():
    parser = argparse.ArgumentParser(prog="unzip", description='list, test and extract compressed files in a ZIP archive')
    parser.add_argument('archive', help="Archive list or extract ('-' for stdout)")
    parser.add_argument('files', metavar="file", nargs='*', help="Files to extract")
    parser.add_argument('-q', dest='quiet', action="store_true", help="Perform operations quietly")
    parser.add_argument('-l', dest='listArchive', action="store_true", help="list archive files")
    parser.add_argument('-d', dest='exdir', help="An optional directory to which to extract files")
    parser.add_argument('-p', dest='pipe', action="store_true", help="extract files to pipe (stdout). Nothing but the file data is sent to stdout")
    parser.add_argument('-P', '--password', dest="password", help="use password to decrypt encrypted zipfile entries")

    return parser.parse_args()
    

options = parseOptions()

if options.archive == '-':
    reopenFileInBinMode(sys.stdin)
    zipFile = sys.stdin
elif not os.path.splitext(options.archive)[1]:
    zipFile = options.archive + ".zip"
else:
    zipFile = options.archive

extractExpression = convertPatternsToRegexp(options.files)
def specifiedFiles(members):
    for m in members.infolist():
        if extractExpression.match(m.filename):
            if options.quiet: print "Extracting", m.filename
            yield m
    
def allFiles(members):
    for m in members.infolist():
        if options.quiet: print "Extracting", m.filename
        yield m

if extractExpression:
    members = specifiedFiles
else:
    members = allFiles

def openZip(file):
    try:
        zipHandle = zipfile.ZipFile(file, "r")
    except zipfile.BadZipfile as e:
        print >> sys.stderr, "Invalid zip file %s: %s" % (options.archive, e)
        sys.exit(1)
    except zipfile.LargeZipFile as e:
        print >> sys.stderr, "ZIP64 extension required"
        sys.exit(1)
    except Exception as e:
        print >> sys.stderr, str(e)
        sys.exit(1)
    if options.password:
        zipHandle.setpassword(options.password)
    return zipHandle
        
zipHandle = openZip(zipFile)

if options.listArchive:
    print "Name\tOrig-Size\tCompressed-Size%\tDate"
    for zipInfo in zipHandle.infolist():
        d = zipInfo.date_time
        ratio = int(float(zipInfo.compress_size)/zipInfo.file_size*100) if zipInfo.file_size else 100 
        print "%s\t%d\t%d%%\t%02d:%02d:%02d %4d-%02d-%02d" % \
              (zipInfo.filename, zipInfo.file_size, ratio, d[3], d[4], d[5], d[0], d[1], d[2])
elif options.pipe:
    reopenFileInBinMode(sys.stdout)
    for zipInfo in zipHandle.infolist():
        if not extractExpression or (extractExpression and extractExpression.match(zipInfo.filename)):
            if zipInfo.file_size <= MEM_EXTRACT_LIMIT:
                data = zipHandle.read(zipInfo)
                sys.stdout.write(data)
            else:
                singleFile = zipHandle.open(zipInfo)
                copyStream(singleFile, sys.stdout, 16*1024)
                singleFile.close()
            
else:
    zipHandle.extractall(path=options.exdir, members=members(zipHandle))

zipHandle.close()


