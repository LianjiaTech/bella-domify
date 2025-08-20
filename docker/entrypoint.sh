#!/bin/bash

uvicorn server.app:app --port 8080 --host 0.0.0.0 --workers 4
