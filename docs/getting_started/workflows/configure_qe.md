# Setting Up Quantum Espresso

----------------------------------------------------------------------

## What is Quantum Espresso (QE)?

Quantum Espresso (QE) is a widely used software for running DFT calculations. 

There are also many other programs which do the same thing as QE, such as VASP, Abinit, and CASTEP. Simmate can be used alongside any of these programs, but (at the moment) Simmate only includes pre-built workflows for VASP and Quantum Espresso.

This tutorial will use QE because it is free & open-source.

----------------------------------------------------------------------

## 1. Install QE using Docker

!!! warning
    :warning: **IMPORTANT** :warning:

    Docker is used in order to help beginners that are using their local laptop or desktop. In practice, most researchers will have a university cluster with QE or some other DFT software installed for them. 
    
    **Beginners:** stick to your laptop & Docker for now.

    **Experienced Programmers:** you may ignore any Docker setup. Simply ensure the `pw.x` executable is available in your `PATH`. See the official QE installation guides if you need them ([link](https://www.quantum-espresso.org/)).

### i. Why Docker?

Most DFT programs can only be installed on Linux and are incompatible with Windows and Mac. And even on Linux, installing such software can be challenging for users. While QE is comparatively more manageable, it remains a significant hurdle for beginners.

To get around this, we will use Docker. Docker simplifies the process for users without coding experience by eliminating complex setup procedures. Similar to Anaconda's isolated "environments" for Python packages, Docker employs isolated "containers" with everything necessary for a package to run, including the operating system.

### ii. Install Docker-Desktop

Download install [Docker-Desktop](https://www.docker.com/products/docker-desktop/). You do not need to make an account.

This will install the `docker` command for you and let you monitor all running containers.

To confirm docker is working properly, run the command:
``` bash
docker run hello-world
```

Read through the output of this command, you will see somewhere this text:
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

Seeing an error? Here are the two most common causes: 

!!! troubeshooting
    If you see an error such as...
    ```
    docker: error during connect: This error may indicate that the docker daemon is not running. ...
    ```

    ... then this means you don't have Docker-Desktop open & running. Open the app (and leave it open) when running `docker` commands.

!!! troubeshooting
    If you see an error such as...
    
    ```
    docker: permission denied while trying to connect to the Docker daemon socket at unix: ...
    ```
    
    ...then you are likely a Linux user and don't have `sudo` permissions yet. To give `sudo` permissions to `docker`, read the official guides [here](https://docs.docker.com/engine/install/linux-postinstall/#configure-docker-to-start-on-boot-with-systemd). For example, on Ubuntu, you can get docker set up and running using:
    ```bash
    sudo snap install docker
    sudo groupadd docker
    sudo usermod -aG docker $USER
    # Then restart your computer
    ```

    If you are on a shared computer system & do not have `sudo` permissons (e.g. you are on a shared HPC cluster), then Docker likely isn't a good solution for you. Make sure you read the "Submit to a Cluster" section of this `Workflows` guide for more information.

### iii. Tell Simmate to use Docker

By default, Simmate assumes QE is installed on your computer. But here, we have QE installed within a Docker container, so QE commands such as `pw.x` are only accessible *inside* a docker container. We therefore need tell Simmate that we are using Docker for QE.

Run this command to tell Simmate to use Docker for QE-based workflows:
``` bash
simmate config update "quantum_espresso.docker.enable=True"
```

----------------------------------------------------------------------

## 2. Configure Psuedo Files

To run calculations with QE, we need psuedopotentials. Normally, you have to find, download, and configure these on your own. Simmate helps load these from the popular [SSSP library](https://www.materialscloud.org/discover/sssp/).

Run the following command to set up your files:
``` bash
simmate-qe setup sssp
```

!!! tip
    To see what this command did, take a look at `~/simmate` and you'll see the following update:
    ``` bash
    # Located at ~ (e.g. /home/johnsmith)
    simmate
    └── quantum_espresso
        └── potentials
            └── << all of your psuedo files! >>
    ```

----------------------------------------------------------------------

## 3. Test Your QE Configuration

Let's make sure we've done the following correctly:

1. Installed QE **-- or --** installed Docker + used `simmate config update`
2. Used `simmate-qe setup sssp` to download our potentials

Run this command to check everything:

``` bash
simmate config test quantum_espresso
```

If all the checks pass, you're ready to run workflows!

----------------------------------------------------------------------