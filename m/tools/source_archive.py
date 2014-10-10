import source_base
import os
import shutil
import m.loggers as loggers

class SourceArchive(source_base.SourceBase):
    def __init__(self, scheme, path, version=None, build=None):
        source_base.SourceBase.__init__(self, scheme, path, version, build)

    def prepare(self, toolName, toolbox, path=None, if_differs_from=None):
        """Installs tool from the path specified.
        Returns True if tool was installed successfully"""
        if not path:
            path = self.path
        md5sum = self.md5sum(path)
        self.toolIdentity["md5sum"] = md5sum
        loggers.installLog.info("Tool %s Setting toolIdentity['md5sum'] = %s from %s", toolName, md5sum, path)
        if if_differs_from is not None:
            try:
                from_md5sum = if_differs_from.get("md5sum")
                if (from_md5sum is not None) and (from_md5sum == md5sum):
                    print "Md5sum of archive %s was not modified" % path
                    loggers.installLog.info("Tool %s Md5sum (%s) was not modified - not installing", toolName, md5sum)
                    return False
            except OSError as e:
                print str(e)
        if path.endswith(".tar") or path.endswith("tar.gz"):
            res = self.prepareTar(path, toolName, toolbox)
        elif path.endswith(".zip"):
            res = self.prepareZip(path, toolName, toolbox)
        else:
            print "Unsupported archive format", self.path
            res = False
        return res
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
                    loggers.installLog.warning("Archive %s doesn't contain single directory at the top level", self.prepareDir)
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
            loggers.installLog.warning("Tool %s: File %s doesn't exist or is not a file", toolName, path)
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
            loggers.installLog.warning("zip file extraction error occurred: %s", str(bzf))
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
            loggers.installLog.warning("Tool %s: File %s doesn't exist or is not a file", toolName, path)
            return False
        extractPath = self._initExtractPath(toolName, toolbox)
        try:
            print "Extracting tar archive %s ..." % path 
            tar = tarfile.open(path)
            tar.extractall(path=extractPath, members=files(tar))
            tar.close()
        except tarfile.TarError as te:
            print "tar file extraction error occurred: %s" % str(te)
            loggers.installLog.warning("tar file extraction error occurred: %s" , str(te))
            return False
        except IOError as ioerror:
            print str(ioerror)
            return False
        except OSError as oserror:
            print str(oserror)
            return False
        return True
    def md5sum(self, fileName):
        import hashlib
        fileObj = open(fileName, "rb")
        READ_BUF_SIZE = 128*1024
        md5Obj = hashlib.md5()
        while True:
            buf = fileObj.read(READ_BUF_SIZE)
            if not buf:
                break
            md5Obj.update(buf)
        digest = md5Obj.digest().encode("hex")
        fileObj.close()
        return digest
