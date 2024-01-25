VASP Error Handlers
--------------------

This module provides error handlers designed to resolve issues that may arise during VASP workflow executions. It is a refactored version of error handlers originally used by [Custodian](https://github.com/materialsproject/custodian), serving as a direct alternative to the [`custodian.vasp.handlers`](https://github.com/materialsproject/custodian/blob/master/custodian/vasp/handlers.py) module. A significant distinction is that our error handlers are divided into smaller units, enhancing visibility of the error and its corresponding solution.