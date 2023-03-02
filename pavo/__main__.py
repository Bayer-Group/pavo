"""pavo cli interface

useful commands for interacting with pavo

"""
from __future__ import annotations

import os
import os.path
import shutil
import subprocess
import warnings
from pathlib import Path
from typing import List
from typing import NoReturn

import typer
from flask import Flask

from pavo import __version__
from pavo.app import create_app
from pavo.config import initialize_config

# --- formatting utils ---


def echo_header(title: str, width: int = 80) -> None:
    """print an ascii header"""
    line = " ".join(["#", "---", title, "-" * (width - len(title) - 7)])
    typer.secho(line, fg=typer.colors.CYAN)


# === pavo cli interface ============================================

cli = typer.Typer(
    name="pavo",
    epilog="#### visualize pado datasets ####",
    no_args_is_help=True,
)


@cli.command("version")
def version() -> None:
    """show the pavo version"""
    typer.echo(__version__)


# --- configuration subcommands -----------------------------------------------

cli_config = typer.Typer(
    help="configuration subcommands",
    no_args_is_help=True,
)
cli.add_typer(cli_config, name="config")


@cli_config.command()
def searchtree() -> None:
    """print the current app config to console"""
    from dynaconf.utils import files as _files

    # get the configured app
    app = create_app(is_worker=False, config_only=True)
    settings = app.dynaconf  # type: ignore

    # note: SEARCHTREE is updated after configure
    tree: List[str] = getattr(_files, "SEARCHTREE", [])

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
    """show the current pavo configuration"""
    # get the configured app
    app = create_app(is_worker=False, config_only=True)
    settings = app.dynaconf  # type: ignore

    echo_header(f"config using env: '{settings.current_env}'")
    for key, value in settings.as_dict().items():
        typer.echo(f"{key}={value!r}")


# --- development subcommands -------------------------------------------------

cli_dev = typer.Typer(
    help="development subcommands",
    no_args_is_help=True,
)
cli.add_typer(cli_dev, name="development")


@cli_dev.command(name="js")
def dev_js(
    watch: bool = typer.Option(False, help="watch changes in frontend and rebuild"),
    check_is_git: bool = typer.Option(
        True, help="test if dev is run on git repository"
    ),
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
            typer.echo("pavo is not in a git repository!", err=True)
            typer.secho(
                "You probably didn't install in development mode and should run again in your dev environment"
            )
            raise typer.Exit(code=1)
        else:
            typer.secho("running in git repo", fg=typer.colors.GREEN)

    cmd = ["npm", "run", "deploy" if not watch else "watch"]
    typer.secho(" ".join(cmd), fg=typer.colors.YELLOW)
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
    app = Flask("pavo")
    settings = initialize_config(
        app=app, override_config=overrides, force_env="development"
    ).settings

    if not settings.DATASET_PATHS:
        warnings.warn(
            "no DATASET_PATHS specified! (set via cmdline in dev or file in prod)"
        )

    # print some extra info
    typer.secho(" * Loading datasets:", fg=typer.colors.GREEN)
    for ds in settings.dataset_paths:
        typer.secho(f"   - '{ds!s}'", fg=typer.colors.GREEN)
    typer.secho(
        f" * Using cache_path: '{settings.cache_path!s}'", fg=typer.colors.GREEN
    )

    # run development app
    app = create_app(configured_app=app)
    app.run(host=app.config.SERVER, port=app.config.PORT, debug=app.config.DEBUG)  # type: ignore


# --- production subcommands --------------------------------------------------

cli_prod = typer.Typer(
    help="production subcommands",
    no_args_is_help=True,
)
cli.add_typer(cli_prod, name="production")


@cli_prod.command(name="run")
def prod_run(
    sanity_check: bool = typer.Option(True, help="check some settings before launch")
) -> None:
    """run production webserver"""
    app = Flask("pavo")
    settings = initialize_config(app=app, force_env="production").settings

    if sanity_check:
        # acquire the configuration
        if not settings.dataset_paths:
            typer.secho("no dataset_paths defined", err=True, fg=typer.colors.RED)
            raise typer.Exit(code=1)
        if settings.current_env.lower() != "production":
            typer.secho(
                f"not running the production env: {settings.current_env!r}",
                err=True,
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

    # fmt: off
    cmd = [
        "uwsgi",
        "--http", f"{settings.SERVER}:{settings.PORT}",
        "--env", f"{settings.ENV_SWITCHER_FOR_DYNACONF}=production",
        "--manage-script-name",
        "--mount", "/=pavo.app:create_app()",
        "--lazy-apps",
        "--master",
        "--buffer-size", "8192",
        "--processes", str(settings.UWSGI_NUM_PROCESSES)
    ]
    # fmt: on

    typer.secho("dispatching to uwsgi:", fg=typer.colors.GREEN)
    os.execvp(file="uwsgi", args=cmd)


if __name__ == "__main__":
    cli()
