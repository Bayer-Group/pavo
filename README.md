# PAVO: PAthological Visualization Obsession

Welcome to `pavo` :wave:, a visualization tool for
[pado datasets](https://github.com/bayer-group/pado).

`pavo`'s goal is to provide a testbed for easy prototyping of data
visualizations of whole slide images and metadata of digital pathology datasets.

We strive to make your lives as easy as possible: If setting up
`pavo` is hard or unintuitive, if its interface is slow or if its
documentation is confusing, it's a bug in `pavo`.
Always feel free to report any issues or feature requests in the issue tracker!

Development
[happens on github](https://github.com/bayer-group/pavo)
:octocat:


## Installation

To install pavo clone the repo and run `pip install .` Note that you need
a "nodejs==16.*" installation to be able to build from source.


## Usage

`pavo` is used to visualize `pado` datasets. If you have a `pado` dataset
just run:

```shell
pavo production run /path/to/your/dataset
```

and access the web ui under the printed address.


## Development Environment Setup

1. Install `git` and `conda` and `conda-devenv`
2. Clone pavo `git clone https://github.com/bayer-group/pavo.git`
3. Change directory `cd pavo`
4. Run `conda devenv --env PAVO_DEVEL=TRUE -f environment.devenv.yml --print > environment.yml`
5. Run `conda env create -f environment.yml`
6. Activate the environment `conda activate pavo`
7. Setup the javascript dependencies `npm install .` (optional, handled in `setup.py`)

Note that in this environment `pavo` is already installed in
development mode, so go ahead and hack.

- Run tests via `pytest`
- Run the static type analysis via `mypy pavo`
- Launch a development instance via `pavo development run`


## Contributing Guidelines

- Check the [contribution guidelines](CONTRIBUTING.md)
- Please use [numpy docstrings](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard).
- When contributing code, please try to use Pull Requests.
- tests go hand in hand with modules on ```tests``` packages at the same level. We use ```pytest```.


## Acknowledgements

Build with love by the _Machine Learning Research_ group at Bayer.

`pavo`: copyright 2020 Bayer AG
