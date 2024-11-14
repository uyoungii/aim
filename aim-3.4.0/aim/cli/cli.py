import click
from click import core

from aim.cli.configs import *  # noqa F403
from aim.cli.init import commands as init_commands
from aim.cli.version import commands as version_commands
from aim.cli.up import commands as up_commands
from aim.cli.server import commands as server_commands
from aim.cli.upgrade import commands as upgrade_commands
from aim.cli.reindex import commands as reindex_commands
from aim.cli.runs import commands as runs_commands

core._verify_python3_env = lambda: None


@click.group()
@click.option('-v', '--verbose', is_flag=True)
def cli_entry_point(verbose):
    if verbose:
        click.echo('Verbose mode is on')


cli_entry_point.add_command(init_commands.init, INIT_NAME)
cli_entry_point.add_command(version_commands.version, VERSION_NAME)
cli_entry_point.add_command(up_commands.up, UP_NAME)
cli_entry_point.add_command(server_commands.server, SERVER_NAME)
cli_entry_point.add_command(upgrade_commands.upgrade, UPGRADE_NAME)
cli_entry_point.add_command(reindex_commands.reindex, REINDEX_NAME)
cli_entry_point.add_command(runs_commands.runs, RUNS_NAME)
