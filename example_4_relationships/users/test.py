#!/usr/bin/env python3
import unittest
import sys, os


sys.path.append(os.path.dirname(os.path.realpath(__file__)))
tests = unittest.TestLoader().discover('.', pattern='?*test.py')
testRunner = unittest.runner.TextTestRunner()
testRunner.run(tests)
