#!/usr/bin/env python

import os, sys, optparse
import boto.ec2
from boto.ec2.connection import EC2Connection
import time
import json

import fabric.api
from fabric.network import disconnect_all

import objects

from pkg_resources import resource_string
import StringIO

USAGE = """usage: planet2ebs.py url
  Simple tool to create EBS volumes containing OpenStreetMap rendering databases.
  Always creates one or more EBS volumes.

  planet2ebs copy http://www.example.com/osm.pbf
    creates an EBS volume containing this data.
    Defaults to writing "osm.pbf" at the root of the volume.
    Example output:
    -> Created ebs://vol-999 (pbf)

  planet2ebs import ebs://vol-999 mapping.json
    Creates a PostgreSQL database on an EBS volume, from the given EBS volume (assumes /osm.pbf)
    Example output:
    -> Created ebs://vol-888 (pgdata)

  planet2ebs import http://example.com/osm.pbf mapping.json
    Creates a PostgreSQL database from a PBF file, also caching the PBF file in an EBS volume.
    Example output:
    -> Created ebs://vol-777 (pbf)
    -> Created ebs://vol-888 (pgdata)

  planet2ebs start ebs://vol-888
    Starts the PostgreSQL database.
    Example output:
    -> Started postgres://render:password@111.111.111.111/osm"

    You are responsible for terminating this instance.
    Options:
      Launch with another private key
      Specify a password
"""

try:
   os.environ["AWS_ACCESS_KEY_ID"]
   os.environ["AWS_SECRET_ACCESS_KEY"]
except KeyError:
   print "Please set the environment variables AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
   sys.exit(1)

AMI_MAPPING = {
 'us-west-1':'ami-1f7c705a',
 'us-west-2':'ami-4fbffa7f',
 'us-east-1':'ami-06b4686e'
}
print "Defaulting to region us-west-2"

# 4 levels of import performance
# level 1 - database < 4 gb, for small extracts and testing
# level 2,3 - suitable for small countries
# level 4 - you need to use this for planet imports

IMPORT_CONFIGS = {
  1:{'instance_type':'m3.medium','disk_size':4  ,'hourly_cost':0.070},
  2:{'instance_type':'r3.large' ,'disk_size':32 ,'hourly_cost':0.175},
  3:{'instance_type':'r3.xlarge','disk_size':80 ,'hourly_cost':0.350},
  4:{'instance_type':'i2.xlarge','disk_size':800,'hourly_cost':0.853}
}

# 3 levels of database performance
# depends on how much memory you want.

START_CONFIGS = {
  1:{'instance_type':'m3.medium','memory':3.75,'hourly_cost':0.070},
  2:{'instance_type':'r3.large' ,'memory':15  ,'hourly_cost':0.175},
  3:{'instance_type':'r3.xlarge','memory':30.5,'hourly_cost':0.350},
}

def doLs(conn):
  print "id\t\tstate\t\tcreated\t\t\t\tsize\ttype\tsource"
  for v in conn.get_all_volumes(filters={'tag-key':'planet2ebs'}):
    print v.id + "\t" + v.update() + "\t" + v.create_time + "\t" + str(v.size) + "\t" + v.tags['planet2ebs'] + "\t" + v.tags['planet2ebs-source']
  for i in conn.get_only_instances(filters={'tag-key':'planet2ebs'}):
    print i.id + "\t" + i.update() + "\t" + i.launch_time + "\t" + i.instance_type + "\t" + i.tags['planet2ebs'] + "\t" + i.tags['planet2ebs-source']

def doStart(conn, args):
  print "Starting database from volume"

  pgdata_url = args[1]
  pgdata = objects.PbfSource(pgdata_url)
  try:
    vol = conn.get_all_volumes([pgdata.netloc])[0]
    if vol.update() != "available":
       print "Pgdata volume unavailable."
       sys.exit(1)
  except:
    print "Pgdata volume missing."
    sys.exit(1)

  timestamp = int(time.time())
  fabric.api.env.key_filename = "planet2ebs-{0}.pem".format(timestamp)
  fabric.api.env.connection_attempts = 10

  i = objects.Instance(conn,timestamp,{'planet2ebs':'db','planet2ebs-source':pgdata_url}).__enter__()
  fabric.api.env.host_string = "ubuntu@{0}".format(i.public_dns_name)
  cm = objects.PbfSourceEbsCm(pgdata,conn,fabric.api,i.id,"pgdata")
  # TODO: should auto-mount on startup, edit fstab
  mountpoint = cm.__enter__()

  pg_hba = StringIO.StringIO(resource_string(__name__, 'pg_config/pg_hba.conf'))
  pg_conf = StringIO.StringIO(resource_string(__name__, 'pg_config/postgresql.conf'))
  fabric.api.put(pg_hba,"/etc/postgresql/9.3/main/pg_hba.conf",use_sudo=True)
  fabric.api.put(pg_conf,"/etc/postgresql/9.3/main/postgresql.conf",use_sudo=True)
  fabric.api.sudo("echo 'auto' > /etc/postgresql/9.3/main/start.conf")
  fabric.api.sudo("chown -R postgres:postgres /mnt/pgdata")
  fabric.api.sudo("service postgresql start")
  fabric.api.run("psql -U postgres -c \"CREATE USER render WITH PASSWORD 'default_password'\"",warn_only=True)
  fabric.api.run("psql -U postgres -c \"ALTER USER render PASSWORD 'default_password'\"",warn_only=True)
  fabric.api.run("psql -U postgres osm -c \"GRANT SELECT ON ALL TABLES IN SCHEMA public TO render\"",warn_only=True)
  print "Connect like this my friend: psql -U render -h {0} osm".format(i.public_dns_name)

def doCopy(conn, args):
  pbf_url = args[1]
  print "PBF Source " + pbf_url
  pbfsource = objects.PbfSource(pbf_url)

  try:
    size = pbfsource.size(conn)
    print "Size is {0} GB".format(size)
  except Exception as e:
    print e
    sys.exit(1)

  timestamp = int(time.time())
  fabric.api.env.key_filename = "planet2ebs-{0}.pem".format(timestamp)
  fabric.api.env.connection_attempts = 10

  print "Copying file to EBS volume..."
  with objects.Instance(conn, timestamp) as i:
    fabric.api.env.host_string = "ubuntu@{0}".format(i.public_dns_name)
    with objects.NewArtifact(conn, i, fabric.api,size,"artifact",{'planet2ebs':'pbf','planet2ebs-source':pbf_url}) as artifact:
      with pbfsource.use(conn, fabric.api, i.id) as path:
        fabric.api.run("cp {0} {1}".format(path, artifact.mountpoint))
      print "Output: " + artifact.output()
    disconnect_all()

def doImport(conn, args):
  pbf_url = args[1]
  print "PBF Source " + pbf_url
  pbfsource = objects.PbfSource(pbf_url)

  try:
    size = pbfsource.size(conn)
    print "Size is {0} GB".format(size)
  except Exception as e:
    print e
    sys.exit(1)

  timestamp = int(time.time())
  fabric.api.env.key_filename = "planet2ebs-{0}.pem".format(timestamp)
  fabric.api.env.connection_attempts = 10

  if len(args) > 2:
    print "Using mapping {0}".format(args[2])
    contents = open(args[2]).read()
    json.loads(contents) #sanity check
  else:
    print "Using default mapping"
    contents = resource_string(__name__, 'default_mapping.json')

  with objects.Instance(conn, timestamp) as i:
    fabric.api.env.host_string = "ubuntu@{0}".format(i.public_dns_name)
    with objects.NewArtifact(conn, i, fabric.api,size*5,"pgdata",{'planet2ebs':'pgdata','planet2ebs-source':pbf_url}) as artifact:
      with pbfsource.use(conn, fabric.api, i.id) as path:
        pg_hba = StringIO.StringIO(resource_string(__name__, 'pg_config/pg_hba.conf'))
        pg_conf = StringIO.StringIO(resource_string(__name__, 'pg_config/postgresql.conf'))
        fabric.api.put(pg_hba,"/etc/postgresql/9.3/main/pg_hba.conf",use_sudo=True)
        fabric.api.put(pg_conf,"/etc/postgresql/9.3/main/postgresql.conf",use_sudo=True)
        fabric.api.sudo("echo 'auto' > /etc/postgresql/9.3/main/start.conf")
        fabric.api.put(StringIO.StringIO(contents),"mapping.json")
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

def run():
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

  if operation == "copy":
    doCopy(conn, args)
  elif operation == "import":
    doImport(conn, args)
  elif operation == "start":
    doStart(conn, args)
  elif operation == "ls":
    doLs(conn)
  else:
    parser.print_help()
