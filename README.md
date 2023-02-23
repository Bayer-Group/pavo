# PAVO: PAthological Visualization Obsession

[![Milestones](https://img.shields.io/badge/mlr%20milestones-pavo-brightgreen)](https://github.com/bayer-int/pathdrive-pavo/milestones?direction=asc&sort=due_date&state=open)

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


## :warning: :dragon: Here be dragons :dragon: :warning:

This is an early release version, so expect things to break. In its current
version we are targeting unix operating system and experienced developers.
Feedback and contributions are very welcome :heart: <br>
If there are any questions open an issue, and we'll do our best to help!


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

Make sure to have a running instance of redis on your development machine. On
OSX install via homebrew `brew install redis && brew services start redis`. On
Ubuntu `sudo apt install redis && sudo systemctl start redis`.

- Run tests via `pytest`
- Run the static type analysis via `mypy pavo`
- Launch a development instance via `pavo development run`


## Contributing Guidelines

- Please use [numpy docstrings](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard).
- When contributing code, please try to use Pull Requests.
- tests go hand in hand with modules on ```tests``` packages at the same level. We use ```pytest```.


## Acknowledgements

Build with love by the _Machine Learning Research_ group at Bayer.

`pavo`: copyright 2020 Bayer AG
