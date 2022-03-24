
<!-- 
This link launches a new DigitalOcean server using the app template. For more
info see...
    https://docs.digitalocean.com/products/app-platform/how-to/add-deploy-do-button/
-->
[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/jacksund/simmate/tree/update-web&refcode=8aeef2ea807c)

# Setting up our DigitalOcean database and servers

> :warning: You can avoid this tutorial if you choose to collaborate with Simmate! Make sure you have read through [our database tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/06_Use_a_cloud_database.md) before deciding to take on the work of managing your database.

In this tutorial, you will learn how to install Simmate with Anaconda. Beginners will also be introduced to the command-line.

1. [Setting up an account](#setting-up-an-account)
2. [Stage 1: Setting up our PostgreSQL Database](#stage-1-setting-up-our-postgresql-database)
    - [creating the cloud database](#creating-the-database-server)
    - [connecting to the database](#connecting-to-the-database)
    - [making a separate the database for testing (on the same server)](#making-a-separate-the-database-for-testing-on-the-same-server)
3. [Stage 2: Setting up a Django Website Server](#stage-2-setting-up-a-django-website-server)


<br/><br/>


## Setting up an account

To start, make an account on DigitalOcean using [this link](https://m.do.co/c/8aeef2ea807c) (which uses our refferal). We recommend using your Github account to sign in. This referral link does two things:

1. DigitialOcean gives you $100 credit for servers (for 60 days)
2. DigitialOcean gives the Simmate team $10 credit, which will help fund our servers

If you have issues with this, please make sure that DigitalOcean is still actually offering this deal [here](https://try.digitalocean.com/freetrialoffer/). Simmate is not affiliated with DigitalOcean, so please contact them with issues!

<br/>

## Stage 1: Setting up our PostgreSQL Database

First, we need to set up our Cloud database, tell Simmate how to connect to it, and build our tables.

### creating the cloud database

1. On our DigitalOcean dashboard, click the green "Create" button in the top right and then select "Database". It should bring you to [this page](https://cloud.digitalocean.com/databases/new).
2. For "database engine", select the newest version of PostgreSQL (currently 14)
3. The remainder of the page's options can be left at their default values.
4. Select **Create a Database Cluster** when you're ready.

Note, this is the database **cluster**, which can host multiple databases on it (each with all their own tables).


### connecting to the database

Before we set up our database on this cluster, we are are first going to try connecting the default database on it (named `defaultdb`).

1. On your new database's page, you'll see a "Getting Started" dialog -- select it!
2. For "Restrict inbound connections", this is completely optional and beginneers should skip this for now. We skip this because if you know you'll be running calculations on some supercomputer/cluster, then you'll need to add all of the associated IP addresses in order for connections to work properly. That's a lot of IP addresses to grab and configure properly -- so we leave this to advanced users.
3. "Connection details" is what we need to feed to django! Let's copy this information. As an example, here is what the details look like on DigitalOcean:
```
username = doadmin
password = asd87a9sd867fasd
host = db-postgresql-nyc3-49797-do-user-8843535-0.b.db.ondigitalocean.com
port = 25060
database = defaultdb
sslmode = require
```
4. We need to pass this information to Simmate (which connects using Django). To do this, add a file named `my_env-database.yaml` (using your conda env name) to your simmate config directory (`~/simmate`) with the following content -- be sure substute in your connection information and note that ENGINE tells Django we are using Postgres:
``` yaml
default:
  ENGINE: django.db.backends.postgresql_psycopg2
  HOST: db-postgresql-nyc3-49797-do-user-8843535-0.b.db.ondigitalocean.com
  NAME: defaultdb
  USER: doadmin
  PASSWORD: asd87a9sd867fasd
  PORT: 25060
  OPTIONS:
    sslmode: require
```
5. Make sure you can connect to this database on your local computer by running the following in Spyder:
``` python
from simmate.configuration.django.settings import DATABASES

print(DATABASES)  # this should give your connect info!
```


### making a separate the database for testing (on the same server)

Just like how we don't use the `(base)` environment in Anaconda, we don't want to use the default database `defaultdb` on our cluster. Here will make a new database -- one that we can delete if we'd  like to restart.

1. On DigitalOcean with your Database Cluster page, select the "Users&Databases" tab.
2. Create a new database using the "Add new database" button and name this `simmate-database-00`. We name it this way because you may want to make new/separate databases and numbering is a quick way to keep track of these.
3. In your connection settings (from the section above), switch the NAME from defaultdb to `simmate-database-00`. You will change this in your `my_env-database.yaml` file.

### creating a connection pool

When we have a bunch of calculations running at once, we need to make sure our database can handle all of these connections. Therefore we make a connection pool which allows for thousands of connections! This "pool" works like a waitlist where the database handles each connection request in order.

1. Select the "Connection Pools" tab and then "Create a Connection Pool"
2. Name your pool `simmate-database-00-pool` and select `simmate-database-00` for the database
3. Select "Transaction" for our mode (the default) and set our pool size to **11** (or modify this value as you wish)
4. Create the pool when you're ready!
5. You'll have to update your `my_env-database.yaml` file to these connection settings. At this point your file will look similar to this (note, our NAME and PORT values have changed):
``` yaml
default:
  ENGINE: django.db.backends.postgresql_psycopg2
  HOST: db-postgresql-nyc3-49797-do-user-8843535-0.b.db.ondigitalocean.com
  NAME: simmate-database-00-pool
  USER: doadmin
  PASSWORD: asd87a9sd867fasd
  PORT: 25061
  OPTIONS:
    sslmode: require
```

### making all of our database tables

Now that we set up and connected to our database, we can now make our Simmate database tables and start filling them with data! We do this the same way we did without a cloud database:

1. In your terminal, make sure you have you Simmate enviornment activated
2. Run the following command: 
```
simmate database reset
```
3. You're now ready to start using Simmate with your new database!
4. If you want to share this database with others, you simply need to have them copy your config file: `my_env-database.yaml`. They won't need to run `simmate database reset` because you did it for them.

<br/>

## Stage 2: Setting up a Django Website Server

If you want to host your Simmate installation as website just for you team, you can use DigitalOcean to host a Django Website server.

This section follows the tutorials listed here. If you are struggling with our guide or want additional explanation, you can refer to these sources:
1. [Overview that links to other tutorials](https://docs.digitalocean.com/tutorials/app-deploy-django-app/)
2. [Step-by-step guide along with how to configure settings.py](https://www.digitalocean.com/community/tutorials/how-to-deploy-django-to-app-platform)
3. [Example github repo to practice with](https://github.com/digitalocean/sample-django)

### uploading our project to github
(TODO --> maybe link to another tutorial)

### setting up our website server

1. On our DigitalOcean dashboard, click the green "Create" button in the top right and then select "Apps". It should bring you to [this page](https://cloud.digitalocean.com/apps/new).
2. Select Github (and give github access if this is your first time)
3. For your "Source", we want to select our project. For me, this is "jacksund/simmate". Leave everything else at its default.
4. When you go to the next page, you should see that Python was detected. We will now update some of these settings in steps 5-8.
5. Edit "Enviornment Variables" to include the following. Also note that we are connecting to our database pool and that your secret key should be [randomly generated](https://passwordsgenerator.net/) and encrypted!:
```
DJANGO_ALLOWED_HOSTS=${APP_DOMAIN}
DEBUG=False
DJANGO_SECRET_KEY=randomly-generated-passord-12345
USE_LOCAL_DATABASE=False
PREFECT__CLOUD__API_KEY=your-prefect-api-key
```
> note to simmate devs: [consider switching to setting all database variables directly](https://docs.digitalocean.com/products/app-platform/how-to/use-environment-variables/)
> note for prefect: in the future, I may want to link API keys to profiles so that we can submit to proper clouds -- rather than assume all go through a single prefect account.

6. Change our "Build Command" to... (`pip install .` is ran automatically)
```
pip install gunicorn psycopg2; prefect backend cloud;
```

<!-- Currently, I'm trying to install blender but running into issues...
wget https://download.blender.org/release/Blender3.1/blender-3.1.0-linux-x64.tar.xz
tar -xf blender-3.1.0-linux-x64.tar.xz
rm blender-3.1.0-linux-x64.tar.xz
./blender --version  (DOES NOT WORK)
-->

7. Change our "Run Command" to...
```
gunicorn --worker-tmp-dir /dev/shm simmate.website.core.wsgi
```
8. Use the button at the bottom of this page to connect to our PostgreSQL database set-up above
9. We can stick with the defaults for the rest of the pages! Create your server when you're ready!


### creating our static file server (CDN)

> :warning: it looks like DigitalOcean is updating the way this is done, so [their guide] is no longer accurate. My guide below may also be outdated.

Everything for our website should work except for the static files. This is because Django doesn't serve static files when DEBUG=False. They want us to serve these separately as a static site (via a CDN). This isn't a big deal because the extra server is free for us on DigitalOcean.

1. On our current app, go to "Settings" and then select "+Add Component" button on the top right. We want to add a "Static Site"
2. Select the same github repo as before and make sure python is detected
3. On this page, change "HTTP Request Routes" to `/static` and  the "Output Directory" to `/src/simmate/website/static`
4. That's it! Start the server when you're ready!


## setting up our website domain name (simmate.org)

We use google domains as I found it had the easiest setup and cheapest prices.
For connecting this to DigitalOcean, I followed these guides: [1](https://docs.digitalocean.com/products/app-platform/how-to/manage-domains/), [2](https://www.digitalocean.com/community/tutorials/how-to-point-to-digitalocean-nameservers-from-common-domain-registrars), [3](https://docs.digitalocean.com/products/networking/dns/how-to/manage-records/). These can give extra details if the steps below aren't enough.

1. Purchase your website (domain) name on https://domains.google.com/registrar/
2. Select the domain you just purchased and now go to its "DNS" tab. For example, ours brings us to https://domains.google.com/registrar/simmate.org/DNS
3. Switch to the "Custom name servers" tab and add the following three servers:
    - ns1.digitalocean.com
    - ns2.digitalocean.com
    - ns3.digitalocean.com
4. Save these and be sure to select "Switch to these settings" at the top to enable them
5. Jump back to your DigitalOcean dashboard and go to the [Networking tab](https://cloud.digitalocean.com/networking/domains)
6. The first page here is the Domain view where you should now add your new domain name
7. Now switch back to our DigitalOcean App (from above) and go to settings
8. Under "Domains", we want to edit and then add `simmate.org` (or your chosen name). Let DigitalOcean manages the DNS.
