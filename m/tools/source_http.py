from source_archive import SourceArchive
import urllib2
import re
import os

class SourceHttp(SourceArchive):
    READ_SZ = 128*1024
    def __init__(self, scheme, path, version=None, build=None):
        SourceArchive.__init__(self, scheme, path, version, build)
    
    def prepare(self, toolName, toolbox, path=None):
        if not path:
            if self.scheme not in ["http", "https", "ftp"]:
                print "Unsupported installation scheme: %s" % self.scheme
                return False
            url = self.scheme + ":" + self.path
        else:
            url = path
        match = re.search(r"\.(zip|tar|tar\.gz|tgz)(\?|$)", self.path)
        if match:
            ext = match.group(1)
        else:
            ext = None
        
        try:
            result = urllib2.urlopen(url)
        except urllib2.URLError as e:
            print "Failed to download %s - %s" % (url, e.reason)
            return False
        if not ext:
            contentType = result.headers.get("content-type")
            #print "content-type", contentType
            if contentType == "application/x-tar":
                ext = "tar"
            elif contentType == "application/x-gtar":
                ext = "tgz"
            elif contentType == "application/zip":
                ext = "zip"
            else:
                contentDisposition = result.headers.get("content-disposition")
                if contentDisposition:
                    match = re.search(r'filename=.*\.(zip|tar|tar\.gz|tgz)($|\"| )', contentDisposition)
                    if match:
                        ext = match.group(1)
                    else:
                        print "According to Content-Disposition:'%s' - it is not an archive" % contentDisposition
                else:
                    print "Failed to extract Archive type from Content-Type: %s and there is no Content-Disposition" % contentType
        if not ext:
            result.close()
            return False
        downloadFileName = os.path.join(toolbox.getDownloadsPath(), toolName+"."+ext)
        if not self.saveResult(downloadFileName, result, toolbox):
            result.close()
            return False
        result.close()
        res = SourceArchive.prepare(self, toolName, toolbox, path=downloadFileName)
        if res:
            os.unlink(downloadFileName)
        return res
    
    def saveResult(self, downloadFileName, result, toolbox):
        toolbox.createDownloadsPath()
        
        out = open(downloadFileName, "wb")
        leftToRead = int(result.headers.get("content-length", -1))
        while True:
            data = result.read(SourceHttp.READ_SZ)
            if not data:
                break
            out.write(data)
            leftToRead -= len(data)
        out.close()
        if leftToRead > 0:
            print "Not all data was downloaded missing %d bytes" % leftToRead
            return False
        else:
            return True
        