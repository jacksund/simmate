# Simmate Website Module

The `simmate.website` module hosts everything for the website interface and API. Unlike most major projects, Simmate makes our website's source-code openly available to everyone! This means that you can host your own Simmate website on your own computer or even in production for your lab to privately use.

------------------------------------------------------------

## Local Server Setup

To set up Simmate on your local computer, execute the following command:

=== "command line"
    ``` bash
    # Initialize your database if not done already
    simmate database reset

    # Run the website locally
    simmate run-server
    ```

While this command is running, open your preferred browser (Chrome, Firefox, etc.) and navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/). This local version of our website at `simmate.org` operates on your desktop using your personal database.

------------------------------------------------------------

## Production Server Setup

To set up a production-ready server for your team, you have three options:

1. Collaborate with the Simmate team and join our server
2. Request our team to manage a server for you
3. Set up and manage your own server

For options 1 and 2, contact us at `simmate.team@gmail.com`.

For option 3, follow [our guide for setting up a server on DigitalOcean](https://github.com/jacksund/simmate/tree/main/.do). Ensure you've completed the base Simmate tutorials, particularly the ones on [setting up a cloud database](/getting_started/use_a_cloud_database/quick_start/) and [setting up computational resources](/getting_started/add_computational_resources/quick_start/).

------------------------------------------------------------

## Third-Party Sign-Ins

Simmate supports sign-ins via third-party accounts such as Google and Github, thanks to the [`django-allauth`](https://github.com/pennersr/django-allauth) package.

By default, servers won't display these sign-in buttons. If you wish to enable third-party account logins, you'll need to configure this manually. Although `django-allauth` supports many account types (see their [full list](https://django-allauth.readthedocs.io/en/latest/providers.html)), Simmate currently only supports Github and Google. Guides for setting these up are provided below.

### Github OAuth

1. Create a new OAuth application [here](https://github.com/settings/applications/new) using the following information (replace `http://127.0.0.1:8000` with your cloud server link if applicable):

```
application name = My New Simmate Server (edit as desired)
homepage url = http://127.0.0.1:8000
authorization callback url = http://127.0.0.1:8000/accounts/github/login/callback/
```

2. On the next page, select "Generate a new client secret" and copy this value.

3. Set the environment variables on your local computer or production-ready server:
```
GITHUB_SECRET = examplekey1234 (value from step 2)
GITHUB_CLIENT_ID = exampleid1234 (value listed on Github as "Client ID")
```

### Google OAuth

1. Follow the django-allauth steps [here](https://django-allauth.readthedocs.io/en/latest/providers.html#google) to configure the Google API application.
2. Set the environment variables on your local computer or production-ready server:
```
GOOGLE_SECRET = examplekey1234
GOOGLE_CLIENT_ID = exampleid1234
```

------------------------------------------------------------

## CSS and JS Assets

Simmate doesn't distribute most source CSS and JavaScript files due to licensing restrictions on our third-party vendor assets. We use the [Hyper theme](https://themes.getbootstrap.com/product/hyper-responsive-admin-dashboard-template/) from the [CoderThemes team](https://coderthemes.com/). You can contribute to Simmate's website using their [Modern Dashboard template](https://coderthemes.com/hyper/modern/index.html) without needing to access any of the assets. Our templates load assets from a Simmate CDN:

``` html
<!-- Normal asset loading with source code distribution -->
<link href="assets/css/vendor/fullcalendar.min.css" rel="stylesheet" type="text/css" />

<!-- Simmate's CDN-based asset loading -->
<link href="https://archives.simmate.org/assets/fullcalendar.min.css" rel="stylesheet" type="text/css" />
```

If you need to modify the CSS or JS, please contact our team to discuss the best approach.

------------------------------------------------------------
