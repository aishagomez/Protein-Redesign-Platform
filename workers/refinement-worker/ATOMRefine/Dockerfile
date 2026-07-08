FROM nvidia/cuda:11.3.1-cudnn8-runtime-ubuntu20.04

RUN apt-get update && apt-get install -y wget bzip2 git build-essential && rm -rf /var/lib/apt/lists/*

ENV CONDA_DIR=/opt/conda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p $CONDA_DIR && rm miniconda.sh

ENV PATH=$CONDA_DIR/bin:$PATH

WORKDIR /app
COPY . /app

RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r


RUN conda env create -f ATOMRefine-linux-cu101.yml

RUN conda run -n ATOMRefine pip install "etils<1.0.0"

SHELL ["conda", "run", "-n", "ATOMRefine", "/bin/bash", "-c"]

RUN chmod +x refine.sh

CMD ["bash"]