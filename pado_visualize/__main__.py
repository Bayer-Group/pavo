"""pado-visualize cli interface

useful commands for interacting with pado-visualize

"""
from __future__ import annotations

import argparse
import os
import os.path
import shutil
import subprocess
import sys
import warnings
from pathlib import Path
from typing import List
from typing import NoReturn
from typing import Optional

import typer
from flask import Flask

from pado_visualize.app import create_app
from pado_visualize.config import initialize_config
from pado_visualize import __version__


# --- formatting utils ---

def echo_header(title, width=80):
    """print an ascii header"""
    line = " ".join([
        "#", "---", title, "-" * (width - len(title) - 7)
    ])
    typer.secho(line, color=typer.colors.CYAN)


# === pado-visualize cli interface ============================================

cli = typer.Typer(
    name="pado-visualize",
    epilog="#### visualize pado datasets ####",
)

@cli.command("version")
def version():
    """show the pado-visualize version"""
    typer.echo(__version__)


# --- configuration subcommands -----------------------------------------------

cli_config = typer.Typer()
cli.add_typer(cli_config, name="config")


@cli_config.command()
def searchtree() -> None:
    """print the current app config to console"""
    from dynaconf.utils import files as _files

    # get the configured app
    app = create_app(is_worker=False)
    settings = app.dynaconf

    # note: SEARCHTREE is updated after configure
    tree: List[str] = getattr(_files, 'SEARCHTREE', [])

    echo_header("search tree")
    for location in tree:
        typer.echo(location)
    typer.echo("")

    echo_header("loaded config files")
    for location in tree:
        for file in settings.settings_file:
            f = os.path.join(location, file)
            if os.path.isfile(f):
                typer.echo(f)


@cli_config.command(name="show")
def config_show() -> None:
    """show the current pado-visualize configuration"""
    # get the configured app
    app = create_app(is_worker=False)
    settings = app.dynaconf

    echo_header(f"config using env: '{settings.current_env}'")
    for key, value in settings.as_dict().items():
        typer.echo(f"{key}={value!r}")


# --- development subcommands -------------------------------------------------

cli_dev = typer.Typer()
cli.add_typer(cli_dev, name="development")


@cli_dev.command(name="js")
def dev_js(
    watch: bool = typer.Option(False, help="watch changes in frontend and rebuild"),
    check_is_git: bool = typer.Option(True, help="test if dev is run on git repository"),
) -> NoReturn:
    """build the javascript frontend"""
    if shutil.which("npm") is None:
        typer.echo("npm not found", err=True)
        raise typer.Exit(code=1)

    module_dir = os.path.dirname(__file__)
    repo_dir = os.path.dirname(module_dir)

    if check_is_git:
        # for sanity let's verify that we actually run this in a git repo
        if shutil.which("git") is None:
            typer.echo("git not found", err=True)
            raise typer.Exit(code=1)
        ret = subprocess.call(
            ["git", "-C", module_dir, "rev-parse"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if ret != 0:
            typer.echo("pado-visualize is not in a git repository!", err=True)
            typer.secho("You probably didn't install in development mode and should run again in your dev environment")
            raise typer.Exit(code=1)
        else:
            typer.secho("running in git repo", color=typer.colors.GREEN)

    cmd = ["npm", "run", "deploy" if not watch else "watch"]
    typer.secho(' '.join(cmd), color=typer.colors.YELLOW)
    # fixme: this throws a warning for now due to a multiprocessing cleanup issue...
    os.chdir(repo_dir)
    os.execvp(file="npm", args=cmd)


@cli_dev.command(name="run")
def dev_run(
    dataset: List[Path] = typer.Option([], exists=True, dir_okay=True, file_okay=False),
    debug: bool = typer.Option(True, help="flask debug on/off"),
    host: str = typer.Option("localhost", help="flask hostname/ip"),
    port: int = typer.Option(8000, help="flask port"),
) -> None:
    """run development webserver"""
    overrides = {
        "DEBUG": debug,
        "SERVER": host,
        "PORT": port,
    }
    if dataset:
        overrides["DATASET_PATHS"] = dataset

    # acquire the configuration
    app = Flask("pado_visualize")
    settings = initialize_config(app=app, override_config=overrides, force_env="development").settings

    if not settings.DATASET_PATHS:
        warnings.warn("no DATASET_PATHS specified! (set via cmdline in dev or file in prod)")

    # print some extra info
    typer.secho(" * Loading datasets:", color=typer.colors.GREEN)
    for ds in settings.dataset_paths:
        typer.secho(f"   - '{ds!s}'", color=typer.colors.GREEN)
    typer.secho(f" * Using cache_path: '{settings.cache_path!s}'", color=typer.colors.GREEN)

    # run development app
    app = create_app(configured_app=app)
    app.run(
        host=app.config.SERVER,
        port=app.config.PORT,
        debug=app.config.DEBUG
    )


# --- production subcommands --------------------------------------------------

cli_prod = typer.Typer()
cli.add_typer(cli_prod, name="production")


@cli_prod.command(name="run")
def prod_run(
    sanity_check: bool = typer.Option(True, help="check some settings before launch")
) -> None:
    """run production webserver"""
    app = Flask("pado_visualize")
    settings = initialize_config(app=app, force_env="production").settings

    if sanity_check:
        # acquire the configuration
        if not settings.dataset_paths:
            typer.secho("no dataset_paths defined", err=True, color=typer.colors.RED)
            raise typer.Exit(code=1)
        if settings.current_env.lower() != "production":
            typer.secho(f"not running the production env: {settings.current_env!r}", err=True, color=typer.colors.RED)
            raise typer.Exit(code=1)

    cmd = [
        "uwsgi",
        "--http", f"{settings.SERVER}:{settings.PORT}",
        "--env", f"{settings.ENVVAR_PREFIX}_ENV=production",
        "--manage-script-name",
        "--mount", "/=pado_visualize.app:create_app()",
        "--lazy-apps",
        "--master",
        "--processes", str(settings.UWSGI_NUM_PROCESSES)
    ]

    typer.secho("dispatching to uwsgi:", color=typer.colors.GREEN)
    os.execvp(file="uwsgi", args=cmd)


if __name__ == "__main__":
    cli()
