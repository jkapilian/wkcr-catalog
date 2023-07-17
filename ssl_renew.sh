#!/bin/bash

COMPOSE="/snap/bin/docker-compose --ansi never"
DOCKER="/snap/bin/docker"

cd /home/library/wkcr-catalog/
$COMPOSE run certbot renew && $COMPOSE kill -s SIGHUP webproxy
$DOCKER system prune -af
