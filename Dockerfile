# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster
WORKDIR /app
RUN apt-get update -q && apt-get upgrade -y && apt-get install -y libudunits2-dev gcc
COPY requirements.txt setup.py setup.py .
ENV UDUNITS2_XML_PATH "/usr/share/xml/udunits/udunits2.xml"
RUN pip install -r requirements.txt
COPY erddap_compliance erddap_compliance
ENTRYPOINT [ "python", "-m" , "erddap_compliance", "-o","/results"]
