#!/bin/bash

# turn on bash's job control
set -m

# Start the primary process and put it in the background
gunicorn --bind 0.0.0.0:5000 -w 4 app:app &

# Start the helper process
celery -A app.celery_app worker -l INFO

# the my_helper_process might need to know how to wait on the
# primary process to start before it does its work and returns


# now we bring the primary process back into the foreground
# and leave it there
fg %1