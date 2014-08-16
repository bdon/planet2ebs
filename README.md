## Installation

`sudo pip install planet2ebs`

## Usage

The environment variables `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are required.
Choose a region from `us-west-1`, `us-west-2`, `us-east-1`.
For other regions you must build the AMI yourself:

`planet2ebs copy http://download.geofabrik.de/north-america/us/hawaii-latest.osm.pbf`

* Creates an EBS volume containing the specified OSM .PBF file.
* Output: `-> Created ebs://vol-999 (pbf)`

`planet2ebs import ebs://vol-f848d1fd/osm.pbf`

* Creates an EBS volume containing a PostgreSQL rendering database, from the data file in volume `vol-f848d1fd` and using the [imposm3]() mapping `example-mapping.json`.
* Output: `-> Created ebs://vol-888 (pgdata)`
* options: `-mapping=mapping.json` - specify a different imposm3 mapping

`planet2ebs start ebs://vol-123123`

* Starts an EC2 instance running the database on the EBS volume `vol-123123`, and creates credentials for a read-only rendering user.
* Output: `-> Started postgres://render:password@1-2-3-4.ec2.amazonaws.com/osm`
* Terminating this instance is left up to you.
* options: `password`

Global options:
* `ami`: use an alternate AMI. Needed if you build the AMI yourself.
* `region`: the AWS region.

`planet2ebs ls`

* Lists volumes and instances created by `planet2ebs`, and their source data.

        vol-123123 pbf       http://example.com/something/osm.pbf
        vol-234234 pgdata    vol-123123
        i-345345   db        vol-234234
 
## Development

`ami/` - builds the AMI used for these operations
