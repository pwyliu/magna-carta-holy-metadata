# Magna Carta Holy Metadata (MCHM)
Magna Carta Holy Metadata (MCHM) is a simple Flask application that provides an http metadata service for virtual machines using cloud-init and the nocloudnet data source. It also works for hosting Kickstart files.

Generate your configuration data, HTTP POST json formatted data to MCHM. Config data hangs out for an hour on a URL you can give to cloud-init or kickstart in a kernel param, then it's deleted automatically.

Nice, right?

## Dependencies
* Python 2.7+ (see requirements.txt for module dependencies)
* MongoDB 2.2+

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
5. There are sample Upstart and Nginx confs in the support folder.

## API Endpoints
There are just a couple endpoints available. Everything is in [views.py](https://github.com/pwyliu/magna-carta-holy-metadata/blob/master/mchm/views.py).

###/api/submit/
`POST` json formatted data to this endpoint. MCHM will respond with an id and urls you can get the data on. TTL is how long before the document is purged by the database.
#####To create new documents
`POST` with parameter `install-type`. You can choose `cloud-init` or `kickstart`.

```bash
# create a new cloud-init file
curl http://mchm.mydomain.local/api/submit/ -X POST -H "Content-type:application/json" -d '{"install-type":"cloud-init","user-data":"my cloud-init userdata","meta-data":"my cloud-init metadata"}'
{
  "created_at": "Wed Feb 19 01:03:34 2014",
  "id": "530402e6844de405b7d48343",
  "installtype": "cloud-init",
  "ipv4_url": "http://mchm.mydomain.local/api/530402e6844de405b7d48343/",
  "phonehome_status": false,
  "status": "ok",
  "ttl": 3600,
  "zeroconf_url": "http://169.254.169.254/api/530402e6844de405b7d48343/"
}

# create new kickstart file
curl http://mchm.mydomain.local/api/submit/ -X POST -H "Content-type:application/json" -d '{"install-type":"kickstart","ks-data":"my kickstart file"}'
{
  "created_at": "Wed Feb 19 00:43:18 2014",
  "id": "5303fe26844de4049723a56e",
  "installtype": "kickstart",
  "ipv4_url": "http://mchm.mydomain.local/api/5303fe26844de4049723a56e/",
  "phonehome_status": false,
  "status": "ok",
  "ttl": 3600,
  "zeroconf_url": "http://169.254.169.254/api/5303fe26844de4049723a56e/"
}
```
#####To update existing documents
`POST` with parameter `id` using the id that was returned to you on document creation. This is useful if you need to know the retrieval URL so you can put it into your kickstart or cloud-init phonehome module. Post once, get the response, then post again.

```bash
#update cloud-init file
curl http://mchm.mydomain.local/api/submit/ -X POST -H "Content-type:application/json" -d '{"id":"530402e6844de405b7d48343","user-data":"my updated cloud-init userdata","meta-data":"my updated cloud-init metadata"}'
{
  "created_at": "Wed Feb 19 01:03:34 2014",
  "id": "530402e6844de405b7d48343",
  "installtype": "cloud-init",
  "ipv4_url": "http://mchm.mydomain.local/api/530402e6844de405b7d48343/",
  "phonehome_status": false,
  "status": "updated",
  "ttl": 3600,
  "zeroconf_url": "http://169.254.169.254/api/530402e6844de405b7d48343/"
}

#update kickstart file
curl http://mchm.mydomain.local/api/submit/ -X POST -H "Content-type:application/json" -d '{"id":"5303fe26844de4049723a56e","ks-data":"my updated kickstart info"}'
{
  "created_at": "Wed Feb 19 00:43:18 2014",
  "id": "5303fe26844de4049723a56e",
  "installtype": "kickstart",
  "ipv4_url": "http://mchm.mydomain.local/api/5303fe26844de4049723a56e/",
  "phonehome_status": false,
  "status": "updated",
  "ttl": 3600,
  "zeroconf_url": "http://169.254.169.254/api/5303fe26844de4049723a56e/"
}
```
###/api/\<id>/
`GET` previously posted data. MCHM will show the right things for cloud-init and kickstart. See "base" in the templates folder for the cloud-init data source page.

```bash
curl http://mchm.mydomain.local/api/530402e6844de405b7d48343/
curl http://mchm.mydomain.local/api/530402e6844de405b7d48343/user-data
curl http://mchm.mydomain.local/api/530402e6844de405b7d48343/meta-data
```
###/api/phonehome/\<id>/
`GET` /api/phonehome/ to poll for VM status.

`POST` to /api/phonehome/ from VM's so you can tell when they are booted. Was made for the cloud-init phonehome module, but you can curl -XPOST from a kickstart `%post%` section just as well. Any post to a valid id will change `phonehome_status` to true.

```bash
curl -XPOST http://mchm.mydomain.local/api/phonehome/5303fe26844de4049723a56e/ -d '{"msg":"kickstarted"}'

{
  "phonehome_data": {}, 
  "phonehome_status": true, 
  "phonehome_time": "Wed, 19 Feb 2014 01:25:00 GMT"
}
```
## Contributors
Just submit a pull request. If you see something which sucks please fix it.

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