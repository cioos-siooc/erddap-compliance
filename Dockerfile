# syntax=docker/dockerfile:1

FROM python:3.10-slim-bookworm
WORKDIR /app
RUN apt-get update -q && apt-get upgrade -y && apt-get install -y libudunits2-dev gcc
RUN pip install uv
COPY pyproject.toml uv.lock .
ENV UDUNITS2_XML_PATH="/usr/share/xml/udunits/udunits2.xml"
RUN uv sync
COPY erddap_compliance erddap_compliance
ENTRYPOINT [ "python", "-m" , "erddap_compliance", "-o","/results"]
