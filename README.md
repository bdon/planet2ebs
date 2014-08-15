planet2ebs - OSM rendering on Amazon EC2

* Caches and creates rendering databases in EBS volumes
* Shut down database instances when you don't need them

`ami` directory - builds the AMI used for these operations

`./planet2ebs.py import http://download.geofabrik.de/north-america/us/hawaii-latest.osm.pbf`
`./planet2ebs.py import ebs://vol-f848d1fd/osm.pbf example-mapping.json`


`./planet2ebs.py start ebs://vol-123123`


`./planet2ebs.py ls`

after running db, you will be able to connect to the psql database like this:
psql 

`planet2ebs cleanup`

Build artifact: 
ebs://


["i2.xlarge",{'/mnt/xvdf','}]
import on instancestore
otherwise need 2 ebs volumes

