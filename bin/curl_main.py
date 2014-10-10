#
# Copyright Michael Groys, 2014
#
import optparse
import sys
import urllib2


usage = "Usage: curl [<options>] <url>"
parser = optparse.OptionParser(usage=usage, version="1.0", prog="curl")
def parseOptions():
    parser.add_option("-i", "--include", dest="include_headers", action="store_true",
                      help="Include the HTTP-header in the  output")
    parser.add_option("-H", "--header", dest="headers", action="append",
                      help="Extra header to use when getting a web page")
    parser.add_option("-o", "--output", dest="file",
                      help="Write output to <file> instead of  stdout")

    (options, urls) = parser.parse_args()
    return (options, urls)

(options, urls) = parseOptions()

if not urls:
    print "No urls specified"

def openFile(options):
    if options.file:
        try:
            out = open(options.file, "wb")
        except Exception as e:
            print >>sys.stderr, "Failed to open %s for writing" % options.file
            print str(e)
            sys.exit(1)
    else:
        out = sys.stdout
    return out


def dumpResult(options, result, out):
    READ_SZ = 128 * 1024
    if options.include_headers:
        print >> out, str(result.headers)
    
    while True:
        data = result.read(READ_SZ)
        if not data:
            break
        out.write(data)
    out.close()

out = openFile(options)

headers = options.headers if options.headers else []

for url in urls:
    req = urllib2.Request(url)
    for header in headers:
        try:
            headerName, headerValue = header.split(':', 1)
            headerValue = headerValue.lstrip()
            req.add_header(headerName, headerValue)
        except:
            print >>sys.stderr, "Invalid header %s, skipped" % header

    try:
        result = urllib2.urlopen(req)
    except urllib2.URLError as e:
        print >>sys.stderr, str(e)
        sys.exit(22)
    dumpResult(options, result, out)

if out != sys.stdout:
    out.close()

    
