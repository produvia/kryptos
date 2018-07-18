#!/bin/bash
echo "Rebuilding frontend"
rm -rf kryptos/app/static/spa-mat
cd frontend/ quasar clean && quasar build && cd ..
cp -r frontend/dist/spa-mat kryptos/app/static/spa-mat
