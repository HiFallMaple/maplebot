FROM python:3.12-slim-bookworm

WORKDIR /app
RUN mkdir -p /app/bin
COPY src/ /app/src/
COPY scripts/ /app/scripts/
COPY locales/ /app/locales/
COPY requirements.txt /app

RUN apt-get update && apt-get install -y libopus-dev gettext curl xz-utils

RUN chmod +x /app/scripts/*.sh
RUN /app/scripts/get_ffmpeg.sh

RUN chmod +x /app/bin/*

RUN python3 -m pip install -r requirements.txt

CMD ["/app/scripts/entrypoint.sh"]