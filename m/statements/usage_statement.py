import miner_globals
import sys
import m.common

def p_usage_statement(p):
    '''statement : USAGE STRING usage_params'''
    Usage.execute(p[2][1:-1], p[3])

# usage statement

def p_usage_params(p):
    '''usage_params : usage_param'''
    p[0] = [ p[1] ]

def p_usage_params_param(p):
    '''usage_params :  usage_params usage_param'''
    p[0] = p[1]
    p[0].append(p[2])

def p_usage_param(p):
    '''usage_param : ID  '=' STRING
                   | '*' '=' STRING
                   | '>' '=' STRING
                   | INTEGER '=' STRING'''
    p[0] = { 'name': p[1], 'description': p[3][1:-1] }

def p_usage_param_GE(p):
    '''usage_param : GE STRING'''
    p[0] = { 'name': '>', 'description': p[2][1:-1] }

def p_usage_param_optional(p):
    '''usage_param : '[' usage_param ']' '''
    p[0] = p[2]
    p[0]['isOptional'] = 1

def p_usage_param_optional_with_default(p):
    '''usage_param : '[' usage_param DEFAULT STRING ']' '''
    p[0] = p[2]
    p[0]['isOptional'] = 1
    p[0]['default'] = p[4][1:-1]

###########################################################################################

class Usage:
    NAME = "USAGE"
    SHORT_HELP = 'USAGE "script description" name="description" [name2=".." [DEFAULT "value"]] *=".." >=".."'
    LONG_HELP = """USAGE "script description"
                         name="description"
                         [name2="description"]
                         [name3="description" DEFAULT "value"]
                         *="description"
                         >="description"
USAGE command validates that all required script parameters were provided otherwise it prints
    usage and exits.
    []  - means optional parameter
    * - positional parameters, usually used for input files (can be optional), accessed by $* or $1, $2
    >  - output parameter, can be optional, specified in script by -o <>, accessed by $>
    DEFAULT "value" - specifies default value for optional parameter
"""
    @staticmethod
    def execute(scriptDescription, parameterList):
        if miner_globals.printUsage:
            Usage.printUsageAndExit(scriptDescription, parameterList)
        for p in parameterList:
            if "isOptional" not in p:
                if p["name"] == "*" and "1" not in miner_globals.scriptParameters:
                    Usage.printUsageAndExit(scriptDescription, parameterList)
                elif p["name"] not in miner_globals.scriptParameters:
                    Usage.printUsageAndExit(scriptDescription, parameterList)
            elif p["name"] not in miner_globals.scriptParameters and \
                 "default" in p:
                miner_globals.setScriptParameter(p["name"], p["default"])

    @staticmethod
    def printUsageAndExit(scriptDescription, parameterList):
        commandParams = []
        for p in parameterList:
            if p["name"].isdigit():
                commandParams.append("<arg%s>" % p["name"])
            elif p["name"] == "*":
                commandParams.append("args ...")
            elif p["name"] == ">":
                commandParams.append("-o <..>")
            else:
                commandParams.append("%s=.." % p["name"])
            if "isOptional" in p:
                commandParams[-1] = "[" + commandParams[-1] + "]"
        print "Usage: %s %s" % (miner_globals.getCurrentScriptPath(), " ".join(commandParams))
        print scriptDescription
        for p in parameterList:
            if p["name"].isdigit():
                name = "arg%s" % p["name"]
            elif p["name"] == "*":
                name = "args"
            elif p["name"] == ">":
                name = "-o <..>"
            else:
                name = p["name"]
            if 'default' in p:
                defaultStr = ", by default - %s" % p["default"]
            else:
                defaultStr = ""
            print "  %-14s - %s%s" % (name, p["description"], defaultStr)
        raise m.common.ReturnFromScript()

miner_globals.addHelpClass(Usage)
miner_globals.addStatementName("USAGE")

