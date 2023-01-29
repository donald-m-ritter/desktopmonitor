import click

from io import StringIO
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

from invoke import Result
from invoke import run


from desktopmonitor.models import Core
from desktopmonitor.models import CPU


class GetCPUInfo(Callable):
    """
    Determines the information per CPU within one or more Cores.
    """

    class Constants:
        ANALYZING_CPU = "analyzing CPU"
        CORE_ID = "core id"
        CPU_TEMPERATURE = "CPU Temperature"
        CPUINFO = "cat /proc/cpuinfo"
        CPUINFO_DELIMINATOR = ":"
        CPUPOWER = "cpupower frequency-info"
        CPUPOWER_DELIMINATOR = ":"
        CPUMHZ = "cpu MHz"
        DEGREES_CELCIUS = "°C"
        HARDWARE_LIMITS = "hardware limits"
        HARDWARE_LIMITS_DELIMINATOR = "-"
        GHZ = "GHz"
        MHZ = "MHz"
        MODEL_NAME = "model name"
        MPSTAT = "mpstat -P ALL"
        MPSTAT_DELIMINATOR = " "
        PHYSICAL_ID = "physical id"
        PROCESSOR = "processor"
        SENSORS = "sensors"
        SENSORS_DELIMINATOR = ":"
        TCTL = "Tctl"

    cores_by_id: Optional[Dict[str, Core]] = None
    cpuinfo_result: Optional[Result] = None
    cpuinfo_processor_chunks: Optional[List[Dict[str, str]]] = None
    cpupower_result: Optional[Result] = None
    cpupower_processor_chunks: Optional[List[Dict[str, str]]] = None
    sensors_result: Optional[Result] = None
    mpstat_result: Optional[Result] = None

    def __call__(self, *args, **kwargs):
        self.cores_by_id = {}
        self.execute_cpuinfo()
        self.process_cpuinfo()
        self.execute_cpupower()
        self.process_cpupower()
        self.execute_sensors()
        self.process_sensors()
        self.execute_mpstat()
        self.process_mpstat()

    def execute_cpuinfo(self):
        try:
            self.cpuinfo_result = run(
                command=GetCPUInfo.Constants.CPUINFO,
                echo_stdin=False,
                in_stream=False,
                out_stream=StringIO(),
                err_stream=StringIO(),
                warn=True
            )
        except Exception:
            pass

    def process_cpuinfo(self):
        """
        Parses the result of cat /proc/cpuinfo to create Core models with each CPU within a Core.
        """
        self.abort_if_cpuinfo_failed()
        self.break_cpuinfo_into_processor_chunks()
        self.parse_cpuinfo_processor_chunks_into_cores()
        self.parse_cpuinfo_processor_chunks_into_cpus()

    def abort_if_cpuinfo_failed(self):
        """
        Aborts the CLI if getting cpuinfo failed.
        """
        if not self.cpuinfo_result or self.cpuinfo_result.return_code != 0:
            message = f'{GetCPUInfo.Constants.CPUINFO} did not run successfully: {self.cpuinfo_result.stderr}'
            click.echo(click.style(message, fg='red'))
            raise click.Abort()

    def break_cpuinfo_into_processor_chunks(self):
        """
        Iterates over the output from cat /proc/cpuinfo to create chunks of lines for each cpu block found.
        """
        self.cpuinfo_processor_chunks = []

        lines = self.cpuinfo_result.stdout.splitlines()
        processor_chunk: Optional[Dict[str, str]] = None

        for line in lines:
            if GetCPUInfo.Constants.CPUINFO_DELIMINATOR in line:
                split = line.split(GetCPUInfo.Constants.CPUINFO_DELIMINATOR, 1)

                if len(split) == 2:
                    key = split[0].strip()
                    value = split[1].strip()

                    if key == GetCPUInfo.Constants.PROCESSOR:
                        processor_chunk = {}
                        self.cpuinfo_processor_chunks.append(processor_chunk)

                    processor_chunk[key] = value

    def parse_cpuinfo_processor_chunks_into_cores(self):
        """
        Iterates over all the processor chunks to create the cores
        """
        for processor_chunk in self.cpuinfo_processor_chunks:
            core_id = processor_chunk.get(GetCPUInfo.Constants.CORE_ID, None)

            if core_id is not None and core_id not in self.cores_by_id:
                self.cores_by_id[core_id] = Core(id=core_id, cpus_by_id={})

    def parse_cpuinfo_processor_chunks_into_cpus(self):
        """
        Iterates over all the processor chunks to create the cpus and put them into their correct core.
        """
        for processor_chunk in self.cpuinfo_processor_chunks:
            core_id = processor_chunk.get(GetCPUInfo.Constants.CORE_ID, None)
            processor = processor_chunk.get(GetCPUInfo.Constants.PROCESSOR, None)
            physical_id = processor_chunk.get(GetCPUInfo.Constants.PHYSICAL_ID, None)
            current_frequency = processor_chunk.get(GetCPUInfo.Constants.CPUMHZ, None)
            model_name = processor_chunk.get(GetCPUInfo.Constants.MODEL_NAME, None)

            if core_id is None or processor is None or current_frequency is None or physical_id is None or model_name is None:  # noqa: E501
                continue

            core = self.cores_by_id[core_id]
            core.cpus_by_id[processor] = CPU(
                id=processor,
                physical_id=physical_id,
                core_id=core_id,
                model_name=model_name,
                minimum_frequency=0.0,
                maximum_frequency=0.0,
                current_frequency=float(current_frequency),
                temperature=0.0,
                utilization=0.0
            )

    def execute_cpupower(self):
        self.cpupower_result = run(
            command=GetCPUInfo.Constants.CPUPOWER,
            echo_stdin=False,
            in_stream=False,
            out_stream=StringIO(),
            err_stream=StringIO(),
            warn=True
        )

    def process_cpupower(self):
        """
        Parses the result of cat /proc/cpuinfo to create Core models with each CPU within a Core.
        """
        self.abort_if_cpupower_failed()
        self.break_cpupower_into_processor_chunks()
        self.parse_frequency_ranges_from_cpupower_chunks()

    def abort_if_cpupower_failed(self):
        """
        Aborts the CLI if getting cpupower failed.
        """
        if not self.cpupower_result or self.cpupower_result.return_code != 0:
            message = f'{GetCPUInfo.Constants.CPUPOWER} did not run successfully: {self.cpupower_result.stderr}'
            click.echo(click.style(message, fg='red'))
            raise click.Abort()

    def break_cpupower_into_processor_chunks(self):
        """
        Iterates over the output from cpupower frequency-info to create chunks of lines for each cpu block found.
        """
        self.cpupower_processor_chunks = []

        lines = self.cpupower_result.stdout.splitlines()
        processor_chunk: Optional[Dict[str, str]] = None

        for line in lines:
            split = line.split(GetCPUInfo.Constants.CPUINFO_DELIMINATOR, 1)

            if len(split) == 2:
                key = split[0].strip()
                value = split[1].strip()

                if key.startswith(GetCPUInfo.Constants.ANALYZING_CPU):
                    processor_chunk = {}
                    self.cpupower_processor_chunks.append(processor_chunk)

                processor_chunk[key] = value

    def parse_frequency_ranges_from_cpupower_chunks(self):
        """
        Iterates over all the processor chunks to create the cores
        """
        for processor_chunk in self.cpupower_processor_chunks:
            analyzing_key: str = list(filter(lambda k: k.startswith(GetCPUInfo.Constants.ANALYZING_CPU), processor_chunk.keys()))[0]  # noqa: E501
            physical_id = analyzing_key.replace(GetCPUInfo.Constants.ANALYZING_CPU, "").replace(GetCPUInfo.Constants.CPUPOWER_DELIMINATOR, "").strip()  # noqa: E501
            hardware_limits = processor_chunk.get(GetCPUInfo.Constants.HARDWARE_LIMITS, None)

            if physical_id is not None and hardware_limits is not None:
                split_hardware_limits = hardware_limits.split(GetCPUInfo.Constants.HARDWARE_LIMITS_DELIMINATOR, 1)
                minimum_frequency = self.convert_frequency_str_to_mhz(split_hardware_limits[0].strip())
                maximum_frequency = self.convert_frequency_str_to_mhz(split_hardware_limits[1].strip())

                for core in self.cores_by_id.values():
                    for cpu in core.cpus_by_id.values():
                        if cpu.physical_id == physical_id:
                            cpu.minimum_frequency = minimum_frequency
                            cpu.maximum_frequency = maximum_frequency

    def convert_frequency_str_to_mhz(self, raw_frequency: str) -> float:
        if GetCPUInfo.Constants.MHZ in raw_frequency:
            return float(raw_frequency.replace(GetCPUInfo.Constants.MHZ, "").strip())
        elif GetCPUInfo.Constants.GHZ in raw_frequency:
            return float(raw_frequency.replace(GetCPUInfo.Constants.GHZ, "").strip()) * 1024.0
        else:
            return 0.0

    def execute_sensors(self):
        self.sensors_result = run(
            command=GetCPUInfo.Constants.SENSORS,
            echo_stdin=False,
            in_stream=False,
            out_stream=StringIO(),
            err_stream=StringIO(),
            warn=True
        )

    def process_sensors(self):
        """
        Parses the result of sensors to determine the CPU temperature
        """
        self.abort_if_sensors_failed()
        lines = self.sensors_result.stdout.splitlines()

        tctl_temp: Optional[float] = None
        cpu_temp: Optional[float] = None

        for line in lines:
            split = line.split(GetCPUInfo.Constants.SENSORS_DELIMINATOR, 1)

            if len(split) == 2:
                key = split[0].strip()
                value = split[1].strip()

                if key == GetCPUInfo.Constants.TCTL:
                    tctl_temp = self.convert_temp_str_to_celcius(value)
                elif key == GetCPUInfo.Constants.CPU_TEMPERATURE:
                    cpu_temp = self.convert_temp_str_to_celcius(value)

        temp = tctl_temp if tctl_temp is not None else cpu_temp

        for core in self.cores_by_id.values():
            for cpu in core.cpus_by_id.values():
                cpu.temperature = temp

    def convert_temp_str_to_celcius(self, raw_temp: str) -> float:
        if GetCPUInfo.Constants.DEGREES_CELCIUS in raw_temp:
            cleaned_temp = raw_temp.replace(GetCPUInfo.Constants.DEGREES_CELCIUS, "").replace("+", "").strip()
            return float(cleaned_temp.strip())
        else:
            return 0.0

    def abort_if_sensors_failed(self):
        """
        Aborts the CLI if getting sensors failed.
        """
        if not self.sensors_result or self.sensors_result.return_code != 0:
            message = f'{GetCPUInfo.Constants.SENSORS} did not run successfully: {self.sensors_result.stderr}'
            click.echo(click.style(message, fg='red'))
            raise click.Abort()

    def execute_mpstat(self):
        self.mpstat_result = run(
            command=GetCPUInfo.Constants.MPSTAT,
            echo_stdin=False,
            in_stream=False,
            out_stream=StringIO(),
            err_stream=StringIO(),
            warn=True
        )

    def process_mpstat(self):
        """
        Parses the result of mpstat to determine the CPU utilization
        """
        self.abort_if_mpstat_failed()
        lines = self.mpstat_result.stdout.splitlines()

        for line in lines:
            self.process_mpstat_line(line.split())

    def process_mpstat_line(self, components: List[str]):
        if len(components) != 13:
            return

        cpu_id = components[2]

        if cpu_id == "all":
            return

        for core in self.cores_by_id.values():
            cpu = core.cpus_by_id.get(cpu_id, None)

            if cpu is not None:
                try:
                    cpu.utilization = round((100.0 - float(components[-1])) * 100.0) / 100.0
                except:
                    # If the cpu id or idle can't be parsed it doesn't really matter
                    pass

    def abort_if_mpstat_failed(self):
        """
        Aborts the CLI if getting mpstat failed.
        """
        if not self.mpstat_result or self.mpstat_result.return_code != 0:
            message = f'{GetCPUInfo.Constants.MPSTAT} did not run successfully: {self.mpstat_result.stderr}'
            click.echo(click.style(message, fg='red'))
            raise click.Abort()