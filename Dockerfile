FROM python:3.8

RUN apt-get update

RUN mkdir /work
WORKDIR /work  

RUN pip install --update pip  
RUN pip install dash requests pandas plotly 

COPY app.py /work
COPY sen_req.py /work 

