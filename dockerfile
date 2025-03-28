FROM arm64v8/python:3.11-slim

WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

ENV RUNTIME_DEPENDENCIES="ffmpeg"

WORKDIR /app

#Set up required packages
RUN apt-get update && apt-get install -y \
	libtag1-dev \
	ffmpeg \
	gcc \
	python3-dev \
	build-essential \
	--no-install-recommends && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/*

COPY server.py .
COPY requirements.txt .

EXPOSE 80

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python"]
CMD ["server.py"]
