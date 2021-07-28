import os
import pathlib
from setuptools import setup


def all_files_at(path):
    p = pathlib.Path(path)
    return [os.fspath(f.relative_to(p.parent)) for f in p.glob("**/*")]


setup(
    use_scm_version={
        "write_to": "pado_visualize/_version.py",
        "version_scheme": "post-release",
    },
    package_data={
        'pado_visualize': [
            *all_files_at('pado_visualize/templates'),
            *all_files_at('pado_visualize/static'),
        ]
    }
)
