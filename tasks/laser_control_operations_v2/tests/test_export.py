import unittest
from verify_export import allowed_name, EXPECTED_FILES
from verify_package import verify
class ExportTests(unittest.TestCase):
    def test_names_are_original_text_and_code(self):
        self.assertEqual(len(EXPECTED_FILES),len(set(EXPECTED_FILES)))
        self.assertTrue(all(n.endswith(('.json','.md','.py')) for n in EXPECTED_FILES))
    def test_unsafe_names_rejected(self):
        for n in ('../evil','/absolute','a/../b','a//b','a/./b','a\\b','.hidden/x','x/.git','C:/x','',None,1):self.assertFalse(allowed_name(n),str(n))
    def test_allowed_names(self):self.assertTrue(all(allowed_name(n) for n in EXPECTED_FILES))
    def test_package_structure(self):self.assertEqual(verify()['errors'],[])
if __name__=='__main__':unittest.main()
