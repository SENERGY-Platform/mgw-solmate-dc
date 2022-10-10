FROM python:3-slim-buster

LABEL org.opencontainers.image.source https://github.com/SENERGY-Platform/mgw-solmate-dc

RUN apt-get update && apt-get install git gcc -y

WORKDIR /usr/src/app

COPY . .
RUN pip install --extra-index-url https://www.piwheels.org/simple --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./dc.py"]
