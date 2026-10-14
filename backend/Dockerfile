# syntax=docker/dockerfile:1

# ---- build stage: compile wheels so the runtime image needs no build tooling ----
FROM python:3.12-slim AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---- runtime stage ----
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore
WORKDIR /app

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* \
 && groupadd --gid 10001 app \
 && useradd --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

# Install the prebuilt wheels, then remove pip itself: it is not needed at runtime
# and its vendored libraries (urllib3, msgpack, ...) otherwise show up in Trivy scans.
COPY --from=build /wheels /wheels
RUN pip install /wheels/* && rm -rf /wheels \
 && pip uninstall -y pip \
 && rm -rf /usr/local/lib/python3.12/ensurepip

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY --chmod=755 start.sh ./

# Never run as root inside the container.
USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

CMD ["./start.sh"]
