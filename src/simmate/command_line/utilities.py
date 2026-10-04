# -*- coding: utf-8 -*-

import click
from typer.core import TyperGroup


class AlphabeticalGroup(TyperGroup):
    """
    A Typer group that lists its commands and subgroups in alphabetical order
    (rather than the order they were registered in).
    """

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(self.commands)
