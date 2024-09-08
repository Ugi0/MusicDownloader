FROM python:3.8.5-slim-buster

WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

ENV RUNTIME_DEPENDENCIES="ffmpeg"

RUN apt-get update \
	&& apt-get install -y ffmpeg \
	&& rm -rf /var/lib/apt/lists/*

#install ssh
#RUN apk update && apk add -y --no-cache openssh ffmpeg

#Labels as key value pair
LABEL Maintainer="roushan.me17"

#to COPY the remote file at working directory in container
COPY server.py ./
COPY download.py ./
COPY requirements.txt ./

# Open required ports
EXPOSE 8123

#Set up required packages
RUN apt-get update \
	&& apt-get install -y build-essential \
	&& pip install --no-cache-dir -r requirements.txt \
	&& apt-get remove -y build-essential \
	&& apt-get auto-remove -y \
	&& rm -rf /var/lib/apt/lists/*

#CMD instruction should be used to run the software
#contained by your image, along with any arguments.

CMD [ "python", "-u", "./server.py"]
