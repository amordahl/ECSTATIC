#!/bin/bash

# Clone repository
CUR=$(pwd)
cd /
git clone https://github.com/amordahl/sa_microbenchmarks.git
cd sa_microbenchmarks

# Build repo
mvn clean compile package

# Move outputs
mkdir -p /benchmarks
mv ./outputs /benchmarks/sa_microbenchmarks
cd $CUR