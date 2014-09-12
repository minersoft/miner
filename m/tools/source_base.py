import shutil

class SourceBase(object):
    def __init__(self, scheme, path, version=None, build=None):
        self.scheme = scheme
        self.path = path
        self.version = version
        self.build = build
        self.prepareDir = None
    
    def prepare(self, toolName, toolbox, path=None):
        """Prepares install sources for actual installation (e.g. download, extract) Updates prepareDir.
        Returns true if prepare stage succeeded"""
        raise NotImplementedError()
    
    def getPreparedToolRootDir(self):
        """returns root directory of tool code""" 
        raise NotImplementedError()
    
    def installFiles(self, dest, toolbox):
        """Installs files after preparation phase.
        Returns True if tool was installed successfully"""
        raise NotImplementedError()

    def clearPrepare(self):
        if self.prepareDir:
            shutil.rmtree(self.prepareDir, ignore_errors=True)
    
    def install(self, toolName, toolbox):
        """Full tool installation"""
        res = self.prepare(toolName, toolbox)
        if not res:
            return False
        res = self.installFiles(toolbox.getToolPath(toolName), toolbox)
        if res:
            self.clearPrepare()
        return res
            
    @staticmethod
    def spliturl(url):
        if not url:
            return None
        parts = url.split("://", 1)
        if len(parts) == 1:
            return ("file", url)
        return (parts[0], "//" + parts[1])