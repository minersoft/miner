import re
from miner_globals import getScriptParameter

class RepositoryPath:
    REPOSITORY_DEF_RE = re.compile(r"^([-\w]*):(\<([-\w]+)\>)?(.*)$")
    def __init__(self):
        self.defaultPath = ""
        self.perTargetDict = {}
        for element in getScriptParameter("REPOSITORY_PATH", "").split(";"):
            match = RepositoryPath.REPOSITORY_DEF_RE.search(element)
            if match:
                root = match.group(1)
                if not root:
                    self.defaultPath = os.path.expanduser(match.group(4))
                else:
                    target = match.group(3)
                    if not target:
                        target = root
                    #print "target", target, "value", value
                    self.perTargetDict[root] = (target, os.path.expanduser(match.group(4)))
    def getSourceType(self, path):
        rest = ""
        if "/" in path:
            root,rest = path.split("/", 1)
        else:
            root = path
        entry = self.perTargetDict.get(root)
        if not entry:
            return root
        else:
            return entry[0]

    def expand(self, path):
        rest = ""
        if "/" in path:
            root,rest = path.split("/", 1)
        else:
            root = path
        entry = self.perTargetDict.get(root)
        if not entry:
            return os.path.join(self.defaultPath, path)
        else:
            return os.path.join(entry[1], rest)

    def getTargetList(self):
        targets = set(self.perTargetDict.iterkeys())
        if self.defaultPath:
            targets |= set(os.listdir(self.defaultPath)) 
        return sorted(targets)
