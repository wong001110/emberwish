"""Reject an empty test suite instead of treating it as green."""
from pathlib import Path
import unittest
import sys
ROOT=Path(__file__).resolve().parents[1]
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_continuity.py')
if suite.countTestCases()==0:raise SystemExit('No continuity tests were discovered')
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
