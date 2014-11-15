#
# Copyright Michael Groys, 2014
#
import tarfile
import optparse
import sys
import os
from bin_utils import *

usage = "Usage: %prog [cxt...] -f archive [<file>...]"
parser = optparse.OptionParser(usage=usage, version="1.0", prog="tar")
def parseOptions():
    parser.add_option("-f", "--file", dest="archive",
                      help="archive file to use")
    parser.add_option("-z", "--gzip", dest="compression", action="store_const", const="gzip",
                      help="use gzip compression")
    parser.add_option("-j", "--bzip2", dest="compression", action="store_const", const="bzip2",
                      help="use bzip2 compression")
    parser.set_defaults(compression="none")
    parser.add_option("-t", "--list", dest="list_files", action="store_true",
                      help="list the contents of an archive")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                      help="verbosely list files processed")
    parser.add_option("-x", "--extract", "--get", dest="extract", action="store_true",
                      help="extract files from an archive")
    parser.add_option("--extract-all", dest="extract_all", action="store_true",
                      help="try to extract all files even those with unsecure pathes (containing ..)")
    parser.add_option("-c", "--create", dest="create", action="store_true",
                      help="create a new archive")
    parser.add_option("-O", "--to-stdout", dest="to_stdout", action="store_true",
                      help="extract files to standard output")
    parser.add_option("--exclude", dest="excludes", action="append",
                      help="glob expression specifying filenames to exclude")
    parser.add_option("-H", "--format", dest="format", action="store",
                      help="create archive of the given format (gnu, pax=posix or ustar)")
    parser.add_option("--posix", dest="format", action="store_const", const="posix",
                      help="set POSIX 1003.1-2001 (pax) format")
    parser.add_option("-C", "--directory", dest="directory", action="store", default=".",
                      help="change to directory")

    (options, files) = parser.parse_args()
    return (options, files)

(options, files) = parseOptions()
files = expandFiles(files)

if not options.archive:
    print >>sys.stderr, "Archive name should be specified"
    parser.print_usage(sys.stderr)
    sys.exit(1)

isVerbose = False

if options.verbose:
    isVerbose = True

def isValidFileName(fileName):
    if fileName.startswith("/"):
        return False
    if ".." in fileName.split("/"):
        return False
    return True

def goodFiles(members):
    for tarinfo in members:
        if isValidFileName(tarinfo.name):
            if isVerbose: print "Extracting", tarinfo.name
            yield tarinfo

def allFiles(members):
    for tarinfo in members:
        if isVerbose: print "Extracting", tarinfo.name
        yield tarinfo

specificFilesToExtract = None
def specificFiles(members):
    for tarinfo in members:
        if tarinfo.name in specificFilesToExtract:
            if isVerbose: print "Extracting", tarinfo.name
            yield tarinfo

def globFilter(tarinfo):
    import fnmatch
    for exclude in options.excludes:
        if fnmatch.fnmatch(tarinfo.name, exclude):
            return None
    if isVerbose: print "Adding", tarinfo.name 
    return tarinfo

def allFilter(tarinfo):
    if isVerbose: print "Adding", tarinfo.name 
    return tarinfo

def openTar(mode, format = tarfile.DEFAULT_FORMAT):
    try:
        tar = tarfile.open(options.archive, mode, format=format)
        return tar
    except tarfile.TarError as te:
        print >>sys.stderr, "tar file open error occurred: %s" % str(te)
    except IOError as ioerror:
        print >>sys.stderr, str(ioerror)
    except OSError as oserror:
        print >>sys.stderr, str(oserror)
    sys.exit(1)

def createTar(tarobj, filterFunc, files):
    backupDir = os.getcwd()
    os.chdir(options.directory)
    for fileName in files:
        try:
            tarobj.add(fileName, filter=filterFunc)
        except Exception as e:
            print >>sys.stderr, str(e)
    os.chdir(backupDir)

def extractTar(tarobj, members, to_stdout):
    if to_stdout:
        reopenFileInBinMode(sys.stdout)
        for tarinfo in members(tarobj):
            fileobj = tarobj.extractfile(tarinfo)
            if fileobj:
                copyStream(fileobj, sys.stdout)
                fileobj.close()
    else:
        try:
            tarobj.extractall(path=options.directory, members=members(tarobj))
        except Exception as e:
            print >> sys.stderr, str(e)
            sys.exit(1)
    
  
if options.list_files:   
    tarobj = openTar("r")
    tarobj.list(verbose=isVerbose)
    tarobj.close()
elif options.create:
    if not files:
        print >>sys.stderr, "No files specified"
        sys.exit(1)
    if options.excludes:
        filterFunc = globFilter
    elif isVerbose:
        filterFunc = allFilter
    else:
        filterFunc = None
    if options.compression == "gzip":
        mode = "w:gz"
    elif options.compression == "bzip2":
        mode = "w:bz2"
    else:
        mode = "w"
    createFormat = tarfile.DEFAULT_FORMAT
    if options.format:
        if options.format in ["pax", "posix"]:
            createFormat = tarfile.PAX_FORMAT
        elif options.format == "ustar":
            createFormat = tarfile.USTAR_FORMAT
        elif options.format == "gnu":
            createFormat = tarfile.GNU_FORMAT
    tarobj = openTar(mode, createFormat)
    createTar(tarobj, filterFunc, files)
    tarobj.close()
elif options.extract:
    if options.extract_all:
        members = allFiles
    elif files:
        specificFilesToExtract = set(options.files)
        members = specificFiles
    else:
        members = goodFiles
    tarobj = openTar("r")
    extractTar(tarobj, members, options.to_stdout)
    tarobj.close()
