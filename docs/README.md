# Documentation

This directory hosts the build script for Simmate's online API documentation. You can access the live docs [here](https://jacksund.github.io/simmate/simmate.html). If you would like to host our documentation locally for offline access, then you can run the following commands:

``` bash
# with your simmate conda env active 
# and the docs/ directory as your working dir
python make_docs.py
```

You can then open up the generated `docs/index.html` file to view the offline documentation.
