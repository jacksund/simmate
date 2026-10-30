# Blender

--------------------------------------------------------------------------------

## About

[Blender](https://www.blender.org/) is a free and open-source 3D modeling program. Simmate's `blender` app uses it to create 3D models of crystal structures (`visualization.blender.structure`).

--------------------------------------------------------------------------------

## Installation

1. Add `blender` to the list of installed Simmate apps with:
``` bash
simmate config add blender
```

2. Install Blender from [their download page](https://www.blender.org/download/). On Linux, make sure the `blender` command is in your path. On Windows, Simmate looks in the default install folder (`C:\Program Files\Blender Foundation\`). Otherwise, set the full path to the Blender command in `~/simmate/blender.yaml`:
``` yaml
COMMAND: /path/to/blender
```

3. Ensure everything is configured correctly:
``` shell
simmate config test blender
```

--------------------------------------------------------------------------------
