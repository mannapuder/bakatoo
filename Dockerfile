FROM python:3.8-buster

WORKDIR /app

RUN apt update
RUN apt install ffmpeg -y

RUN pip install -U pip


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install madmom==0.16.1


COPY . .

CMD [ "python", "app.py"]
