import optparse
import sys
import os
import shutil
import stat

minerBaseDir = os.path.dirname(os.path.abspath(__file__))

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
    parser.add_option("--log", dest="logfilename",
                      help="file name for logging")
    
    (options, args) = parser.parse_args()
    return (options, args)

def rmtreeOnError(func, path, exc):
    # try to change permissions to readwrite and retry the function
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        func(path)
    except:
        raise

def getLogFunction(logFileName):
    def nullFunc(*args, **kwargs):
        pass
    if not logFileName:
        return nullFunc
    else:
        import logging
        logging.basicConfig(
            level = logging.DEBUG,
            filename = logFileName,
            filemode = "a",
            format = "%(asctime)-15s %(filename)10s:%(lineno)4d:%(funcName)s: %(message)s"
        )
        logger = logging.getLogger()
        return logger.info

(options, args) = parseOptions()

if not options.destination:
    parser.print_help()
    sys.exit(1)

log = getLogFunction(options.logfilename)

if options.current_version is not None and options.current_build is not None:
    if options.current_version==miner_version.version and int(options.current_build)==miner_version.build:
        print "Not updated, miner version is the same: %s build %d" % (miner_version.version, miner_version.build)
        log("Not updated, miner version is the same: %s build %d" , miner_version.version, miner_version.build)
        sys.exit()

print "\nUpgrade started, please wait"    
if options.recovery_location:
    minerRecovery = os.path.join(options.recovery_location, "miner")
    print "Creating recovery folder at %s ..." % minerRecovery
    log("Creating recovery at %s", options.recovery_location)
    if not os.path.isdir(options.recovery_location):
        log("makedirs %s", options.recovery_location)
        os.makedirs(options.recovery_location)
    if os.path.isdir(minerRecovery):
        log("rmtree %s", minerRecovery)
        shutil.rmtree(minerRecovery, onerror=rmtreeOnError)
    log("copytree from %s to %s ...", options.destination, minerRecovery)
    shutil.copytree(src=options.destination, dst=minerRecovery)
    log(">>copytree ended")

print "Start copying files ..."
for newFileName in os.listdir(minerBaseDir):
    destFilePath = os.path.join(options.destination, newFileName)
    if os.path.isfile(destFilePath):
        try:
            log("remove file %s", destFilePath)
            os.unlink(destFilePath)
        except Exception as e:
            log("Failed to remove: %s will try to change permissions and retry", e)
            rmtreeOnError(os.unlink, destFilePath, e)
        if destFilePath.endswith(".py") and os.path.isfile(destFilePath+"c"):
            # if there is "pyc" for relevant python file - remove it as well
            destFilePathPyc = destFilePath + "c"
            log("remove file %s", destFilePathPyc)
            try:
                os.unlink(destFilePathPyc)
            except Exception as e:
                log("Failed to remove: %s will try to change permissions and retry", e)
                rmtreeOnError(os.unlink, destFilePathPyc, e)
             
    elif os.path.isdir(destFilePath):
        log("rmtree %s", destFilePath)
        shutil.rmtree(destFilePath, onerror=rmtreeOnError)
    elif os.path.islink(destFilePath):
        log("remove link file %s", destFilePath)
        os.unlink(destFilePath)
    
    newFilePath = os.path.join(minerBaseDir, newFileName)
    if os.path.isfile(newFilePath):
        log("copy2 from %s to %s", newFilePath, options.destination)
        shutil.copy2(newFilePath, options.destination)
    elif os.path.isdir(newFilePath):
        log("copytree from %s to %s", newFilePath, options.destination)
        shutil.copytree(newFilePath, destFilePath)

print "Upgrade finished successfully!"
