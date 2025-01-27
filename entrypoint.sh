#!/bin/bash

if [ "$APP_MODE" = "starter" ]; then
    echo "Running starter.py"
    exec python starter.py
elif [ "$APP_MODE" = "agent" ]; then
    echo "Running agent.py"
    exec python agent.py
else
    echo "No valid APP_MODE specified. Exiting."
    exit 1
fi 