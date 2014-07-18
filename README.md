# Magna Carta Holy Metadata (MCHM)
Magna Carta Holy Metadata (MCHM) is a simple Flask application that provides an http metadata service for virtual machines using cloud-init and the nocloudnet data source. It also works for hosting Kickstart files.

Generate your configuration data, HTTP POST json formatted data to MCHM. Config data hangs out for an hour on a URL you can give to cloud-init or kickstart in a kernel param, then it's deleted automatically.

Nice, right?

## Dependencies
* Python 2.7.6+ (see requirements.txt for module dependencies)
* MongoDB 2.4+

## Motivation
* [To do this](http://smoser.brickies.net/ubuntu/nocloud/)
* [And also this](https://access.redhat.com/site/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s2-kickstart2-networkbased.html)

## Installation
1. Clone the project and install requirements. You should use a virtualenv.

    ```bash
    git clone https://github.com/pwyliu/magna-carta-holy-metadata.git
    cd magna-carta-holy-metadata
    pip install -r requirements.txt
    ```

2. Create an `instance` folder in the project root and create config and key files. There is a sample config in the support directory.
   
    ```bash
    cd magna-carta-holy-metadata
    mkdir instance
    # generate a key file
    head -c 32 /dev/urandom > instance/app.key
    # copy the sample config and edit for your environment
    cp support/conf.py.example instance/conf.py
    vim instance/conf.py
    ```

3. Run the build_indexes script. MCHM uses a [MongoDB TTL collection](http://docs.mongodb.org/manual/tutorial/expire-data/) so that records are automatically deleted after an hour.

    ```bash
    ./manage.py build_indexes
    ```

4. MCHM is intended to be run behind Gunicorn+Nginx, but you can start it with the built in webserver for testing.
    
    ```bash
    ./manage.py runserver
    ```

5. There are sample Upstart and Nginx confs in the support folder for real production.

## API Endpoints
There are only three endpoints: `submit`, `lookup` and `phonehome`. Everything is in [views.py](https://github.com/pwyliu/magna-carta-holy-metadata/blob/master/mchm/views.py).

###/api/submit
`POST` json formatted data to this endpoint. The content type header must be `application/json`. MCHM will respond with an id and urls you can get the data on. TTL is how long before the document is purged by the database.

####Creating new documents
For cloud-init `POST` with `install-type: cloud-init`, `user-data: <my user data>` and `meta-data: <my meta data>`. 

For kickstart, `POST` with `install-type: kickstart` and `ks-data: <my kickstart file>` 

```bash
# Creating a cloud-init file:
curl https://mchm.mydomain.local/api/submit -X POST \
-H "Content-type:application/json" \
-d '{"install-type":"cloud-init","user-data":"my cloud-init userdata","meta-data":"my cloud-init metadata"}'

{
  "created_at": "Fri Jul 18 23:40:50 2014", 
  "id": "53c9b0824ecee371865ad9eb", 
  "install_type": "cloud-init", 
  "ipv4_url": "https://mchm.mydomain.local/api/lookup/53c9b0824ecee371865ad9eb/", 
  "phonehome_status": false, 
  "status": "ok", 
  "ttl": 3600, 
  "zeroconf_url": "https://169.254.169.254/api/lookup/53c9b0824ecee371865ad9eb/"
}

# Creating a kickstart file:
curl https://mchm.mydomain.local/api/submit -X POST \
-H "Content-type:application/json" \
-d '{"install-type":"kickstart","ks-data":"my kickstart file"}'

{
  "created_at": "Fri Jul 18 23:44:46 2014", 
  "id": "53c9b16e4ecee37185d3c8d5", 
  "install_type": "kickstart", 
  "ipv4_url": "https://mchm.mydomain.local/api/lookup/53c9b16e4ecee37185d3c8d5/", 
  "phonehome_status": false, 
  "status": "ok", 
  "ttl": 3600, 
  "zeroconf_url": "https://169.254.169.254/api/lookup/53c9b16e4ecee37185d3c8d5/"
}
```

####Updating existing documents
Updating works the same as above, except you `POST` with `id: <my id>` instead of `install-type`. Use the id that was returned to you on document creation. Updating is useful if you need to know the retrieval URL ahead of time so you can put it into a cloud-init phonehome module (for example, [Strikepackage](https://github.com/pwyliu/strikepackage) does this). Post, get the response, then post again to update.

```bash
# Updating a cloud-init file...
curl https://mchm.mydomain.local/api/submit -X POST \
-H "Content-type:application/json" \
-d '{"id":"530402e6844de405b7d48343","user-data":"my updated cloud-init userdata","meta-data":"my updated cloud-init metadata"}'

{
  "created_at": "Fri Jul 18 23:40:50 2014", 
  "id": "53c9b0824ecee371865ad9eb", 
  "install_type": "cloud-init", 
  "ipv4_url": "https://mchm.mydomain.local/api/lookup/53c9b0824ecee371865ad9eb/", 
  "phonehome_status": false, 
  "status": "updated", 
  "ttl": 3600, 
  "zeroconf_url": "https://169.254.169.254/api/lookup/53c9b0824ecee371865ad9eb/"
}

# Updating a kickstart file...
curl https://mchm.mydomain.local/api/submit -X POST \
-H "Content-type:application/json" \
-d '{"id":"5303fe26844de4049723a56e","ks-data":"my updated kickstart info"}'

{
  "created_at": "Fri Jul 18 23:44:46 2014", 
  "id": "53c9b16e4ecee37185d3c8d5", 
  "install_type": "kickstart", 
  "ipv4_url": "https://mchm.mydomain.local/api/lookup/53c9b16e4ecee37185d3c8d5/", 
  "phonehome_status": false, 
  "status": "updated", 
  "ttl": 3600, 
  "zeroconf_url": "https://169.254.169.254/api/lookup/53c9b16e4ecee37185d3c8d5/"
}
```

###/api/lookup/\<id>/\<field>/
`GET` a cloud-init file. MCHM will show the right output for cloud-init and kickstart. See "base" in the templates folder for the cloud-init data source page.

```bash
curl https://mchm.mydomain.local/api/53c9b0824ecee371865ad9eb/
curl https://mchm.mydomain.local/api/53c9b0824ecee371865ad9eb/user-data
curl https://mchm.mydomain.local/api/53c9b0824ecee371865ad9eb/meta-data
```

###/api/phonehome/\<id>
`GET` /api/phonehome/\<id> to poll for status.

`POST` to /api/phonehome/\<id> with the (phone_home module)[http://cloudinit.readthedocs.org/en/latest/topics/examples.html#call-a-url-when-finished] so you know cloud-init has finished running. Any `POST` to a valid id will change `phonehome_status` to true, the payload doesn't matter.

```bash
curl https://mchm.mydomain.local/api/phonehome/53c9b0824ecee371865ad9eb \
-X POST \
-d ''

{
  "phonehome_data": {}, 
  "phonehome_status": true, 
  "phonehome_time": "Sat, 19 Jul 2014 00:02:25 GMT"
}
```
## Contributors
Feel free to submit any pull request. I ain't fancy.

## License
The MIT License (MIT)

Copyright (c) 2014 Paul Liu

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