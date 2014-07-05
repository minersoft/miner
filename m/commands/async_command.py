import miner_globals
from base import *

def p_async_command(p):
    """command : ASYNC integer"""
    p[0] = AsyncCommand(p[2])

class AsyncCommand(CommandBase):
    NAME = "ASYNC"
    SHORT_HELP = "ASYNC <max-buffered-records> - runs previous commands in chain in different thread"
    LONG_HELP = """ASYNC <max-buffered-records>
Runs previous commands in chain in different thread, improves performance while scanning large
amounts of data, e.g.:
    READ<frecord> *.tgz | ASYNC 50000 | FOR SELECT frecord.downloadedContentBytes | STDOUT
"""
    def __init__(self, maxBuffered):
        CommandBase.__init__(self)
        self.maxBuffered = maxBuffered
    def getVariableNames(self):
        return self.myParent.getVariableNames()
    def createGenerator(self, name, parentGeneratorName):
        s = """
def %s_connector(queue):
    for record in %s():
        queue.put(record)
    queue.put(None)

def %s():
    from Queue import Queue
    from threading import Thread
    queue = Queue(%s)
    async = Thread(target=%s_connector, args=(queue,))
    async.daemon = True
    async.start()
    while True:
        record = queue.get()
        if record is None:
            break
        yield record
        queue.task_done()
    #async.join()
""" % (name, parentGeneratorName, name, self.maxBuffered, name)
        return s

miner_globals.addHelpClass(AsyncCommand)
miner_globals.addCommandName("ASYNC")
