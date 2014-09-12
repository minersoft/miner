import source_base
import os
import shutil

class SourceArchive(source_base.SourceBase):
    def __init__(self, scheme, path, version=None, build=None):
        source_base.SourceBase.__init__(self, scheme, path, version, build)

    def prepare(self, toolName, toolbox, path=None):
        """Installs tool from the path specified.
        Returns True if tool was installed successfully"""
        if not path:
            path = self.path
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
            shutil.rmtree(self.prepareDir, ignore_errors=True)
        return self.prepareDir

    def getPreparedToolRootDir(self):
        topFiles = os.listdir(self.prepareDir)
        if len(topFiles)!=1:
            print "Archive should contain single directory at the top level"
            return None
        srcPath = os.path.join(self.prepareDir, topFiles[0])
        if not os.path.isdir(srcPath):
            print "Archive doesn't contain top level directory"
            return None
        return srcPath
        
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
        