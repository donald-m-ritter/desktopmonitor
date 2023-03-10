import os
from unittest import TestCase

from expects import equal
from expects import expect
from expects import have_len
from expects import raise_error
from invoke import Result

from desktopmonitor.actions import GetCPUInfo


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TEST_DIR, '../fixtures')


class Fixtures:
    CPUINFO_SUCCESS = os.path.join(FIXTURES_DIR, 'cpuinfo.stdout')
    CPUPOWER_SUCCESS = os.path.join(FIXTURES_DIR, 'cpupower.stdout')
    SENSORS_SUCCESS = os.path.join(FIXTURES_DIR, 'sensors.stdout')
    MPSTAT_SUCCESS = os.path.join(FIXTURES_DIR, 'mpstat.stdout')


class SuccessfulGetCPUInfo(GetCPUInfo):
    def execute_cpuinfo(self):
        with open(Fixtures.CPUINFO_SUCCESS, 'r') as f:
            self.cpuinfo_result = Result(stdout=f.read(), stderr='', exited=0)

    def execute_cpupower(self):
        with open(Fixtures.CPUPOWER_SUCCESS, 'r') as f:
            self.cpupower_result = Result(stdout=f.read(), stderr='', exited=0)

    def execute_sensors(self):
        with open(Fixtures.SENSORS_SUCCESS, 'r') as f:
            self.sensors_result = Result(stdout=f.read(), stderr='', exited=0)

    def execute_mpstat(self):
        with open(Fixtures.MPSTAT_SUCCESS, 'r') as f:
            self.mpstat_result = Result(stdout=f.read(), stderr='', exited=0)


class GetCoreInfoTest(TestCase):
    action: GetCPUInfo

    def test_cores_parsed_successfully(self):
        self.action = SuccessfulGetCPUInfo()

        def callback():
            self.action()

        expect(callback).to_not(raise_error)
        expect(self.action.cores_by_id).to(have_len(8))

        expect(self.action.cores_by_id["0"].cpus_by_id["0"].id).to(equal("0"))
        expect(self.action.cores_by_id["0"].cpus_by_id["0"].physical_id).to(equal("0"))
        expect(self.action.cores_by_id["0"].cpus_by_id["0"].core_id).to(equal("0"))
        expect(self.action.cores_by_id["0"].cpus_by_id["0"].model_name).to(equal("AMD Ryzen 7 5700G with Radeon Graphics"))  # noqa: E501
        expect(self.action.cores_by_id["0"].cpus_by_id["0"].minimum_frequency).to(equal(1433.6))
        expect(self.action.cores_by_id["0"].cpus_by_id["0"].maximum_frequency).to(equal(4782.08))
        expect(self.action.cores_by_id["0"].cpus_by_id["0"].current_frequency).to(equal(2853.877))
        expect(self.action.cores_by_id["0"].cpus_by_id["0"].temperature).to(equal(29.8))
        expect(self.action.cores_by_id["0"].cpus_by_id["0"].utilization).to(equal(1.13))
