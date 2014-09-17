import source_base
import os
import shutil

class SourceArchive(source_base.SourceBase):
    def __init__(self, scheme, path, version=None, build=None):
        source_base.SourceBase.__init__(self, scheme, path, version, build)

    def prepare(self, toolName, toolbox, path=None, check_modification=False, last_modified=None, etag=None):
        """Installs tool from the path specified.
        Returns True if tool was installed successfully"""
        if not path:
            path = self.path
        if check_modification:
            try:
                statData = os.stat(path)
                self.setLastModified(statData.st_mtime)
                if (last_modified is not None) and (last_modified == self.last_modified):
                    print "Directory %s was not modified" % path
                    return False
            except OSError:
                pass
        if path.endswith(".tar") or path.endswith("tar.gz"):
            return self.prepareTar(path, toolName, toolbox)
        elif path.endswith(".zip"):
            return self.prepareZip(path, toolName, toolbox)
        else:
            print "Unsupported archive format", self.path
            return False

    @staticmethod
    def isValidFileName(fileName):
        if fileName.startswith("/"):
            return False
        if ".." in fileName.split("/"):
            return False
        return True

    def _initExtractPath(self, toolName, toolbox):
        toolbox.createDownloadsPath()
        self.prepareDir = os.path.join(toolbox.getDownloadsPath(), "%s_extract" % toolName)
        if os.path.isdir(self.prepareDir):
            shutil.rmtree(self.prepareDir)
        return self.prepareDir

    def getPreparedToolRootDir(self):
        topFiles = os.listdir(self.prepareDir)
        dir = None
        for f in topFiles:
            srcPath = os.path.join(self.prepareDir, f)
            if os.path.isdir(srcPath):
                if dir:
                    print "Archive should contain single directory at the top level"
                    return None
                else:
                    dir = srcPath
        return dir
        
    def installFiles(self, destPath, toolbox):
        srcPath = self.getPreparedToolRootDir()
        if os.path.isdir(destPath):
            shutil.rmtree(destPath, ignore_errors=True)
        shutil.move(srcPath, destPath)
        return True
    
    def prepareZip(self, path, toolName, toolbox):
        import zipfile
        zip = zipfile.ZipFile(path)
        if not os.path.isfile(path):
            print "File %s doesn't exist or is not a file" % path
            return False
        def files(aZip):
            return filter(SourceArchive.isValidFileName, aZip.namelist())
        extractPath = self._initExtractPath(toolName, toolbox)
        try:
            print "Extracting zip archive %s ..." % path 
            zip = zipfile.ZipFile(path, "r")
            zip.extractall(path=extractPath, members=files(zip))
            zip.close()
        except zipfile.BadZipfile as bzf:
            print "tar file extraction error occurred: %s" % str(bzf)
            return False
        except IOError as ioerror:
            print str(ioerror)
            return False
        except OSError as oserror:
            print str(oserror)
            return False
        return True
    
    def prepareTar(self, path, toolName, toolbox):
        import tarfile
        def files(members):
            for tarinfo in members:
                if SourceArchive.isValidFileName(tarinfo.name):
                    yield tarinfo

        if not os.path.isfile(path):
            print "File %s doesn't exist or is not a file" % path
            return False
        succeeded = False
        extractPath = self._initExtractPath(toolName, toolbox)
        try:
            print "Extracting tar archive %s ..." % path 
            tar = tarfile.open(path)
            tar.extractall(path=extractPath, members=files(tar))
            tar.close()
        except tarfile.TarError as te:
            print "tar file extraction error occurred: %s" % str(te)
            return False
        except IOError as ioerror:
            print str(ioerror)
            return False
        except OSError as oserror:
            print str(oserror)
            return False
        return True
        