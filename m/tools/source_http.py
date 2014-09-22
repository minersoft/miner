from source_archive import SourceArchive
import urllib2
import re
import os

class SourceHttp(SourceArchive):
    READ_SZ = 128*1024
    def __init__(self, scheme, path, version=None, build=None):
        SourceArchive.__init__(self, scheme, path, version, build)
    
    def prepare(self, toolName, toolbox, path=None, check_modification=False, last_modified=None, etag=None):
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
            print "Downloading %s ..." % url
            req = urllib2.Request(url)
            if last_modified:
                req.add_header('If-Modified-Since', last_modified)
            if etag:
                req.add_header("If-None-Match", etag)

            result = urllib2.urlopen(req)
        except urllib2.URLError as e:
            print "Failed to download %s - %s" % (url, e.reason)
            return False
        except urllib2.HTTPError as httpError:
            httpStatus = httpError.code 
            if httpStatus == 304:
                print "%s was not modified" % url
                self.last_modified = last_modified
                self.etag = etag
                return False
            elif httpStatus != 200:
                print "Status code is not OK", httpStatus
                return False
        if check_modification:
            self.last_modified = result.headers.get("last-modified")
            self.etag = result.headers.get("etag")
            
            # even if response is 200 check if it was not modified
            if (last_modified is not None) or (etag is not None):
                if (last_modified is not None) and (last_modified == self.last_modified) or \
                   (etag is not None) and (etag == self.etag):
                    print "%s appears to be the same" % url
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
        #if res:
        #    os.unlink(downloadFileName)
        return res
    
    def saveResult(self, downloadFileName, result, toolbox):
        toolbox.createDownloadsPath()
        if os.path.isfile(downloadFileName):
            os.unlink(downloadFileName)
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
        