from invoke import run, task

@task
def test():
    run("python tests/TestNgramLM.py")
