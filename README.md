# Magna Carta Holy Metadata (MCHM)
Magna Carta Holy Metadata (MCHM) is a simple Flask application that provides an http metadata service for virtual machines using cloud-init and the nocloudnet data source. 

HTTP POST json formatted data, it hangs out for an hour on a URL you can give to cloud-init, then it's deleted automatically. Easy. 

## Dependencies
* Python 2.7+ (see requirements.txt for module dependencies)
* MongoDB 2.2+

## Motivation
* [Boom](http://smoser.brickies.net/ubuntu/nocloud/)

## Installation
1. Clone the project and install requirements. You should use a virtualenv.

    ```bash
    git clone https://github.com/pwyliu/magna-carta-holy-metadata.git
    cd magna-carta-holy-metadata
    pip install -r requirements.txt
    ```
2. Edit the configuration file to fit your environment.
   
    ```bash
    cd mchm
    cp site_config.py.example site_config.py
    vim site_config.py
    ```
3. Run build_index script. MCHM uses a [MongoDB TTL collection](http://docs.mongodb.org/manual/tutorial/expire-data/) so that records are automatically deleted after an hour.

    ```bash
    python build_index.py
    ```
4. MCHM is intended to be run behind Gunicorn+Nginx, but you can start it with the built in webserver
    
    ```bash
    ./runserver.py
    ```

## API Endpoints
There are just a couple endpoints available. Everything is clearly laid out in views.py.

####/api/submit/
POST json formatted data to this endpoint. The three required fields are iid, userdata and metadata. iid should be unique, I used the Python UUID module to generate these.

```bash
curl http://mchm.mydomain.local/api/submit/ -X POST -H "Content-type:application/json" -d '{"iid":"some_unique_uuid","user-data":"this is some cloud-init userdata","meta-data":"this is some cloud-init metadata"}'
```

####/api/\<iid>/
GET posted data. The `<iid>` is the iid you submitted in the post.
```bash
curl http://mchm.mydomain.local/api/some_unique_uuid/
```

####/api/\<iid>/\<field>
```bash
curl http://mchm.mydomain.local/api/some_unique_uuid/userdata
curl http://mchm.mydomain.local/api/some_unique_uuid/metadata
curl http://mchm.mydomain.local/api/some_unique_uuid/phonehome
```
GET posted data. Supported fields:
* `userdata`: the userdata you posted
* `metadata`: the metatdata you posted
* `phonehome`: for use with cloud-init's phonehome module. When cloud-init posts here phonehome_status is set to true and phonehome_data contains the post data. See views.py for more details.

## Contributors
Hey man, I'm easy. Just submit a pull request. If you see something which sucks please fix it.

## License
The MIT License (MIT)

Copyright (c) [2014] [Paul Liu]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.