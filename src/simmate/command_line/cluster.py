# -*- coding: utf-8 -*-

import click


@click.group()
def cluster():
    """A group of commands for starting up Prefect Agents and Dask Clusters."""
    pass


@cluster.command()
@click.option(
    "--prefect_config",
    "-p",
    help="the name of the Prefect Agent configuration to use",
)
@click.option(
    "--dask_config",
    "-d",
    help="the name of the Dask Cluster configuration to use",
)
def start(cluster_name):
    """
    This starts up a Dask cluster and/or a Prefect Agent that can run Simmate jobs.
    
    This convenience command is really only meant for testing purposes, as Dask
    and Prefect teams offer their own commands with much more control. For 
    example, this command uses Prefect's LocalAgent, but there are other
    advanced types available such as DockerAgent which may be better for your
    use case.
    
    If you would like this cluster to run endlessly in the background, you can
    submit it with something like "nohup simmate cluster start <<extra-options>> &".
    The "nohup" and "&" symbol together make it so this runs in the background AND
    it won't shutdown if you close your terminal (or ssh).
    
    For more help on managing your computational resources, see here:
        <<TODO: insert link>>
    
    """

    # We can now proceed with reseting the database
    click.echo("Checking for configuration file...")

    # Let the user know everything succeeded
    click.echo("Success! Your database has been reset.")
