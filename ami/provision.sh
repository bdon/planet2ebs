#!/bin/bash

set -e


sudo /usr/sbin/update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
# install PostgreSQL 9.3 with PostGIS
# https://wiki.postgresql.org/wiki/Apt

sudo apt-get update
sudo apt-get install -y wget ca-certificates
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
sudo apt-get update
sudo apt-get install -y postgresql-9.3-postgis-2.1

echo "disabled" | sudo tee /etc/postgresql/9.3/main/start.conf

wget http://imposm.org/static/rel/imposm3-0.1dev-20150515-593f252-linux-x86-64.tar.gz
tar -xvzf imposm3-0.1dev-20150515-593f252-linux-x86-64.tar.gz
echo "export PATH=~/imposm3-0.1dev-20150515-593f252-linux-x86-64:$PATH" >> ~/.profile
#. ~/.profile

# planet2ebs should be able to run on its own ami
sudo apt-get install -y python-pip python-dev
