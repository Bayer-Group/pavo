from __future__ import annotations

import concurrent.futures
import os

import click
import redis
from flask import current_app
from flask.cli import FlaskGroup
from flask.cli import with_appcontext
from tqdm import tqdm

from pado_visualize.app import create_app
from pado_visualize.data import dataset
from pado_visualize.slides.utils import thumbnail_image


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


@cli.command()
@click.option("--threads", default=6, type=int, show_default=True)
@with_appcontext
def create_thumbnails(threads):
    """precompute all thumbnail images"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        ip = dataset.images
        futures = [
            executor.submit(thumbnail_image, image_id, image, base_path=current_app.config["CACHE_PATH"])
            for image_id, image in tqdm(ip.items(), desc="dispatch", total=len(ip))
        ]
        for f in tqdm(concurrent.futures.as_completed(futures), desc="thumbnail", total=len(ip)):
            f.result()


@cli.command()
@click.option("--image-id", type=str)
@click.option("--output", default=None, type=str)
@with_appcontext
def create_deepzoom(image_id, output):
    """create a deepzoom image on disk at the output location"""
    raise NotImplementedError("todo")


if __name__ == "__main__":
    cli()
