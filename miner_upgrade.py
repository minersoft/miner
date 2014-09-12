import optparse
import sys
import os
import shutil

minerBaseDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(minerBaseDir)
import miner_version

usage = "Usage: %prog -d <destination> [<more options>]"
parser = optparse.OptionParser(usage=usage, version=miner_version.version, prog="miner_upgrade")
def parseOptions():
    parser.add_option("-d", "--destination", dest="destination",
                      help="location of current miner installation")
    parser.add_option("-r", "--recovery-location", dest="recovery_location",
                      help="recovery folder")
    parser.add_option("-v", "--current-version", dest="current_version",
                      help="current version of miner in the destination folder")
    parser.add_option("-b", "--current-build", dest="current_build",
                      help="current version of miner in the destination folder")
    
    (options, args) = parser.parse_args()
    return (options, args)

(options, args) = parseOptions()

if not options.destination:
    parser.print_help()
    sys.exit(1)

if options.current_version is not None and options.current_build is not None:
    if options.current_version==miner_version.version and int(options.current_build)==miner_version.build:
        print "Not updated miner version is the same: %s build %d" % (miner_version.version, miner_version.build)
        sys.exit()

if options.recovery_location:
    os.makedirs(options.recovery_location)
    minerRecovery = os.path.join(options.recovery_location, "miner")
    shutil.rmtree(minerRecovery, ignore_errors=True)
    shutil.copytree(src=options.destination, dst=minerRecovery)

for newFileName in os.listdir("."):
    destFilePath = os.path.join(options.destination, newFileName)
    if os.path.isfile(destFilePath):
        os.unlink(destFilePath)
    elif os.path.isdir(destFilePath):
        shutil.rmtree(destFilePath, ignore_errors=True)
    elif os.path.islink(destFilePath):
        os.unlink(destFilePath)
    
    if os.path.isfile(newFileName):
        shutil.copy2(newFileName, options.destination)
    elif os.path.isdir(newFileName):
        shutil.copytree(newFileName, destFilePath)
