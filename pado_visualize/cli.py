import os

import click
import redis
from flask import current_app
from flask.cli import FlaskGroup
from flask.cli import with_appcontext

from pado_visualize.app import create_app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """pado_visualize's commandline interface"""


@cli.command()
@with_appcontext
def clear_redis():
    """delete all entries from the redis queues..."""
    print("redis cleanup: flushall")
    for url in [current_app.config["broker_url"], current_app.config["result_backend"]]:
        print(f">>> {url}")
        try:
            redis.Redis.from_url(url).flushall()
        except BaseException as e:
            print("ERROR", repr(e))
        else:
            print("... OK")


@cli.command()
def tasks_list():
    """launch the celery task monitor"""
    os.execvpe("python", ["python", "-m", "celery", "-A", "pado_visualize.worker", "events"], os.environ)


if __name__ == "__main__":
    cli()
