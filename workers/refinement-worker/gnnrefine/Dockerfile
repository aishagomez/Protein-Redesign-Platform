FROM python:3.8-slim

ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    wget \
    curl \
    unzip \
    cmake \
    g++ \
    libglib2.0-0 \
    libxext6 \
    libsm6 \
    libxrender1 \
    libssl-dev \
    ca-certificates \
    libeigen3-dev \
    libboost-all-dev \
    dssp \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install \
    torch==1.4.0 \
    dgl==0.4.3 \
    biopython==1.75 \
    numpy==1.18.1

RUN git clone https://github.com/cmbi/dssp.git /opt/dssp && \
    cd /opt/dssp && \
    ./autogen.sh && \
    ./configure && \
    make -j4 && \
    make install && \
    ln -s /usr/local/bin/mkdssp /usr/local/bin/dssp

WORKDIR /opt

RUN wget https://graylab.jhu.edu/download/PyRosetta4/archive/release/PyRosetta4.MinSizeRel.python38.linux/PyRosetta4.MinSizeRel.python38.linux.release-387.tar.bz2 && \
    tar -xjf PyRosetta4.MinSizeRel.python38.linux.release-387.tar.bz2

WORKDIR /opt/PyRosetta4.MinSizeRel.python38.linux.release-387/setup

RUN python setup.py install

WORKDIR /app

COPY code/ /app/code/
COPY data/ /app/data/

COPY metadata/ /app/metadata/

ENV DGLBACKEND=pytorch

CMD ["bash"]