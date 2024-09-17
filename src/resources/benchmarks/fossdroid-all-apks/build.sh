#!/bin/bash

CURDIR=$(pwd)
cd /
mkdir -p benchmarks
cd /benchmarks
mkdir fossdroid
cd fossdroid
git clone https://github.com/Pancax/fossdroid_apks.git
cd $CURDIR