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
* Launch Nginx


## Stack

* **LAN**: client -> router -> nginx -> daphne -> if websocket -> redis -> django asgi <br>
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
   
* Client asks for ip 192.168.1.204.
* The server has a fixed ip (192.168.1.204) attributed by the router.
* Nginx listens to every request to port 80
* The client communicates with daphne and django through nginx

## PostgreSQL (MacOs)
install postgresql

    brew install postgresql

run pgsql server

    pg_ctl -D /usr/local/var/postgres start

create user and db

    createuser dasein
    createdb MoneyServer --owner dasein

if you need to remove the db
    
    dropdb MoneyServer

## Nginx config

Modify the config file. Default location MacOS: '/usr/local/etc/nginx/nginx.conf'.
Default location Linux: '/etc/nginx/nginx.conf' 

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
     
On Macos the user must be followed by a group (e.g. staff).

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
                 alias <path_of_the_static_folder>;
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
* To attach a new device on the router (set a fixed ip) Advanced > setup > LAN setup
<!--* tuto dnsmasq: https://www.michaelpporter.com/2017/11/using-dnsmasq-for-local-development-on-macos/ -->


## Code structure
The consumers.py scripts contains a Consumer class, that is instantiated when running the server.
That's how the Consumer instance stores and maintains information about clients through time.
When request from client, 'received' is called from 'consumers.py' (websocket) and then views.py. 

All view functions have generic patterns. 

* Get user and room. Defined in 'client.py' from either 'room' or 'user' folder. 
  - room folder: all functions relative to change properties of room or sending information to all users;
  - user folder: all functions relative to a single user.

* Specific function. Defined in 'client.py' of either 'room' or 'user' folder.
  
...then generic stuff:

* 'get_progression'. Defined in 'room/client.py'. Return an integer between 0 and 100.

* 'state_verification'.  Defined in 'room/client.py'. Along with other args, take progression as an input. 
Change state if needed. return if client has to wait and state. Different states are:
    - welcome
    - survey
    - training 
    - game
    - end
    
* Communicate response to group (except 'training_choice') 

* Return response to Consumer instance 

* The Consumer instance gets the response and send it to the client

* Then the consumer call the on_receive method and do all the group operations (removing, adding) based on
the content of the response dictionary


## Tweaking / scaling

* channels_redis (in settings.py): 
    expiry: 4  # Time before a msg expires
    capacity: 200  # Message capacity
    
# How to run a Demo

## Server

Assuming that python3, posgresql, redis are installed:

* create user and db


    createuser dasein
    createdb MoneyServer --owner dasein
    
* Make migrations


    python3 manage.py makemigrations
    python3 manage.py migrate
    
* Launch redis

    
    bash launch_redis.sh

* Launch the server

        python3 manage.py runserver
        
* Go to http://127.0.0.1:8000/

* Create a room

* Go to settings and turn on 'trial'

## Unity


* Tablet pixel size: 1024 x 600

* Development: address is: ws://127.0.0.1:8000/ws/

* Production: address is: ws://192.168.1.204/ws/