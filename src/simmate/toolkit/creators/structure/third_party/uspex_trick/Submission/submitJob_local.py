from __future__ import with_statement
from __future__ import absolute_import
from subprocess import check_output
import re
import sys
from io import open


def submitJob_local(index, commnadExecutable):
    return 12345  #


if __name__ == u"__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(u"-i", dest=u"index", type=int)
    parser.add_argument(u"-c", dest=u"commnadExecutable", type=unicode)
    args = parser.parse_args()

    jobNumber = submitJob_local(
        index=args.index, commnadExecutable=args.commnadExecutable
    )
    print("<CALLRESULT>")
    print(int(jobNumber))
