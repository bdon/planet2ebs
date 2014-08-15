#!/usr/bin/env python

import os, sys, optparse
import boto.ec2
from boto.ec2.connection import EC2Connection
import time
import json

import fabric.api
from fabric.network import disconnect_all

import objects

USAGE = """usage: planet2ebs.py url
  Simple tool to create EBS volumes containing OpenStreetMap rendering databases.
  Always creates one or more EBS volumes.

  planet2ebs.py import http://www.example.com/osm.pbf
    (No imposm3 mapping provided) creates an EBS volume containing this data.
    Defaults to writing "osm.pbf" at the root of the volume.
    Example output:
    -> Created ebs://vol-999 (pbf)

  planet2ebs.py import ebs://vol-999 mapping.json
    Creates a PostgreSQL database on an EBS volume, from the given EBS volume (assumes /osm.pbf)
    Example output:
    -> Created ebs://vol-888 (pgdata)

  planet2ebs.py --cache import http://example.com/osm.pbf mapping.json
    Creates a PostgreSQL database from a PBF file, also caching the PBF file in an EBS volume.
    Example output:
    -> Created ebs://vol-777 (pbf)
    -> Created ebs://vol-888 (pgdata)

  planet2ebs.py run ebs://vol-888
    Starts the PostgreSQL database.
    Example output:
    -> Started postgres://render:password@111.111.111.111/osm"
"""

try:
   os.environ["AWS_ACCESS_KEY_ID"]
   os.environ["AWS_SECRET_ACCESS_KEY"]
except KeyError:
   print "Please set the environment variables AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
   sys.exit(1)

def doImport(conn, args):
  pbf_url = args[1]
  print "PBF Source " + pbf_url
  pbfsource = objects.PbfSource(pbf_url)
  if not pbfsource.sanitycheck(conn):
    print pbf_url + " does not exist, or is inaccessible."
    sys.exit(1)

  timestamp = int(time.time())
  fabric.api.env.key_filename = "planet2ebs-{0}.pem".format(timestamp)
  fabric.api.env.connection_attempts = 10

  if len(args) == 2:
    print "No mapping; Copying file to EBS volume..."
    with objects.Instance(conn, timestamp) as i:
      fabric.api.env.host_string = "ubuntu@{0}".format(i.public_dns_name)
      with objects.NewArtifact(conn, i, fabric.api,"artifact") as artifact:
        with pbfsource.use(conn, fabric.api, i.id) as path:
          fabric.api.run("cp {0} {1}".format(path, artifact.mountpoint))
        print "Output: " + artifact.output()
      disconnect_all()

  else:
    mapping = args[2]
    print "Using mapping {0}".format(mapping)
    json.loads(open(mapping).read()) #sanity check

    with objects.Instance(conn, timestamp) as i:
      fabric.api.env.host_string = "ubuntu@{0}".format(i.public_dns_name)
      with objects.NewArtifact(conn, i, fabric.api,"pgdata") as artifact:
        with pbfsource.use(conn, fabric.api, i.id) as path:
          fabric.api.put("pg_config/pg_hba.conf","/etc/postgresql/9.3/main/pg_hba.conf",use_sudo=True)
          fabric.api.put("pg_config/postgresql.conf","/etc/postgresql/9.3/main/postgresql.conf",use_sudo=True)
          fabric.api.put("pg_config/start_auto.conf","/etc/postgresql/9.3/main/start.conf",use_sudo=True) # Why?
          fabric.api.put(mapping,"mapping.json")
          fabric.api.sudo("mv /var/lib/postgresql/9.3/main {0}".format(artifact.mountpoint))
          fabric.api.sudo("service postgresql start")
          fabric.api.sudo("su postgres -c 'createuser -s importer'")
          fabric.api.sudo("su postgres -c 'createdb osm -O importer'")
          fabric.api.run("psql osm -U importer -c 'CREATE EXTENSION postgis;'")
          fabric.api.run("imposm3 import -mapping={0} -read {1} -connection={2} -write -deployproduction -optimize".format(
            "mapping.json",
            path,
            "postgis:///osm?host=/var/run/postgresql\&user=importer")) #this fucking kills me
          fabric.api.sudo("service postgresql stop")
        print "Output: " + artifact.output()
      disconnect_all()

if __name__ == '__main__':
  parser = optparse.OptionParser(USAGE)
  (options, args) = parser.parse_args()
  if len(args) == 0:
    parser.print_help()
    sys.exit(1)

  operation = args[0]

  conn = boto.ec2.connect_to_region("us-west-2",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
  )

  if operation == "import":
    doImport(conn, args)

  elif operation == "start":
    pass

  else:
    parser.print_help()
