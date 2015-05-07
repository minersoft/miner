#
# Copyright Michael Groys, 2015
#
import zipfile
import argparse
import sys
import os
from bin_utils import *

def parseOptions():
    parser = argparse.ArgumentParser(prog="zip", description='zip - package and compress (archive) files')
    parser.add_argument('-r', '--recurse-paths', dest="recurse", action='store_true',  help="Travel the directory structure recursively")
    parser.add_argument('-n', '--suffixes', dest="suffixes", help="Colon separated list of file suffixes that should not be compressed",
                        default=".Z:.zip:.zoo:.arc:.lzh:.arj")
    parser.add_argument('-x', '--exclude', nargs='+', help="Explicitly exclude the specified files by their path/pattern in zip archive")
    parser.add_argument('archive', help="Archive to create or update ('-' for stdout)")
    parser.add_argument('files', metavar="file", nargs='+', help="Files to archive")

    return parser.parse_args()
    

options = parseOptions()

files = expandFiles(options.files)

if options.archive == '-':
    reopenFileInBinMode(sys.stdout)
    zipFile = sys.stdout
elif not os.path.splitext(options.archive)[1]:
    zipFile = options.archive + ".zip"
else:
    zipFile = options.archive

dontCompress = set(options.suffixes.split(":"))
excludeExpression = convertPatternsToRegexp(options.exclude)


def getZipOperation(fileName):
    if excludeExpression:
        if excludeExpression.match(unixPath(fileName)):
            return None
    ext = os.path.splitext(fileName)[1]
    if ext in dontCompress:
        return zipfile.ZIP_STORED
    else:
        return zipfile.ZIP_DEFLATED

def WriteDirectoryToZipFile( zipHandle, srcPath, zipLocalPath = "" ):
    # Thanks to M Katz
    # https://stackoverflow.com/questions/1855095/how-to-create-a-zip-archive-of-a-directory/25048491#25048491?newreg=c6d3584148714d378eabac50090ff108
    srcPath = os.path.normpath(srcPath)
    basePath = os.path.split( srcPath )[ 0 ]
    prefixLen = ( len( basePath ) + 1 ) if basePath else 0
    for root, dirs, files in os.walk( srcPath ):
        p = os.path.join( zipLocalPath, root [prefixLen : ] )
        if excludeExpression:
            for d in dirs[:]:
                dirInZipPath = os.path.join(p, d)
                if excludeExpression.match(unixPath(dirInZipPath)):
                    dirs.remove(d)
        # add dir
        zipHandle.write( root, p, zipfile.ZIP_STORED )
        # add files
        for f in files:
            filePath = os.path.join( root, f )
            fileInZipPath = os.path.join( p, f )
            zipOperation = getZipOperation(fileInZipPath)
            if zipOperation is not None:
                zipHandle.write( filePath, fileInZipPath, zipOperation )

try:
    with zipfile.ZipFile(zipFile, 'a', allowZip64=True) as zipHandle:
        for file in files:
            if os.path.isdir(file):
                if options.recurse:
                    WriteDirectoryToZipFile(zipHandle, file)
                else:
                    print >> sys.stderr, "File %s is directory, skipped" % file
            else:
                zipHandle.write( file, zipfile.ZIP_DEFLATED)
except zipfile.BadZipfile as e:
    print >> sys.stderr, "Invalid zip file %s: %s" % (options.archive, e)
    sys.exit(1)
except zipfile.LargeZipFile as e:
    print >> sys.stderr, "ZIP64 extension required"
    sys.exit(1)
except Exception as e:
    print >> sys.stderr, str(e)
    sys.exit(1)

