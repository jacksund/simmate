This module hosts everything for SQL-type database access. Right now it's just the ORM, but I may make submodules of 'orm', 'api', and 'util' in the future.

It is likely to be a common task for users to convert data from SQL to CSV. To do this, we'd really take a django QuerySet --> convert it to a Pandas dataframe --> and then write the CSV file. There is a python package written for this (here)[https://github.com/chrisdev/django-pandas] but because it's really just one file that we'd use, it may be worth rewritting. It doesn't look like it handles relationship columns the way I'd like, as storing the related primary key is sufficient.

