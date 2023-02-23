# howto setup the dev environment

I assume you have `git`, `conda` and `conda-devenv` installed.

0. `git clone git@github.com:bayer-group/pavo.git && cd pavo`
1. `PAVO_DEVEL=True conda devenv -f environment.devenv.yml --print > environment.yml`
2. `conda env create -f environment.yml`
3. `conda activate pavo`
4. `npm install`
5. `supervisord -c dev/pavo.conf`

this should spawn the flask server in development mode and run the celery
workers and scheduler as well as run the frontend compiler parcel in watch mode.

You should be able to reach the server at 127.0.0.1:5000 and the celery task
overview at 127.0.0.1:5555

NOTE: celery won't restart workers on code changes... (see issue #15)
