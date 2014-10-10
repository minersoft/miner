#!/usr/local/bin/python2.6

import optparse
import sys
import os
import miner_version
import miner_globals

usage = "Usage: %prog [options] [<param>=<value> ...] ..."
parser = optparse.OptionParser(usage=usage, version=miner_version.version, prog="miner")

def parseOptions():
    parser.add_option("-c", "--command", dest="commands", action="append",
                      help="specify command to execute")
    parser.add_option("-m", "--mining", dest="miningCommand",
                      help="specify actual mining command files to read/write will be taken from command line")
    parser.add_option("-u", "--use", dest="uses", action="append",
                      help="specifies miner modules to use prior to running miner command/scripts")
    parser.add_option("-a", "--alias", dest="aliases", action="append",
                      help="specify alias to create: -a 'name=<chain>'")
    parser.add_option("-s", "--set", dest="variables", action="append",
                      help="specify variable to create: -s 'name=<expression>'")
    parser.add_option("-i", dest="imports", action="append",
                      help="specify import module to add")
    parser.add_option("-o", "--output", dest="output",
                      help="specify output path for scripts")
    parser.add_option("-f", "--file", dest="scriptFileName",
                      help="specify miner script to execute")
    parser.add_option("-d", dest="debugmodes", action="append_const", const="main",
                      help="Creates miner.log file with basic logging")
    parser.add_option("--debug", dest="debugmodes", action="append",
                      help="allows to specify detailed logging targets")
    parser.add_option("-x", "--echo", dest="echo", action="store_true",
                      help="runs miner in echo mode where each command is printed before being executed")
    parser.add_option("--path", dest="pythonpath", action="append",
                      help="specify additional path to python modules")
    parser.add_option("--spath", dest="scriptpath", action="append",
                      help="specify additional path to miner scripts (used by SOURCE command)")
    parser.add_option("--usage", dest="scriptusage", action="store_true",
                      help="gets script usage information")
    parser.add_option("--profile", dest="profile",
                      help="run with profiling, save output to file")
    parser.add_option("--pyreadline-log", dest="pyreadlineLog",
                      help="enables logging of pyreadline library")
    parser.add_option("--tools-path", dest="toolspath",
                      help="specify path where to install minere tool (by default ~/miner-tools)")
    parser.add_option("--home-dir", dest="homedir", default="~",
                      help="specify specifies alternative home directory instead of '~'")
    parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                      help="Runs miner in quiet mode (don't show  'Mining ...' messages)")
    parser.add_option("--list-scripts", dest="listscripts", action="store_true",
                      help="lists scripts from installed tools")
    
    (options, args) = parser.parse_args()
    return (options, args)

def listScripts(toolsDir):
    tools = []
    for tool in os.listdir(toolsDir):
        if os.path.isdir(os.path.join(toolsDir, tool)):
            tools.append(tool)
    tools.sort()
    def getScripts(tool):
        toolDir = os.path.join(toolsDir, tool)
        scripts = []
        for file in os.listdir(toolDir):
            if file.endswith(".miner") and file[0]!="." and file[0]!="_" and file!="init.miner":
                scripts.append(file[:-6])
        return sorted(scripts)
    for tool in tools:
        scripts = getScripts(tool)
        if scripts:
            print "In %s toolbox:" % tool
            for script in scripts:
                print "  %s.%s" % (tool, script)

    
(options, args) = parseOptions()

if options.pythonpath:
    #print "Updating pythonpath"
    for p in options.pythonpath:
        sys.path.append(p)

# for IMPORT statements
sys.path.append(os.getcwd())

miner_globals.minerBaseDir = os.path.dirname(os.path.abspath(__file__))

if miner_globals.minerBaseDir not in sys.path:
    sys.path.append(miner_globals.minerBaseDir)

# add my lib folder to python path
sys.path.append(os.path.join(miner_globals.minerBaseDir, "lib"))

if options.pyreadlineLog:
    miner_globals.setPyreadlineLog(options.pyreadlineLog)

miner_globals.setHomeDir(options.homedir)

MINERRC_FILE = os.path.join(miner_globals.getHomeDir(), ".minerrc")

from m import executor

if options.debugmodes:
    executor.setDebugModes(options.debugmodes)
if options.output:
    miner_globals.setOutputFile(options.output)
if options.scriptpath:
    executor.setScriptPath(options.scriptpath)
if options.scriptusage:
    miner_globals.setPrintUsage()
if options.echo:
    miner_globals.setEchoMode(True)
if options.toolspath:
    miner_globals.setToolsPath(options.toolspath)
if options.quiet:
    miner_globals.setVerbose("False")
if options.listscripts:
    listScripts(miner_globals.getToolsPath())
    sys.exit(0)

miner_globals.loadRegistry()
miner_globals._executeScript = executor.executeScript

miner_globals.setScriptParameters(args)
executor.createImports(options.imports)
executor.createAliases(options.aliases)
executor.createVariables(options.variables)

if options.uses:
    for toolName in options.uses:
        miner_globals.useTool(toolName)

if not sys.stdout.isatty():
    # reopen stdout file in line buffering mode
    sys.stdout = os.fdopen( sys.stdout.fileno(), 'w', 1 )

def runIt (executor, options):
    if options.miningCommand:
        executor.execute("READ $* | %s | WRITE $>" % options.miningCommand)
    elif options.commands:
        executor.executeCommands(options.commands)
    elif options.scriptFileName:
        miner_globals.callScript(options.scriptFileName)
    else:
        from m import interactive
        minerrcFile = os.path.expanduser(MINERRC_FILE)
        if os.path.isfile(minerrcFile):
            executor.executeScript(minerrcFile)
        interactive.runInteractive()

if not options.profile:
    runIt(executor, options)
else:
    import cProfile
    cProfile.run('runIt(executor, options)', options.profile)

