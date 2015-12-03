import sys

from DependencyTreeNode import DependencyTreeNode
import DependencyParserHelper as dph
from NgramLM import NgramLM

# TODO: Add support for arbitrary n-gram LM. This class currently support only trigram
class DependencyLM(object):

    def __init__(self, countkey = lambda tree: tree.data["pos2"], smoothing="ml"):
        self.probHead = NgramLM(1)
        self.probLeft = NgramLM(3)
        self.probRight = NgramLM(3)
        self.countkey = countkey
        self.smoothing = smoothing

    def train(self, filename, modelFile, progress=100):
        """
        filename: Filename of EBMT format
        progress: print dot(.) every #progress trees; default: 100
        """
        cnt = 0
        print "Model training started"
        for depString in dph(filename):
            cnt += 1
            if cnt % progress == 0:
                sys.stdout.write(".")
            tree = dph.stringToDependencyTreeWeakRef(depString)
            self.countFrequency(tree)
        if self.smoothing == "ml":
            # Apppy maximum likelihood estimation to get probability from counts
            self.probHead.mlEstimate()
            self.probLeft.mlEstimate()
            self.probRight.mlEstimate()
        else:
            raise NotImplemented("Currently only maximum likelihood is supported as a smoothing method (though ML is not smoothing technique)"
        if cnt >= progress:
            print # Without this, when there are less than #progress trees, there will be an empty line, which is ugly in my opinion...
        print "Model training has successfully finished!"
        print "Writing model infomation to %s" % (modelFile, )
        with open(modelFile, "w") as model:
            self.probHead.saveNgramInfo(fstream=model)
            self.probLeft.saveNgramInfo(fstream=model)
            self.probRight.saveNgramInfo(fstream=model)
        print "Finished writing model information to %s" % (modelFile, )

    def countFreq(self, node):
        if node.parent is None:
            self.probHead.addNgramCount(countkey(node))
        left, right = self._partition(node.children, node.data["id"])

        if len(left) > 0:
            self.probLeft.addNgramCount([countkey(node.parent)+"___head", "___none", countkey(left[0])])
        for index in xrange(1, len(left)):
            self.probLeft.addNgramCount([countkey(node.parent)+"___head", countkey(left[i-1]), countkey(left[i])])

        if len(right) > 0:
            self.probRight.addNgramCount([countkey(node.parent)+"___head", "___none", countkey(right[0])])
        for index in xrange(1, len(right)):
            self.probRight.addNgramCount([countkey(node.parent)+"___head", countkey(right[i-1]), countkey(right[i])])

    def _partition(self, list, pivot):
        left = [] # items smaller than pivot
        right = [] # items bigger than pivot
        for item in list:
            if item < pivot:
                left.append(item)
            elif item > pivot:
                right.append(item)
            else:
                raise ValueError("item and pivot cannot have the same value because they are node ID")
        sorted(left, key=lambda x: x.data["id"], reverse=True)
        # By default reverse is False, but this is just for emphasizing right is not reversed as opposed to left
        sorted(right, key=lambda x: x.data["id"], reverse=False) 
        return left, right
