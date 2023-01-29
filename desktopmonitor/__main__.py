from dataclasses import asdict
from json import dumps
from typing import Any
from typing import Dict
from typing import List

import click

from desktopmonitor.actions import GetCPUInfo
from desktopmonitor.models import CPU


@click.command()
def command():
    try:
        cpu_info = GetCPUInfo()
        cpu_info()

        cpus: List[Dict[str, Any]] = []

        for core in cpu_info.cores_by_id.values():
            for cpu in core.cpus_by_id.values():
                cpus.append(asdict(cpu))

    except Exception as e:
        click.echo(click.style(f"{e}", fg='red'))
        raise click.Abort()

    json = {
        "cpus": cpus
    }

    click.echo(dumps(json, indent=2))
