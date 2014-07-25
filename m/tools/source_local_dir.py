import os
import source_base
import sys
import subprocess
import shutil

class SourceLocalDir(source_base.SourceBase):
    def __init__(self):
        source_base.SourceBase.__init__(self)

    def install(self, scheme, path, toolName, toolbox, version=None, build=None):
        """Installs tool from the path specified.
        Returns True if tool was installed successfully"""
        if not os.path.isdir(path):
            print "Local path %s is not a directory" % path
            return False
        res = SourceLocalDir.linkLocal(path, toolName, toolbox)
        if not res:
            return SourceLocalDir.copyLocal(path, toolName, toolbox)
        return res
    @staticmethod
    def linkLocal(path, toolName, toolbox):
        if sys.platform.startswith("linux"):
            os.symlink(path, toolbox.getToolPath(toolName))
        elif (sys.platform=="win32") and (sys.getwindowsversion().major >= 6):
            cmd = ["mklink", "/J", toolbox.getToolPath(toolName), path]
            try:
                subprocess.check_call(" ".join(cmd), shell=True)
                return True
            except subprocess.CalledProcessError:
                return False
        else:
            return False
                 
    @staticmethod
    def copyLocal(path, toolName, toolbox):
        try:
            shutil.copytree(path, toolbox.getToolPath(toolName))
            return True
        except shutil.Error as e:
            print str(e)
            try:
                shutil.rmtree(toolbox.getToolPath(toolName), ignore_errors=True)
            except:
                pass
            return False
            