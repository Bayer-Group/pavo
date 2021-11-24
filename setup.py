import distutils.command.build
import os
import pathlib
import shutil
from setuptools import Command
from setuptools import setup


# noinspection PyAttributeOutsideInit
class BuildFrontendCommand(Command):
    """build_js subcommand for npm building the frontend"""

    def initialize_options(self):
        self.build_lib = None
        self.npm = None

    def finalize_options(self):
        self.set_undefined_options('build', ('build_lib', 'build_lib'))
        if self.npm is None:
            self.npm = shutil.which("npm")

    def run(self):
        if not self.npm:
            raise RuntimeError("installing pado_visualize from source requires npm")
        self.spawn([self.npm, "install"])
        self.spawn([self.npm, "run", "deploy"])
        src = os.path.join("pado_visualize", "static")
        dst = os.path.join(self.build_lib, "pado_visualize", "static")
        self.copy_tree(src, dst)


# noinspection PyUnresolvedReferences
distutils.command.build.build.sub_commands.append(('build_js', None))


def all_files_at(path):
    p = pathlib.Path(path)
    return [
        os.fspath(f.relative_to(p.parent))
        for f in p.glob("**/*")
        if f.name not in {".DS_Store"}
    ]


setup(
    use_scm_version={
        "write_to": "pado_visualize/_version.py",
        "version_scheme": "post-release",
    },
    package_data={
        'pado_visualize': [
            *all_files_at('pado_visualize/templates'),
        ]
    },
    cmdclass={
        'build_js': BuildFrontendCommand
    }
)
