"""Mypy static tests for all python scripts in controller folder.
They make sure there are no type clashes or other unexpected
    situations (undefined variables, etc.).
Requirements:
- mypy library installed with python3
"""

import os
import sys
import unittest
import subprocess


class MypyTest(unittest.TestCase):
    def setUp(self):
        # To rightly run these tests, there is a need for python3.7 or higher
        python_version = float(sys.version[:3])

        if python_version < 3.7:
            reason = "Required python version for these tests is 3.7 or above. Skipping"
            self.skipTest(reason)

    def test_all_project_files(self):
        """Scanning the whole controller dir for mypy issues"""
        file_dir = os.path.dirname(os.path.realpath(__file__))
        main_code_dir = os.path.join(file_dir, "../controller")
        command_list = ["python3", "-m", "mypy", main_code_dir]
        mypy_validation = subprocess.run(
            command_list, capture_output=True, text=True)
        if "no issues found" not in mypy_validation.stdout:
            print(f"MYPY ERRORS:\n{mypy_validation.stdout}")
        self.assertTrue("no issues found" in mypy_validation.stdout)


def suite_statuses():
    tests = [
        "test_all_project_files",
    ]
    return unittest.TestSuite(map(MypyTest, tests))


def suite_my_module():
    suite = unittest.TestSuite()

    suite.addTest(suite_statuses())
    return suite


def main():
    unittest.TextTestRunner(verbosity=2).run(suite_my_module())


if __name__ == "__main__":
    main()
