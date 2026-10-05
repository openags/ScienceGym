import unittest,json
from pathlib import Path
from verify_package import validate
class PackageTests(unittest.TestCase):
 def test_complete_static_package(self):self.assertEqual(validate(Path(__file__).resolve().parents[1])['status'],'PASS')
if __name__=='__main__':unittest.main()
