#!/usr/bin/env python
# otsuki@nlp (Otsuki Hitoshi)

class DependencyTreeNode:
    def __init__(self, data = None):
        self.data = data
        self.parent = None
        self.children = []

    def addChild(self, child):
        self.children.append(child)
