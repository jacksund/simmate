!!! I should consider other 'distance' operations
from scipy.spatial.distance --- https://docs.scipy.org/doc/scipy-0.14.0/reference/spatial.distance.html

Also note that the scipy versions are slower because they perform checks before doing the calculation to avoid this, look at the source code for each scipy call and you'll see what the numpy code should be.

Here's an example showing how scipy's call for scipy.spatial.distance.euclidean (which calls scipy.linalg.norm) is much slower than numpy:
```python
import numpy
a = numpy.random.random(size=(1000, 2000))

from scipy.linalg import norm as norm_scipy
from numpy.linalg import norm as norm_numpy
%timeit norm_scipy(a)
%timeit norm_numpy(a)
```
