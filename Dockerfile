FROM ubuntu:20.04
LABEL maintainer="Ilya Khoryzhev"
RUN apt-get update -y && apt-get install -y python3-pip python-dev build-essential
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3", "bot.py"]
