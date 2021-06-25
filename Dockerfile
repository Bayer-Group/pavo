FROM mambaorg/micromamba:0.14.0

COPY environment.yml /root/environment.yml
RUN micromamba install -y -n $ENV_NAME -f /root/environment.yml \
    && micromamba clean --all --yes

WORKDIR /src

ARG SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0

COPY . /src/pado_visualize
RUN pip install /src/pado_visualize

CMD python -c "print('Hello World')"



# FROM ubuntu:focal

# ENV PATH="/root/miniconda3/bin:${PATH}"
# ARG PATH="/root/miniconda3/bin:${PATH}"

# setup wget (needs certs for downloading via https)
# RUN apt-get update \
#     && apt-get install -y wget ca-certificates \
#     && rm -rf /var/lib/apt/lists/*

# download micromamba
# RUN wget -qO- https://micromamba.snakepit.net/api/micromamba/linux-64/latest | tar -xvj bin/micromamba
# setup mamba base env
# RUN ./bin/micromamba shell init -s bash -p /root/micromamba \
#     && . /root/.bashrc \
#     && micromamba activate

# setup miniconda
# RUN wget \
#     https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
#     && mkdir /root/.conda \
#     && bash Miniconda3-latest-Linux-x86_64.sh -b \
#     && rm -f Miniconda3-latest-Linux-x86_64.sh
# RUN conda --version
# # try to exclusively use conda-forge
# RUN conda config --remove channels defaults \
#     && conda config --append channels conda-forge
# # finalize conda setup
# RUN conda install -n base conda-devenv mamba
# RUN mamba update conda mamba -n base -c conda-forge
#
# #
# COPY . /app
# RUN mamba devenv -f /app/environment.devenv.yml --print > environment.yml
# RUN mamba env create -f environment.yml
#
# # conda activate won't do the trick
#
# RUN pip install .
#
