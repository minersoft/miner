#
# Copyright Michael Groys, 2012-2014
#

#
# This file implements completion logic
# and runInteractive() function for interactive mode
#
# on windows platform completion logic requires manual installation of pyreadline package
#

import executor
import commands
import atexit
import os
import sys
import traceback
import miner_version
import miner_globals
import completer
import signal

pathToScript = os.path.dirname(sys.argv[0])
historyFileName = miner_globals.getHistoryFile()

#if sys.platform.startswith("win") or miner_globals.runsUnderPypy:
if True:
    # always use pyreadline
    import readline_replacement as readline
    sys.modules['readline'] = readline
    import pyreadline.rlmain
    readline.rl.read_inputrc(os.path.join(pathToScript, "pyreadlineconfig.py"))
    if miner_globals.pyreadlineLogFile:
        import pyreadline.logger
        pyreadline.logger.start_file_log(miner_globals.pyreadlineLogFile)
else:
    import readline
    readline.read_init_file(os.path.join(pathToScript, "readline.ini"))
    readline.set_completer_delims(" \t\n\"\\/-+*^%:~!%'`@$><=,;|&{}()?:[]")

readline.parse_and_bind("tab: complete")

if sys.platform.startswith('linux') or sys.platform=='darwin':
    def interactiveSIGHUP(signum, frame):
        sys.exit(0)

    signal.signal(signal.SIGHUP, interactiveSIGHUP)

try:
    readline.read_history_file(historyFileName)
except IOError:
    pass

atexit.register(readline.write_history_file, historyFileName)

def runInteractive():
    """
    Main function for interactive mode
    """
    print "------------- Welcome to the Miner %s ----------------" % miner_version.version
    print "You can run HELP command anytime to get more information."
    print "Press TAB key for context base completion"
    print "    - F1  key to get miner command help"
    print "    - F2  key to get python documentation"
    print "    - Ctrl-K to get list of keyboard bindings"
    print "    - Ctrl-D to exit"
    miner_globals.setIsInteractive(True)
    while True:
        s = ""
        try:
            s = raw_input(">>> ")
        except KeyboardInterrupt:
            print
            continue
        except EOFError:
            break
        if not s: continue
        executor.execute(s)

    print "\nGoodbye"

