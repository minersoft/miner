# 
# Copyright Michael Groys, 2014
#

#
# Different utils for writing unit tests
#
import inspect
from collections import Counter

class UnitTestAssert(Exception):
    def __init__(self):
        Exception.__init__(self)
    def __str__(self):
        return "Unit test failed"

_conditionFailed = Counter()

_currTest = None

def _failCondition():
    if _currTest:
        _conditionFailed[_currTest] += 1

def __check_eq(funcName, expected, actualStr, msg):
    st = inspect.stack()
    (frame, filename, lineno, function, code_context, index) = st[2]
    actual = eval(actualStr, frame.f_globals, frame.f_locals)
    if expected != actual:
        _failCondition()
        print "!!-Failed %s at %s:%d: " % (funcName, filename, lineno)
        print "     Expected %s" % expected
        print "     Not equal to %s which is: %s" % (actualStr, actual)
        if msg:
            print "       " + msg
        return False
    else:
        return True

def __check_bool(funcName, expectedBool, actualStr, msg):
    st = inspect.stack()
    (frame, filename, lineno, function, code_context, index) = st[2]
    actual = eval(actualStr, frame.f_globals, frame.f_locals)
    if actual:
        res = expectedBool
    else:
        res = not expectedBool
    if not res:
        _failCondition()
        print "!!-Failed %s at %s:%d: " % (funcName, filename, lineno)
        print "     Expected %s" % ("True" if expectedBool else "False")
        print "     Not matching %s which is: %s" % (actualStr, actual)
        if msg:
            print "       " + msg
    return res

def ASSERT_EQ(expectedStr, actualStr, msg=None):
    if not __check_eq("ASSERT_EQ", expectedStr, actualStr, msg):
        raise UnitTestAssert()

def ASSERT_TRUE(actualStr, msg=None):
    if not __check_bool("ASSERT_TRUE", True, actualStr, msg):
        raise UnitTestAssert()
def ASSERT_FALSE(actualStr, msg=None):
    if not __check_bool("ASSERT_FALSE", False, actualStr, msg):
        raise UnitTestAssert()

def EXPECT_TRUE(actualStr, msg=None):
    __check_bool("EXPECT_TRUE", True, actualStr, msg)
def EXPECT_FALSE(actualStr, msg=None):
    __check_bool("EXPECT_FALSE", False, actualStr, msg)

def EXPECT_EQ(expected, actualStr, msg=None):
    __check_eq("EXPECT_EQ", expected, actualStr, msg)

def START_TEST(name):
    global _currTest
    _currTest = name
    _conditionFailed[_currTest] = 0
    print "[Test %s started]" % _currTest
    

def END_TEST():
    global _currTest
    failedConditions = _conditionFailed[_currTest]
    if failedConditions:
        print "\n[Test %s failed! - %d unmatched conditions]\n" % (_currTest, failedConditions)
    else:
        print "[Test %s succeeded]\n" % _currTest
    _currTest = None

def test():
    START_TEST("test-ut")
    x = True
    ASSERT_TRUE("x")
    y = False
    EXPECT_TRUE("y")
    
    EXPECT_FALSE("y")
    
    EXPECT_EQ(True, "y", msg="y should be True")
    
    ASSERT_EQ(False, "y")
    END_TEST()
    