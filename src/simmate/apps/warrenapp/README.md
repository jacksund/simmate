<!-- This displays entry text -->
<h1><p align="center">
Welcome to the Warren Lab's extension app for
</h1></p>
<!-- This displays the Simmate Logo -->
<p align="center" href=https://github.com/jacksund/simmate>
   <img src="https://github.com/jacksund/simmate/blob/main/src/simmate/website/static_files/images/simmate-logo-dark.svg?raw=true" width="300" style="max-width: 700px;">
</p>

### Requirements
This extension is built off of [Simmate](https://github.com/jacksund/simmate). In order to use it you must have the base Simmate package installed. The current version is built on top of Simmate 0.13.2 and does not work with the most up-to-date version of Simmate. We are working to fix this in the next couple of weeks.

Tutorials are at: https://jacksund.github.io/simmate/getting_started/overview/

### How to Use
1. If you haven't already, you may need to register the warrenapp with simmate. Register the warrenapp with simmate by adding `- warrenapp.apps.SimmateWarrenConfig` to ~/Home/simmate/my_env-apps.yaml
2. Update your database to include custom tables from the warrenapp
``` shell
simmate database update
```
