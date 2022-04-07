VASP Error Hanlders
--------------------

This module defines error handlers to help address issues during VASP workflow runs. This module is a fork and refactor of error handlers used by [Custodian](https://github.com/materialsproject/custodian). Specifically, this is a direct alternative to the [`custodian.vasp.handlers`](https://github.com/materialsproject/custodian/blob/master/custodian/vasp/handlers.py) module. One key difference is that we break up our error handlers into smaller handlers because this allows us to more-easily see the error/fix identified.
