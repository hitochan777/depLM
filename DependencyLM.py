import sys

import DependencyParserHelper as dph
from NgramLM import NgramLM
# import depLM_pb2

# TODO: Add support for arbitrary n-gram LM. This class currently support only trigram
class DependencyLM(object):

    def __init__(self, countkey = lambda tree: tree.data["pos"], smoothing="ml"):
        self.probHead = NgramLM(1)
        self.probLeft = NgramLM(3)
        self.probRight = NgramLM(3)
        self.countkey = countkey
        self.smoothing = smoothing

    def train(self, filename, modelFile, progress=10000):
        """
        filename: Filename of CONLL format
        progress: print dot(.) every #progress trees; default: 10000
        """
        cnt = 0
        print "Model training started"
        for depString in dph.readDependencyFile(filename):
            cnt += 1
            if cnt % progress == 0:
                sys.stdout.write(".")
            tree = dph.stringToDependencyTreeWeakRef(depString)
            if tree is None:
                continue
            self.countFreq(tree)
        if self.smoothing == "ml":
            # Apppy maximum likelihood estimation to get probability from counts
            self.probHead.mlEstimate()
            self.probLeft.mlEstimate()
            self.probRight.mlEstimate()
        else:
            raise NotImplemented("Currently only maximum likelihood is supported as a smoothing method (though ML is not smoothing technique)")

        if cnt >= progress:
            print # Without this, when there are less than #progress trees, there will be an empty line, which is ugly in my opinion...
        print "Model training has successfully finished!"
        print "Writing model infomation to %s" % (modelFile, )
        self.saveModelAsPlainText(modelFile)
        print "Finished writing model information to %s" % (modelFile, )

    def saveModelAsPlainText(self, filename):
        with open(filename, "w") as model:
           model.write("[probHead]\n")
           self.probHead.saveNgramInfo(fstream=model)
           model.write("[probLeft]\n")
           self.probLeft.saveNgramInfo(fstream=model)
           model.write("[probRight]\n")
           self.probRight.saveNgramInfo(fstream=model)

    def readModelFromPlainText(self, file):
        isString = False
        if isinstance(file, basestring):
            model = open(file, "r")
            isString = True
        else:
            model = file
        
        for line in model:
            line = line.strip()
            if line in ["[probHead]", "[probLeft]", "[probRight]"]:
                state = line
                continue

            if line == "":
                continue

            ngram, count, logProb = line.split("\t")
            ngram = ngram.split(" ")
            count = int(count)
            if state == "[probHead]":
                self.probHead.addNgramCount(ngram, count)

            elif state == "[probLeft]":
                self.probLeft.addNgramCount(ngram, count)
            
            elif state == "[probRight]":
                self.probRight.addNgramCount(ngram, count)

        if self.smoothing == "ml":
            # Apppy maximum likelihood estimation to get probability from counts
            self.probHead.mlEstimate()
            self.probLeft.mlEstimate()
            self.probRight.mlEstimate()

        else:
            raise NotImplemented("Currently only maximum likelihood is supported as a smoothing method (though ML is not smoothing technique)")

        if isString: # If filestream is opened in this function, close fstream
            model.close()


    def saveModelAsProtocolBuffer(self, filename):
        with open(filename, "wb") as model:
            lmpb = depLM_pb2.depLM()
            self.probHead.writeMessage(lmpb.probHead.ngramEntries)
            self.probLeft.writeMessage(lmpb.probLeft.ngramEntries)
            self.probRight.writeMessage(lmpb.probRight.ngramEntries)
            model.write(lmpb.SerializeToString())
             
    def readModelFromProtocolBuffer(self, file):
        isString = False
        if isinstance(file, basestring):
            model = open(file, "rb")
            isString = True
        else:
            model = file
        
        lmpb = depLM_pb2.depLM()
        lmpb.ParseFromString(model.read())
        for ngramEntry in lmpb.probHead.ngramEntries:
            self.probHead.addNgramProb(ngramEntry.ngram, ngramEntry.prob)
            self.probHead.addNgramCount(ngramEntry.ngram, ngramEntry.count)
        for ngramEntry in lmpb.probLeft.ngramEntries:
            self.probLeft.addNgramProb(ngramEntry.ngram, ngramEntry.prob)
            self.probLeft.addNgramCount(ngramEntry.ngram, ngramEntry.count)
        for ngramEntry in lmpb.probRight.ngramEntries:
            self.probRight.addNgramProb(ngramEntry.ngram, ngramEntry.prob)
            self.probRight.addNgramCount(ngramEntry.ngram, ngramEntry.count)
        if isString: # If filestream is opened in this function, close fstream
            model.close()

    def countFreq(self, node):
        if node.parent is None:
            self.probHead.addNgramCount([self.countkey(node)])
        left, right = node.partitionChildren()

        if len(left) > 0:
            self.probLeft.addNgramCount(["___none", self.countkey(left[0].parent)+"___head", self.countkey(left[0])])
        for index in xrange(1, len(left)):
            self.probLeft.addNgramCount([self.countkey(left[index-1]), self.countkey(left[index].parent)+"___head", self.countkey(left[index])])

        if len(right) > 0:
            self.probRight.addNgramCount(["___none", self.countkey(right[0].parent)+"___head", self.countkey(right[0])])

        for index in xrange(1, len(right)):
            self.probRight.addNgramCount([self.countkey(right[index-1]), self.countkey(right[index].parent)+"___head", self.countkey(right[index])])

        for child in node.children:
            self.countFreq(child)
