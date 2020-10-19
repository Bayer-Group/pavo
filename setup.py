from setuptools import setup

setup(
    use_scm_version={
        "write_to": "pado_visualize/pado/ext/visualize/_version.py",
        "version_scheme": "post-release",
    }
)
