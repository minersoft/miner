import os
import source_base
import sys
import subprocess
import shutil

class SourceLocalDir(source_base.SourceBase):
    def __init__(self, scheme, path, version=None, build=None):
        source_base.SourceBase.__init__(self, scheme, path, version, build)

    def prepare(self, toolName, toolbox, path=None, if_differs_from=None):
        if not path:
            path = self.path
        self.prepareDir = path
        if if_differs_from is not None:
            try:
                statData = os.stat(path)
                self.setLastModified(statData.st_mtime)
                from_last_modified = if_differs_from.get("last-modified")
                if (from_last_modified is not None) and (from_last_modified == self.getLastModified()):
                    print "Directory %s was not modified" % path
                    return False
            except OSError as e:
                print str(e)
        return True
    
    def getPreparedToolRootDir(self):
        return self.prepareDir
    
    def clearPrepare(self):
        pass

    def installFiles(self, dest, toolbox):
        """Installs tool from the path specified.
        Returns True if tool was installed successfully"""
        path = self.prepareDir
        if not os.path.isdir(path):
            print "Local path %s is not a directory" % path
            return False
        res = SourceLocalDir.linkLocal(path, dest)
        if not res:
            return SourceLocalDir.copyLocal(path, dest)
        return res
    @staticmethod
    def linkLocal(path, dest):
        if sys.platform.startswith("linux"):
            os.symlink(path, dest)
        elif (sys.platform=="win32") and (sys.getwindowsversion().major >= 6):
            cmd = ["mklink", "/J", dest, path]
            try:
                subprocess.check_call(" ".join(cmd), shell=True)
                return True
            except subprocess.CalledProcessError:
                return False
        else:
            return False
                 
    @staticmethod
    def copyLocal(path, dest):
        try:
            shutil.copytree(path, dest)
            return True
        except shutil.Error as e:
            print str(e)
            try:
                shutil.rmtree(dest, ignore_errors=True)
            except:
                pass
            return False
            