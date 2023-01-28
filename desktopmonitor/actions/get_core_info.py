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
        CORE_ID = "core id"
        CPUINFO = "cat /proc/cpuinfo"
        CPUINFO_DELIMINATOR = ":"
        CPUMHZ = "cpu MHz"
        PROCESSOR = "processor"

    cores_by_id: Optional[Dict[str, Core]] = None
    cpuinfo_result: Optional[Result] = None
    cpuinfo_processor_chunks: Optional[List[Dict[str, str]]] = None

    def __call__(self, *args, **kwargs):
        self.determine_cores()

    def determine_cores(self):
        """
        Uses cat /proc/cpuinfo to determine the layout of cores and cpus
        """
        self.cores_by_id = {}
        self.execute_cpuinfo()
        self.process_cpuinfo()

    def execute_cpuinfo(self):
        self.cpuinfo_result = run(
            command=GetCPUInfo.Constants.CPUINFO,
            echo_stdin=False,
            err_stream=None,
            in_stream=StringIO(),
            out_steam=StringIO(),
            warn=True
        )

    def process_cpuinfo(self):
        """
        Parses the result of cat /proc/cpuinfo to create Core models with each CPU within a Core.
        """
        self.abort_if_cpuinfo_failed()
        self.break_cpuinfo_into_processor_chunks()
        self.parse_processor_chunks_into_cores()
        self.parse_processor_chunks_into_cpus()

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

    def parse_processor_chunks_into_cores(self):
        """
        Iterates over all the processor chunks to create the cores
        """
        for processor_chunk in self.cpuinfo_processor_chunks:
            core_id = processor_chunk.get(GetCPUInfo.Constants.CORE_ID, None)

            if core_id is not None and core_id not in self.cores_by_id:
                self.cores_by_id[core_id] = Core(id=core_id, temperature=0.0, cpus_by_id={})

    def parse_processor_chunks_into_cpus(self):
        """
        Iterates over all the processor chunks to create the cpus and put them into their correct core.
        """
        for processor_chunk in self.cpuinfo_processor_chunks:
            core_id = processor_chunk.get(GetCPUInfo.Constants.CORE_ID, None)
            processor = processor_chunk.get(GetCPUInfo.Constants.PROCESSOR, None)
            current_frequency = processor_chunk.get(GetCPUInfo.Constants.CPUMHZ, None)

            if core_id is None or processor is None or current_frequency is None:
                continue

            core = self.cores_by_id[core_id]
            core.cpus_by_id[processor] = CPU(
                id=processor,
                minimum_frequency=0.0,
                maximum_frequency=0.0,
                current_frequency=float(current_frequency),
                utilization=0.0
            )
