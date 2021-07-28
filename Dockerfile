# syntax=docker/dockerfile:experimental

FROM mambaorg/micromamba:0.14.0

# we need git and ssh for pip installs from github
RUN micromamba install -y -n $ENV_NAME -c conda-forge git openssh \
    && micromamba clean --all --yes

# the environment can potentially contain private repos for now
RUN mkdir -p -m 0700 /root/.ssh \
    && ssh-keyscan github.com >> /root/.ssh/known_hosts

ARG ENV_HASH=not-set

# create the environment
COPY environment.docker.yml /root/environment.docker.yml
RUN --mount=type=ssh \
    micromamba install -y -n $ENV_NAME -f /root/environment.docker.yml \
    && micromamba clean --all --yes

WORKDIR /app

ARG SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0
COPY . /app/src
RUN pip install /app/src
COPY .pado_visualize.toml /app

CMD python -m pado_visualize --debug
