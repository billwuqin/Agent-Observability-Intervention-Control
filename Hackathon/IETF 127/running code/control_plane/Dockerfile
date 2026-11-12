# Control & Enforcement Plane. Build from this directory:
#   docker build -t icon-control-plane .
#   docker run --rm icon-control-plane
FROM python:3.12-alpine

WORKDIR /opt/icon
COPY icon_control_plane /opt/icon/icon_control_plane
COPY schemas /opt/icon/schemas

ENV PYTHONPATH=/opt/icon
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER nobody
ENTRYPOINT ["python", "-m", "icon_control_plane"]
