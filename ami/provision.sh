#!/bin/bash

sudo /usr/sbin/update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

# install PostgreSQL 9.3 with PostGIS
sudo apt-get install -y python-software-properties
sudo apt-add-repository deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main
sudo apt-add-key https://www.postgresql.org/media/keys/ACCC4CF8.asc
sudo apt-get update
sudo apt-get install -y postgresql-9.3-postgis-2.1

echo "disabled" | sudo tee /etc/postgresql/9.3/main/start.conf

wget http://imposm.org/static/rel/imposm3-0.1dev-20140702-ced9f92-linux-x86-64.tar.gz
tar -xvzf imposm3-0.1dev-20140702-ced9f92-linux-x86-64.tar.gz
echo "export PATH=~/imposm3-0.1dev-20140702-ced9f92-linux-x86-64:$PATH" >> ~/.profile
#. ~/.profile
