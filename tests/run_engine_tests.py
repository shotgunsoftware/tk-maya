"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
Test runner for engines and apps. This file should be 
copied to an engine's tests folder.
"""
import sys
import os
from optparse import OptionParser
import unittest2 as unittest

# add Engine root to the python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

class TankEngineTestRunner(object):
    def __init__(self):
        file_path = os.path.abspath(__file__)
        engine_test_dir = os.path.dirname(file_path)
        self.engine_root = os.path.dirname(engine_test_dir)
        self.apps_root = os.path.join(self.engine_root, "apps")
        # get app names
        self.apps = [x for x in os.listdir(self.apps_root) if not x.startswith(".")]
        # add to path
        sys.path.append(self.engine_root)
        self.suite = unittest.TestSuite()


    def run_tests_with_coverage(self, test_name):
        import coverage
        source_paths = ["engine"]
        source_paths.extend(self.get_apps_source_paths())
        cov = coverage.coverage(source=source_paths)
        cov.start()
        self.discover(test_name)
        test_results = unittest.TextTestRunner(verbosity=2).run(self.suite)
        cov.stop()
        cov.report()
        return test_results

    def run_tests(self, test_name):
        # get engine tests
        self.discover(test_name)
        test_results = unittest.TextTestRunner(verbosity=2).run(self.suite)
        return test_results

    def discover(self, test_filter):
        """
        Discovers tests for engine and it's apps.

       :param test_filter: Specifiction of engine only, app only, specific module, class or test.
                         The format is <engine/app_name>.<module>.<test case>.<test>
                         For modules that live in sub-packages to the test directory:
                         <engine/app_name>.<package>.<module>.<test case>.<test>
        """
        if test_filter:
            app_name, test_name = self.parse_filter(test_filter)
            if app_name == os.path.basename(self.engine_root):
                # run only engine tests
                engine_test_dir = os.path.join(self.engine_root, "tests")
                self.setup_suite(engine_test_dir, test_name)
            elif app_name in self.apps:
                app_test_dir = os.path.join(self.apps_root, app_name, "tests")
                self.setup_suite(app_test_dir, test_name)
            else:
                print "Test filter not understood: %s" % test_filter
        else:
            engine_test_dir = os.path.join(self.engine_root, "tests")
            self.setup_suite(engine_test_dir)
            for app_name in self.apps:
                app_test_dir = os.path.join(self.apps_root, app_name, "tests")
                self.setup_suite(app_test_dir)

    def setup_suite(self, test_dir, test_name=None):
        """
        Discover and add tests to the test suite.

        :param test_dir: Directory in which to find tests.
        :param test_name: (Optional) If specified, used to find specific module.TestCase.test
        """
        if not os.path.exists(test_dir):
            print "Test directory does not exist: %s" % test_dir
            return

        if test_name:
            # find filtered test
            cur_dir = os.getcwd()
            os.chdir(test_dir)
            suite = unittest.loader.TestLoader().loadTestsFromName(test_name)
            os.chdir(cur_dir)
        else:
            suite = unittest.loader.TestLoader().discover(test_dir)
        self.suite.addTests(suite)

    def parse_filter(self, test_filter):
        app_name = test_name = None
        if test_filter:
            if '.' in test_filter:
                app_name, test_name = test_filter.split('.', 1)
            else:
                app_name = test_filter
        return app_name, test_name

    def get_apps_source_paths(self):
        """Construct paths to app file and app modules for coverage."""
        source_paths = []
        for app_name in self.apps:
            app_dir = os.path.join(self.apps_root, app_name)
            app_path = os.path.join(app_dir, "app.py")
            source_paths.append(app_path)
            module_dir = os.path.join(app_dir, "python", app_name)
            if os.path.exists(module_dir):
                source_paths.append(module_dir)
        return source_paths
    
def main():
    parser = OptionParser()
    parser.add_option("--with-coverage",
                      action="store_true",
                      dest="coverage", 
                      help="run with coverage (requires coverage is installed)")

    # Add help for unit2 style test specification
    parser.usage = "usage: %prog [options] test\n"
    parser.usage += "Examples:\n"
    parser.usage += " run_tests.py                                      - run tests for an engine and it's apps\n"
    parser.usage += " run_tests.py my_engine_name                       - run tests for the engine only\n"
    parser.usage += " run_tests.py my_app                               - run tests for specified app only\n"
    parser.usage += " run_tests.py my_engine.test_module                - run specific test module\n"
    parser.usage += " run_tests.py my_engine.test_module.TestClass.test - run specific test only"

    (options, args) = parser.parse_args()
    test_name = None
    if args:
        test_name = args[0]
     
    tank_test_runner = TankEngineTestRunner()

    if options.coverage:
        test_results = tank_test_runner.run_tests_with_coverage(test_name)
    else:
        test_results = tank_test_runner.run_tests(test_name)

    if test_results.errors or test_results.failures:
        exit_code = 1
    else:
        exit_code = 0

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
