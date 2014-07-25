class SourceBase(object):
    def __init__(self):
        pass
    
    def getFile(self, scheme, path, toolbox, version=None, build=None):
        """Returns content of the file as string"""
        raise NotImplemented
    
    def install(self, scheme, path, dest, toolbox, version=None, build=None):
        """Installs tool from the path specified.
        Returns True if tool was installed successfully"""
        raise NotImplemented

    @staticmethod
    def spliturl(url):
        if not url:
            return None
        parts = url.split("://", 1)
        if len(parts) == 1:
            return ("file", url)
        return (parts[0], "//" + parts[1])