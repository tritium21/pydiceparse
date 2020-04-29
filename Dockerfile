FROM ubuntu:bionic
ENV DEBIAN_FRONTEND noninteractive
WORKDIR /diceparse
COPY diceparse.py .
COPY README.rst .
COPY setup.py .
RUN apt-get update && apt-get upgrade -y && apt-get install -y python3-venv
RUN python3 -m venv env && env/bin/python -m pip install --upgrade pip setuptools wheel && env/bin/python -m pip install .
CMD ["/bin/bash"]