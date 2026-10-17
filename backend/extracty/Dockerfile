FROM python:3.14

WORKDIR /code
COPY . .
# ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN uv sync 

ENTRYPOINT [ "python3" , "refresh.py" ]
