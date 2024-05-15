# An Introduction to Python & Spyder

----------------------------------------------------------------------

## Introduction to Python

If you're new to coding and Python, you will still be able to read along and follow this tutorial.

However, we *strongly* recommend dedicating 2-3 days to learn Python fundamentals once you complete the tutorial. Python fundamentals are beyond the scope of our guides, but resources such as [Codecademy's Python lessons](https://www.codecademy.com/learn/learn-python-3) are excellent for beginners.

----------------------------------------------------------------------

## Where to write Python code

Remember from the Installation tutorial: Anaconda provided several programs on their home screen, including Jupyter Notebook, Spyder, and others. These programs allow you to write your own Python code. Just as there are various platforms for writing papers, like Microsoft Word, Google Docs, and LibreOffice, these programs offer different ways to write Python. 

Our team prefers Spyder, and we highly recommend it to our users. We will use Spyder in this tutorial.

----------------------------------------------------------------------

## Launching Spyder

!!! tip 
    If you're already comfortable with Python or have completed the Codecademy python course, you can quickly familiarize yourself with Spyder by watching their intro videos. [There are 3 videos, each under 4 minutes long](https://docs.spyder-ide.org/current/videos/first-steps-with-spyder.html).

If you followed the installation tutorial, Spyder should already be installed and ready to use. 

To launch it, search for Spyder in your computer's apps (use the search bar at the bottom-left of your screen on Windows 10) and select `Spyder (my_env)`. 

Spyder will be empty when you first launch it. Here's a glimpse of what Spyder looks like when it's in use:

<!-- This is an image of the Spyder IDE -->
<p align="center" style="margin-bottom:40px;">
<img src="https://raw.githubusercontent.com/spyder-ide/spyder/5.x/img_src/screenshot.png"  height=440 style="max-height: 440px;">
</p>

----------------------------------------------------------------------

## Running Python code

For this tutorial, we'll only be using the Python console (located at the bottom-right of the screen). The console behaves just like our command-line, except it runs Python code instead.

To kick things off, paste the following in the console & hit enter to run:
``` python
x = 123 + 321

print("Using Python, we found the value of x:")
print(x)
```

In the output, you should see our message and the answer `444`.

----------------------------------------------------------------------