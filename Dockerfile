# Jobs Finder Board
#
# The board needs nothing but a Python interpreter. The image exists so you do
# not have to care which Python you have, or whether you have one at all.

FROM python:3.12-slim

# Run as a non-root user. The board writes into a bind-mounted directory, so the
# uid needs to line up with your host user; override at build time if yours is
# not 1000:
#   docker compose build --build-arg UID=$(id -u) --build-arg GID=$(id -g)
ARG UID=1000
ARG GID=1000
RUN groupadd -g "${GID}" board 2>/dev/null || true \
 && useradd -m -u "${UID}" -g "${GID}" board 2>/dev/null || true

WORKDIR /app

COPY dashboard/ ./dashboard/
COPY scripts/ ./scripts/

# applications/ is bind-mounted at run time. Create it so a first run without a
# mount still starts instead of erroring.
RUN mkdir -p /app/applications && chown -R "${UID}:${GID}" /app

USER ${UID}:${GID}

ENV BOARD_PORT=8765 \
    BOARD_HOST=0.0.0.0 \
    BOARD_NO_BROWSER=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8765

# BOARD_HOST=0.0.0.0 is required for the host to reach the container at all.
# It is safe here only because compose publishes the port to 127.0.0.1.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"BOARD_PORT\"]}/').read()" || exit 1

CMD ["python", "dashboard/serve.py"]
