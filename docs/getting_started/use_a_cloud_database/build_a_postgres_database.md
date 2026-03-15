
-------------------------------------------------------------------------------

# Building a Postgres Database

Simmate employs the Django ORM for database management, meaning any database [supported by Django](https://docs.djangoproject.com/en/5.1/ref/databases/) can be used.

This encompasses PostgreSQL, MariaDB, MySQL, Oracle, SQLite, and others via third-party providers. Comprehensive documentation for Django databases is available [here](https://docs.djangoproject.com/en/5.1/ref/databases/). 

However, **we strongly recommend using Postgres**, which we discuss in the following section.

!!! warning
    Our team only uses SQLite (as the default for beginners) and PostgreSQL (for production). While you're free to use other backends, we have not tested them and may not be able to assist with troubleshooting.

-------------------------------------------------------------------------------

## Deployment Options

Postgres is free and open-source, so you can set it up on your own computer or a cloud server. 

While you can [manually build a Postgres server](https://www.postgresql.org/docs/current/tutorial.html), we strongly recommend one of the two options below. Managed cloud services are easier for long-term projects, while Docker is perfect for local testing and development.

### Option A: DigitalOcean (Cloud)

Our team uses DigitalOcean, where a basic database server (~$15/month) is sufficient for most Simmate projects. You'll only need a larger plan if you're running hundreds of thousands of calculations or storing very large datasets.

#### 1. Account Creation

Start by creating an account on DigitalOcean using [this link](https://m.do.co/c/8aeef2ea807c) (our referral). This link should provide you a $200 credit for 60 days, which is more than enough to test things for free.

[![DigitalOcean Referral Badge](https://web-platforms.sfo2.cdn.digitaloceanspaces.com/WWW/Badge%203.svg)](https://www.digitalocean.com/?refcode=8aeef2ea807c&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge)

#### 2. Cloud Database Creation

1. On the DigitalOcean dashboard, click the green "Create" button in the top right and select **Databases**.
2. Select the latest version of PostgreSQL.
3. Choose a plan (the $15/month basic plan is a good starting point).
4. Select a data center region close to your primary compute resource (e.g., if your supercomputer is in the US East, choose NYC).
5. Click **Create Database Cluster**.

### Option B: Docker (Local)

If you want to test Postgres locally for free before moving to the cloud, Docker is the best way to do so. This requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) to be installed and running on your computer.

#### 1. Local Database Creation

To start a Postgres server locally, run the following command in your terminal:

``` bash
docker run \
    --name simmate-postgres \
    -e POSTGRES_PASSWORD=mysecretpassword \
    -v ~/simmate/postgres_data:/var/lib/postgresql/data \
    -p 5432:5432 \
    -d postgres
```

#### 2. Understanding the Docker Command

For beginners, here is a breakdown of what each part of the command does:

*   `docker run`: Tells Docker to start a new container.
*   `--name simmate-postgres`: Gives your container a friendly name so you can find it later.
*   `-e POSTGRES_PASSWORD=mysecretpassword`: Sets an environment variable (`-e`) for the database password. **You should change this to something more secure.**
*   `-v ~/simmate/postgres_data:/var/lib/postgresql/data`: This "mounts a volume" (`-v`). It maps a folder on your computer (`~/simmate/postgres_data`) to the folder where Postgres stores data inside the container. This ensures your database results are saved to your actual hard drive even if the container is stopped or deleted.
*   `-p 5432:5432`: Maps the container's port to your computer's port (`-p`). 5432 is the default port for Postgres.
*   `-d postgres`: Tells Docker to run the container in the background ("detached" mode) using the official `postgres` image.

-------------------------------------------------------------------------------

## Next Steps

Now that you have a Postgres instance running, you can connect Simmate to it in the next step.

[Connect to Postgres :material-arrow-right:](connect_to_postgres.md)
