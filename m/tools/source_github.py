from source_http import SourceHttp

class SourceGithub(SourceHttp):

    def __init__(self, scheme, path, version=None, build=None):
        SourceHttp.__init__(self, scheme, path, version, build)
    def prepare(self, toolName, toolbox, path=None, if_differs_from=None):
        if not path:
            path = self.path
        
        elements = path.split("/")
        if len(elements)<5 or len(elements)>6:
            print "The format of github path is github:///<org-name>/<repos-name>[/v<version-number>]"
            return False
        if len(elements)==5:
            if self.version:
                versionStr = "/v" + self.version
            else:
                versionStr = ""
        else:
            versionStr = "/" + elements[5]
        httpUrl = "https://api.github.com/repos/%s/%s/tarball%s" % (elements[3], elements[4], versionStr)
        if if_differs_from is not None:
            # Ignore http identity tags and leave only with md5sum
            copy_if_differs_from = if_differs_from.copy()
            if "etag" in copy_if_differs_from:
                del copy_if_differs_from["etag"]
            if "last-modified" in copy_if_differs_from:
                del copy_if_differs_from["last-modified"]
        else:
            copy_if_differs_from = None
        res = SourceHttp.prepare(self, toolName, toolbox, path=httpUrl,
                                if_differs_from = copy_if_differs_from)
        # Ignore http identity tags and leave only with md5sum
        if "etag" in self.toolIdentity:
            del self.toolIdentity["etag"]
        if "last-modified" in self.toolIdentity:
            del self.toolIdentity["last-modified"]
        return res
    
