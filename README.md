# Ganomics server

## Python dependencies 
    
* channels
* django-crispy-forms
* channels_redis
* numpy
* django
* psycopg2-binary
* websocket-client
* click

## Other dependencies

* redis
* postgresql


## Do not forget

* Launch Postgresql server
* Launch Redis server


## Stack

* **LAN**: client -> router -> dnsmasq -> nginx -> daphne -> if websocket -> redis -> django asgi <br>
                                                         else -> django wsgi
                                                         
* **WAN**: client -> online.net DNS  -> getz-server -> nginx -> daphne -> if websocket -> redis -> django asgi
                                                         else -> django wsgi

# Local network config

## Correspondance access point - tablet range id
* 1: 0-16
* 2: 17-33
* 3: 34-50
* 4: 51-67
* 5: 68-85
* 6: 90-103

## login router

* SSID: NETGEAR54-5G
* pw: macaque40

## How it works

* Client asks the router for a domain name (money.getz.fr)

* Local dns is configured on the router interface (Advanced > Setup > internet configuration section)

* Router asks the local dns (dnsmasq), it returns the nginx ip

* The client communicates with daphne and django through nginx

## Dnsmasq config

Linux: 

    /etc/dnsmasq.conf

MacOS: 

    /usr/local/etc/dnsmasq.conf

Modify the variable named **address**: 

    address=/fr/192.168.1.204
    
The dns server catch all domain names ending with **fr** and returns 
the address of the nginx server on the local network (here **192.168.1.204**).

## Nginx config

We tell nginx to serve static files:

    location /static/ {
         autoindex on;
         alias /home/getz/Pycharm/MoneyServer/static/;
     }
     
To be able to do that nginx must have the proper permissions and access to the folder.
Then we can tell nginx to log as a certain user, or alternatively change the folder permissions.

All the other request are redirected to daphne:

    location / {
         proxy_pass http://localhost:8018 ;
         proxy_redirect off;
    }
   
All requests ending with **/ws/** are Websocket requests and need specific headers
to work correctly. So we add:
     
    location /ws/ {
         proxy_pass http://localhost:8018 ;
         proxy_http_version 1.1;
         proxy_set_header Upgrade $http_upgrade;
         proxy_set_header Connection "upgrade";
     }

The whole config file looks like: 

    user getz;
    worker_processes  1;

    #error_log  logs/error.log;
    #error_log  logs/error.log  notice;
    #error_log  logs/error.log  info;

    #pid        logs/nginx.pid;


    events {
        worker_connections  1024;
    }


    http {
        include       mime.types;
        default_type  application/octet-stream;

        #log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
    #                  '$status $body_bytes_sent "$http_referer" '
    #                  '"$http_user_agent" "$http_x_forwarded_for"';

        #access_log  logs/access.log  main;

        sendfile        on;
        #tcp_nopush     on;

        #keepalive_timeout  0;
        keepalive_timeout  65;

        #gzip  on;

        server {
            listen       80;
            server_name  localhost 127.0.0.1 money.getz.fr;

            #charset koi8-r;

            #access_log  logs/host.access.log  main;

            location /static/ {
                 autoindex on;
                 alias /home/getz/Pycharm/MoneyServer/static/;
             }
         
            location / {
                 proxy_pass http://localhost:8018 ;
                 proxy_redirect off;
                 #proxy_set_header Host $http_host;
                # proxy_set_header X-Real-IP $remote_addr;
                # proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
             }
         
            location /ws/ {
                 proxy_pass http://localhost:8018 ;
                 proxy_http_version 1.1;
                 proxy_set_header Upgrade $http_upgrade;
                 proxy_set_header Connection "upgrade";
            }
        }
    }

 
## Other details 

* access points are connected using rj-45 (not in the 'console' port)

* Local static IP Thinkpad basile: 192.168.1.204
* tuto dnsmasq: https://www.michaelpporter.com/2017/11/using-dnsmasq-for-local-development-on-macos/

