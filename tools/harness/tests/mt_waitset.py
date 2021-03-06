##########################################################################
# Copyright (c) 2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Haldeneggsteig 4, CH-8092 Zurich. Attn: Systems Group.
##########################################################################

import re
import tests
from common import TestCommon
from results import PassFailResult
import debug

@tests.add_test
class MultithreadedWaitsetTest(TestCommon):
    '''multithreaded waitset functionality'''
    name = "mt_waitset"

    def setup(self, build, machine, testdir):
        super(MultithreadedWaitsetTest, self).setup(build, machine, testdir)
        self.test_timeout_delta *= 2
        debug.verbose("%s: increasing test timeout delta by factor 2: new = %s" %
                (self.name, self.test_timeout_delta))

    def get_modules(self, build, machine):
        modules = super(MultithreadedWaitsetTest, self).get_modules(build, machine)
        modules.add_module("mt_waitset", ["10", "10", "100000", "8"])
        return modules

    def is_finished(self, line):
        return "Test PASSED" in line or "Test FAILED" in line

    def process_data(self, testdir, rawiter):
        passed = False
        for line in rawiter:
            if "Test PASSED" in line:
                passed = True
        return PassFailResult(passed)
