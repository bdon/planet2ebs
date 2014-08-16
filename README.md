## Installation

`pip install planet2ebs` 

(may need `sudo`)

## Usage

The environment variables `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are required.

AWS Region defaults to `us-west-2`.

### Copy
Creates an EBS volume containing the specified OSM .PBF file.

    $ planet2ebs copy http://download.geofabrik.de/north-america/us/hawaii-latest.osm.pbf
	...
     -> Created vol-111111 (pbf, 25 GB)
     
* For the planet: [planet.openstreetmap.org/pbf](http://planet.openstreetmap.org/pbf/)
* For country-level extracts: [Geofabrik Downloads](http://www.geofabrik.de/data/download.html)
* For metro-level extracts: [Mapzen Metro Extracts](https://mapzen.com/metro-extracts/)

### Import
Creates a rendering database on an EBS volume from the .PBF stored on the given volume.

By default, uses the [imposm3]() mapping [example-mapping.json]().

    $ planet2ebs import vol-111111
    ...
    -> Created vol-222222 (pgdata, 180 GB)

* To use a custom mapping: `planet2ebs import -mapping=mapping.json vol-111111`


### Start
Starts an EC2 instance using the given data volume, and creates a read-only rendering user.

    $ planet2ebs start vol-222222
    ...
	-> Started postgres://render:password@3-3-3-3.ec2.amazonaws.com/osm`

* To set the `render` user password: `planet2ebs start -password=PASSWORD vol-222222`
* This instance must be terminated manually. It can be rebooted without problems.

### List
Lists volumes and instances created by `planet2ebs` and how they were created.

	$ planet2ebs ls
	id			type	size		source
    vol-111111  pbf     25 GB  		http://example.com/something/osm.pbf
    vol-222222  pgdata  180 GB 		vol-111111
    i-333333    db      r3.large	vol-222222

### Global Options
  
* `-region=REGION`: the AWS region.
* `-ami=ami-444444`: use an alternate AMI. Needed if you build the AMI yourself and/or are using a non-US region.
 
## Development

`ami/` - builds the AMI used for these operations

Other typical EC2 operations such as deleting volumes and terminating instances are better done with the official AWS CLI.

You can get that on Mac with `brew install ec2-api-tools`.
