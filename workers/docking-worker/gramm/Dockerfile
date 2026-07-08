FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    gcc \
    g++ \
    make \
    wget \
    curl \
    git \
    fftw3 \
    libfftw3-dev \
    openmpi-bin \
    libopenmpi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

WORKDIR /app

RUN chmod +x build

RUN ./build || make

RUN chmod +x gramm

ENV GRAMMDAT=/app/ANG
ENV GRAMMTEMPLATES=/app/templates

CMD ["bash"]