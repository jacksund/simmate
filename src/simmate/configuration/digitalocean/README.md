
# Directions on setting up our DigitalOcean servers for Django

To start, make an account on DigitalOcean using [this link](https://m.do.co/c/8aeef2ea807c) (which uses our refferal).

## Stage 1: Setting up our PostgreSQL Database

### creating the database server
1. On our DigitalOcean dashboard, click the green "Create" button in the top right and then select "Database". It should bring you to [this page](https://cloud.digitalocean.com/databases/new).
2. For "database engine", select the newest version of PostgreSQL (currently 13)
3. The remainder of the page's options can be left at their default values.
4. Select **Create a Database Cluster** when you're ready.

### connecting to the database
1. On your new database's page, you'll see a "Getting Started" dialog -- let's go through it!
2. For "Restrict inbound connections", this is completely optional and beginneers should skip this for now. We skip this because if you know you'll be running calculations on some supercomputer/cluster, then you'll need to add all of the associated IP addresses in order for connections to work properly. That's a lot of IP addresses to grab and configure properly -- so we leave this to advanced users.
3. "Connection details" is what we need to feed to django! Let's copy this information. As an example, here is what the details look like on DigitalOcean:
```
username = doadmin
password = s63keewaux8w8irf
host = db-postgresql-nyc3-49797-do-user-8843535-0.b.db.ondigitalocean.com
port = 25060
database = defaultdb
sslmode = require
```
4. We need to pass this information to Simmate (which connects using Django). So in our settings.py file, we want to set this as our default database. We do this with...
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "defaultdb",
        "USER": "doadmin",
        "PASSWORD": "asdf234jkn2kbjsd8",
        "HOST": "db-postgresql-nyc3-49797-do-user-234334-0.b.db.ondigitalocean.com",
        "PORT": "25060",
        'OPTIONS': {'sslmode': 'require'},
    }
}
```

### making a separate the database for testing (on the same server)
*Note that that we are just using the "defaultdb" database above! Within a PostgreSQL server, we can actually have multiple databases set up. This "defaultdb" one can never be deleted or reset, so we typically like to make a separate one.*
1. Select the "Users&Databases" tab.
2. Create a new database using the "Add new database" button and name this "simmate-database".
3. In your connection settings (from the section above), switch the NAME from defaultdb to simmate-database

### creating a connection pool
*When we have a bunch of calculations running at once, we need to make sure our database can handle all of these connections. Therefore we make a connection pool which allows for thousands of connections! This "pool" works like a waitlist where the database handles each connection request in order.*
1. Select the "Connection Pools" tab and then "Create a Connection Pool"
2. Name your pool "simmate-database-pool" and select "simmate-database" for the database
3. Select "Transaction" for our mode (the default) and set our pool size to **11**
4. Create the pool when you're ready!
5. In your connection settings (from the section above), switch the NAME to simmate-database-pool

### making all of our database tables
*Now that we set up and connected to our database, we can now make our database tables and start filling them with data! We let Simmate and Django do the heavy lifting here.*
1. In your terminal, make sure you have you Simmate enviornment activated
2. Run the following command: simmate database initial_setup
3. You're now ready to start using Simmate with your new database!


## Stage 2: Setting up our Django Website Server

These are the tutorials that I'm following along with:
1. [Overview that links to other tutorials](https://docs.digitalocean.com/products/app-platform/languages-frameworks/django/)
2. [Step-by-step guide along with how to configure settings.py](https://www.digitalocean.com/community/tutorials/how-to-deploy-django-to-app-platform)
3. [Example github repo to practice with](https://github.com/digitalocean/sample-django)

### configuring our settings, setup, and manage python files
(TODO)

### uploading our project to github
(TODO --> this will link to another README)

### setting up our website server
1. On our DigitalOcean dashboard, click the green "Create" button in the top right and then select "Apps". It should bring you to [this page](https://cloud.digitalocean.com/apps/new).
2. Select Github (and give github access if this is your first time)
3. For your "Source", we want to select our project. For me, this is "jacksund/simmate". Leave everything else at its default. 
4. When you go to the next page, you should see that Python was detected. We will now update some of these settings
5. Edit "Enviornment Variables" to include the following. Also note that we are connecting to our database pool and that your secret key should be [randomly generated](https://passwordsgenerator.net/) and encrypted!:
```
DJANGO_ALLOWED_HOSTS=${APP_DOMAIN}
DATABASE_URL=${db-postgresql-nyc3-09114.DATABASE_URL}
DEBUG=False
DJANGO_SECRET_KEY=randomly-generated-passord-12345
DEVELOPMENT_MODE=False
```
**consider switching to setting all database variables directly:
https://docs.digitalocean.com/products/app-platform/how-to/use-environment-variables/

6. Change our "Run Command" to...
```
gunicorn --worker-tmp-dir /dev/shm simmate.website.core.wsgi
```
7. Use the button at the bottom of this page to connect to our PostgreSQL database set-up above
8. We can still with the defaults for the rest of the pages! Create your server when you're ready!


### creating our static file server (CDN)
Everything for our website should work except for the serving of static files. This is because DigitalOcean wants us to serve these separately. This isn't a big deal because the extra server is free for us!
1. On our current app, go to "Settings" and then select "+Add Component" button on the top right. We want to add a "Static Site"
2. Select the same github repo as before and make sure python is detected
3. On this page, change "HTTP Request Routes" to **/static** and  the "Output Directory" to **/src/simmate/website/static**
4. That's it! Start the server when you're ready!


## setting up our website domain name (simmate.org)

We use google domains as I found it had the easiest setup and cheapest prices.
For connecting this to DigitalOcean, I follow these guides:
- https://docs.digitalocean.com/products/app-platform/how-to/manage-domains/
- https://www.digitalocean.com/community/tutorials/how-to-point-to-digitalocean-nameservers-from-common-domain-registrars
- https://docs.digitalocean.com/products/networking/dns/how-to/manage-records/

1. Purchase your website (domain) name on https://domains.google.com/registrar/
2. Select the domain you just purchased and now go to it "DNS" tab. For example, ours brings us to https://domains.google.com/registrar/simmate.org/DNS
3. Switch to the "Custom name servers" tab and add the following three servers:
- ns1.digitalocean.com
- ns2.digitalocean.com
- ns3.digitalocean.com
4. Save these and be sure to select "Switch to these settings" at the top to enable them
5. Jump back to your DigitalOcean dashboard and go to the [Networking tab](https://cloud.digitalocean.com/networking/domains)
6. The first page here is the Domain view where you should now add your new domain name
7. Now switch back to our DigitalOcean App (from above) and go to settings
8. Under "Domains", we want to edit and add 

