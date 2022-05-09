FROM python:3.8-buster
ARG PORT
RUN apt update
RUN apt install libasound2-dev libsndfile-dev libsndfile1 -y
COPY ../../Downloads .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install madmom==0.16.1
ENV PORT=$PORT
EXPOSE $PORT
CMD [ "python", "main.py"]
