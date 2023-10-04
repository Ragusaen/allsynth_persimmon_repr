from pyparsing import *
from property import *

# Token constructors
def MakeTrue(tokens):
    return TTrue()

def MakeFalse(tokens):
    return FFalse()

def MakeLoopFree(tokens):
    return LoopFreedom()

def MakeSwitchID(tokens): 
    return SwitchID(tokens[0])

def MakeConjunction(tokens):
    return Conjunction(tokens[0], tokens[1])

def MakeDisjunction(tokens):
    return Disjunction(tokens[0], tokens[1])

def MakeUntil(tokens):
    return Until(tokens[0], tokens[1])

def MakeNegation(tokens):
    return Negation(tokens[0])

def MakeReachability(tokens):
    return Reachability(tokens[0])

def MakeWaypoint(tokens):
    return WayPoint(tokens[0],tokens[1])

def MakeServiceChain(tokens):
    return ServiceChain(tokens[0], tokens[1])
    
# "TOKENS"
NEGSIGN = Suppress(Literal("!"))
AND     = Suppress(Literal("&"))
OR      = Suppress(Literal("|"))
LEFTPAREN = Suppress(Literal("("))
RIGHTPAREN = Suppress(Literal(")"))
UNTIL = Suppress(Literal("U"))
DASH = Suppress(Literal("-"))
SWITCHNAME = Word(nums)
LEFT_BRACK = Suppress(Literal("["))
RIGHT_BRACK = Suppress(Literal("]"))
REACH = Suppress(Literal("Reach"))
WAYPOINT = Suppress(Literal("WP"))
SERVICE = Suppress(Literal("SC"))

# Forwards
switchID = Forward()
djunct = Forward()
cjunct = Forward()
until = Forward()
loopfree = Forward()
negation = Forward()
prop = Forward()
reach = Forward()
waypoint = Forward()
service = Forward()

WP_LIST = Group(delimitedList(SWITCHNAME))
WP_LIST_BRACK = LEFT_BRACK + WP_LIST + RIGHT_BRACK

# Booleans
true = Suppress(Literal("true")).addParseAction(MakeTrue)
false = Suppress(Literal("false")).addParseAction(MakeFalse)

# Formula
prop <<= djunct | cjunct | until | loopfree | negation | true | false | reach | waypoint | service | switchID

# Disjunction:
djunct <<= LEFTPAREN + prop + OR + prop + RIGHTPAREN
djunct.addParseAction(MakeDisjunction)

# Conjunction
cjunct <<= LEFTPAREN + prop + AND + prop + RIGHTPAREN
cjunct.addParseAction(MakeConjunction)

# Until
until<<= LEFTPAREN + prop + UNTIL + prop + RIGHTPAREN
until.addParseAction(MakeUntil)

# LoopFree
loopfree = Suppress(Literal("LF")).addParseAction(MakeLoopFree)

# Negation
negation <<= NEGSIGN + LEFTPAREN + prop + RIGHTPAREN
negation.addParseAction(MakeNegation)

# switchID
switchID <<= SWITCHNAME
switchID.addParseAction(MakeSwitchID)

# Reachability
reach <<= REACH + LEFTPAREN + SWITCHNAME + RIGHTPAREN
reach.addParseAction(MakeReachability)

# Waypointing
waypoint <<= WAYPOINT + LEFTPAREN + SWITCHNAME + DASH + SWITCHNAME + RIGHTPAREN
waypoint.addParseAction(MakeWaypoint)

# Service chaining
service <<= SERVICE + LEFTPAREN + WP_LIST_BRACK + DASH + SWITCHNAME + RIGHTPAREN
service.addParseAction(MakeServiceChain)

def parse_property(file_path):
    try:
        with open(file_path, "r") as f:
            p =  f.read()
            return prop.parseString(p, parseAll = True)[0]
    except FileNotFoundError:
        return prop.parseString(file_path, parseAll = True)[0]
