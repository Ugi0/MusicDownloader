FROM arm64v8/python:3.11-slim

ENV PATH="$PATH:/home/appuser/.local/bin"
ENV RUNTIME_DEPENDENCIES="ffmpeg"

RUN useradd -ms /bin/bash appuser

WORKDIR /app

RUN apt-get update && apt-get install -y \
	libtag1-dev \
	ffmpeg \
	gcc \
	python3-dev \
	build-essential \
	--no-install-recommends && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/*

COPY . .

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "run:app"]
