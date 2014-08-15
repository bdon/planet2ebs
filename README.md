## Installation

`sudo pip install planet2ebs`

## Usage

The environment variables `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are required.

`planet2ebs.py import http://download.geofabrik.de/north-america/us/hawaii-latest.osm.pbf`

* Creates an EBS volume containing the specified OSM .PBF file.
* Output: `-> Created ebs://vol-999 (pbf)`


`planet2ebs.py import ebs://vol-f848d1fd/osm.pbf example-mapping.json`

* Creates an EBS volume containing a PostgreSQL rendering database, from the data file in volume `vol-f848d1fd` and using the [imposm3]() mapping `example-mapping.json`.
* Output: `-> Created ebs://vol-888 (pgdata)`

`planet2ebs.py start ebs://vol-123123`

* Starts an EC2 instance running the database on the EBS volume `vol-123123`, and creates credentials for a read-only rendering user.
* Output: `-> Started postgres://render:password@1-2-3-4.ec2.amazonaws.com/osm`
* Terminating this instance is left up to you.

## Development

`ami/` - builds the AMI used for these operations