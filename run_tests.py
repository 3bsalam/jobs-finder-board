#!/usr/bin/env python3
"""Run all unit test suites across the project."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "dashboard"))

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_dirs = [
        os.path.join(ROOT, "scripts", "__tests__"),
        os.path.join(ROOT, "dashboard", "__tests__"),
    ]

    for d in test_dirs:
        if os.path.exists(d):
            suite.addTests(loader.discover(d))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())
