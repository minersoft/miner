#
# Copyright Qwilt, 2012
#
# The code contained in this file may not be used by any other entities without explicit written permission from Qwilt.
#
# Author: michaelg
# 

#
# This file implements expressions used in commands
# Two Expressions classes are available:
#   Expression - general Expression which are translated as is to python expressions
#   MatchExpression - uses regular expressions for match statements
#

EXP_TYPE_UNKNOWN = ""
EXP_TYPE_ATOMIC  = "atomic"
EXP_TYPE_COAL    = "coal"
EXP_TYPE_ACCUMULATED = "accumulated"
EXP_TYPE_DIAMOND = "diamond"


class Expression:
    def __init__(self):
        self.name = ""
        self.exp = ""
        self.myType = EXP_TYPE_UNKNOWN
        self.myGlobalExpressions = []

    def setDeref(self, expParent, childName):
        self.name = childName
        self.exp = expParent.exp + "." + childName
        self.myGlobalExpressions = expParent.getGlobalExpressions()
    def setBinary(self, left, op, right):
        self.exp = "%s %s %s" % (left.exp, op, right.exp)
        self.myGlobalExpressions = left.getGlobalExpressions() + right.getGlobalExpressions()
    def setUnary(self, op, exp):
        self.name = ""
        self.exp = op + " " + exp.exp
        self.myGlobalExpressions = exp.getGlobalExpressions()
    def setListAccess(self, exp, indexExp):
        self.name = indexExp.getName()
        self.exp = "%s[%s]" % (exp.exp, indexExp.exp)
        self.myGlobalExpressions = exp.getGlobalExpressions() + indexExp.getGlobalExpressions()
    def setListRange(self, exp, fromExp, toExp):
        self.name = ""
        self.myGlobalExpressions = exp.getGlobalExpressions()
        if fromExp and toExp:
            self.exp = "%s[%s:%s]" % (exp.exp, fromExp.getValue(), toExp.getValue())
            self.myGlobalExpressions += fromExp.getGlobalExpressions() + toExp.getGlobalExpressions()
        elif fromExp:
            self.exp = "%s[%s:]" % (exp.exp, fromExp.getValue())
            self.myGlobalExpressions += fromExp.getGlobalExpressions()
        elif toExp:
            self.exp = "%s[:%s]" % (exp.exp, toExp.getValue())
            self.myGlobalExpressions += toExp.getGlobalExpressions()
        else:
            self.exp = "%s[:]" % exp.exp
        
    def setFunctionCall(self, exp, parameters, namedParameters):
        self.name = ""
        if not parameters and not namedParameters:
            self.exp = "%s()" % exp.getValue()
        elif not namedParameters:
            self.exp = "%s(%s)" % (exp.getValue(), ", ".join(e.getValue() for e in parameters))
        elif not parameters:
            self.exp = "%s(%s)" % (exp.getValue(), ", ".join(e.getValue() for e in namedParameters))
        else:
            self.exp = "%s(%s, %s)" % (exp.getValue(), 
                ", ".join(e.getValue() for e in parameters),
                ", ".join(e.getValue() for e in namedParameters))
        self.myGlobalExpressions = exp.getGlobalExpressions()
        if parameters:
            for exp in parameters:
                self.myGlobalExpressions.extend(exp.getGlobalExpressions())
        if namedParameters:
            for exp in namedParameters:
                self.myGlobalExpressions.extend(exp.getGlobalExpressions())
    def setList(self, listOfExpressions):
        self.name = ""
        for exp in listOfExpressions:
            self.myGlobalExpressions.extend(exp.getGlobalExpressions())
        listStr = ", ".join(exp.getValue() for exp in  listOfExpressions)
        self.exp = '[' + listStr + ']'
    def setAssignment(self, name, exp):
        self.exp = "%s = %s" % (name , exp.getValue())
        self.name = name
        self.myGlobalExpressions = exp.getGlobalExpressions()
    def setId(self, id):
        self.name = id
        self.exp = id
    def setValue(self, value):
        self.name = ""
        self.exp = value
    def getName(self):
        return self.name
    def setName(self, name):
        self.name = name
    def getValue(self):
        return self.exp
    def __str__(self):
        return self.exp
    def setBracketExpression(self, exp):
        self.exp = "( " + exp.exp + " )"
        self.name = exp.name
        self.myGlobalExpressions = exp.getGlobalExpressions()
    def getGlobalExpressions(self):
        return self.myGlobalExpressions
    def getGlobalSection(self):
        return ""
    def setConditional(self, ifExp, thenExp, elseExp):
        self.name = ""
        self.exp = "(%s if %s else %s)" % (thenExp.getValue(), ifExp.getValue(), elseExp.getValue())
        self.myGlobalExpressions = ifExp.getGlobalExpressions() + thenExp.getGlobalExpressions() + elseExp.getGlobalExpressions()
    def setTupleWithComa(self, expressions):
        self.name = ""
        self.exp = "(" + "".join("%s, "%e.getValue() for e in expressions ) + ")"
        for e in expressions:
            self.myGlobalExpressions += e.getGlobalExpressions()
    def setTupleWithoutComa(self, expressions):
        self.name = ""
        self.exp = "(" + ", ".join(e.getValue() for e in expressions ) + ")"
        for e in expressions:
            self.myGlobalExpressions += e.getGlobalExpressions()
    def setListComprehension(self, itemExpression, iteratorId, listExpression):
        self.name = ""
        self.exp = "%s for %s in %s" % (itemExpression.getValue(), iteratorId, listExpression.getValue())
        self.myGlobalExpressions = itemExpression.getGlobalExpressions() + listExpression.getGlobalExpressions()
    def setDictionaryItems(self, itemsList):
        s = ", ".join("%s: %s" % (key, value) for (key, value) in itemsList)
        self.name = ""
        self.exp = "{ " + s + " }"
        self.myGlobalExpressions = []
        for (key, value) in itemsList:
            self.myGlobalExpressions.extend(key.getGlobalExpressions())
            self.myGlobalExpressions.extend(value.getGlobalExpressions())
    def setLambda(self, paramList, expression):
        self.exp = "lambda " + ", ".join(paramList) + ": "
        self.exp += expression.getValue()
        self.name = ""

class MatchExpression(Expression):
    _expressionId = 1
    def __init__(self, exp, regExp, negate = False):
        Expression.__init__(self)
        self.name = ""
        self.myRegExp = regExp
        self.myId = MatchExpression._expressionId
        MatchExpression._expressionId += 1
        self.myGlobalExpressions = exp.getGlobalExpressions() + regExp.getGlobalExpressions() + [self]
        self.exp = "_regExp%d.search(%s)" % (self.myId, exp.exp)
        if negate:
            self.exp = "(not %s)" % self.exp

    def getGlobalSection(self):
        return "    _regExp%d = re.compile(%s)\n" % (self.myId, self.myRegExp.exp)

class CounterExpression(Expression):
    def __init__(self, name):
        Expression.__init__(self)
        self.name = name
        self.exp = "%s.val" % self.name
        self.myGlobalExpressions = [self]

    def getGlobalSection(self):
        return "    %s = _runtime.Counter()\n" % self.name

    def preIncr(self):
        self.exp = "%s.preIncr()" % self.name
    def postIncr(self):
        self.exp = "%s.postIncr()" % self.name
    def preDecr(self):
        self.exp = "%s.preDecr()" % self.name
    def postDecr(self):
        self.exp = "%s.postDecr()" % self.name
    def add(self, exp):
        self.exp = "%s.add(%s)" % (self.name, exp.getValue())
        self.myGlobalExpressions += exp.getGlobalExpressions()
    def sub(self, exp):
        self.exp = "%s.sub(%s)" % (self.name, exp.getValue())
        self.myGlobalExpressions += exp.getGlobalExpressions()
    def method(self, methodName, expressionList):
        self.exp = "%s.%s(%s)" % (self.name, methodName, ", ".join([e.getValue() for e in expressionList]))
        for exp in expressionList:
            self.myGlobalExpressions += exp.getGlobalExpressions()


class DictCounterExpression(CounterExpression):
    def __init__(self, name, indexExp):
        self.realName = name
        CounterExpression.__init__(self, "_%s_dict[%s]" % (name, indexExp.getValue()))
        self.indexExp = indexExp
        self.myGlobalExpressions = [self] + indexExp.getGlobalExpressions()

    def getName(self):
        return self.realName
    
    def getGlobalSection(self):
        return "    _%s_dict = collections.defaultdict(_runtime.Counter)\n" % self.realName

