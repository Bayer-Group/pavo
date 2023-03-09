# howto setup the dev environment

I assume you have `git` and `conda` installed.

0. `git clone git@github.com:bayer-group/pavo.git && cd pavo`
2. `conda env create -f environment.yml`
3. `conda activate pavo`

Now you need a pado dataset somewhere. See `https://github.com/Bayer-Group/pado`
Either provide the path as commandline argument to command `5.` or run
`pavo config default > .pado.toml`
and set the PADO_DATASETS and PADO_STORAGE_OPTIONS variables in the config file.

4. Run `pavo development js` to build the javascript. (`--watch` will rebuild on changes of the js source files)
5. Run `pavo development run` to launch the pavo dev server in debug mode

Happy hacking! :sunglasses:
