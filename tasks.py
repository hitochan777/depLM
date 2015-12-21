from invoke import run, task
from DependencyLM import *

@task
def test():
    run("python tests/TestNgramLM.py")

@task
def clean():
    run("rm *.pyc *_pb2.py")

@task
def proto():
    run("protoc -I=. --python_out=. depLM.proto")

@task
def train(filename, modelFile):
    lm = DependencyLM()
    lm.train(filename, modelFile)
