from source_http import SourceHttp

class SourceGithub(SourceHttp):

    def __init__(self, scheme, path, version=None, build=None):
        SourceHttp.__init__(self, scheme, path, version, build)
    def prepare(self, toolName, toolbox, path=None, check_modification=False, last_modified=None, etag=None):
        if not path:
            path = self.path
        
        elements = path.split("/")
        if len(elements)<5 or len(elements)>6 or (len(elements)==5 and not self.version):
            print "The format of github path is github:///<org-name>/<repos-name>[/v<version>]"
            return False
        if len(elements)==5:
            version = "v" + self.version
        else:
            version = elements[5]
        httpUrl = "https://api.github.com/repos/%s/%s/tarball/%s" % (elements[3], elements[4], version)
        return SourceHttp.prepare(self, toolName, toolbox, path=httpUrl,
                                  check_modification=check_modification, last_modified=last_modified, etag=etag)
    
