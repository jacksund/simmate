from __future__ import absolute_import
import argparse
import glob
import os

from subprocess import check_output

_author_ = u"etikhonov"


def checkStatus_local(jobID):
    u"""
    This function is to check if the submitted job is done or not
    One needs to do a little edit based on your own case.
    1   : whichCluster (0: no-job-script, 1: local submission, 2: remote submission)
    Step1: the command to check job by ID.
    Step2: to find the keywords from screen message to determine if the job is done
    Below is just a sample:
    -------------------------------------------------------------------------------
    Job id                    Name             User            Time Use S Queue
    ------------------------- ---------------- --------------- -------- - -----
    2455453.nano              USPEX            qzhu            02:28:42 R cfn_gen04
    -------------------------------------------------------------------------------
    If the job is still running, it will show as above.

    If there is no key words like 'R/Q Cfn_gen04', it indicates the job is done.
    :param jobID:
    :return: doneOr
    """

    # Step 1
    output = unicode(check_output(u"qstat {}".format(jobID), shell=True))
    # Step 2
    doneOr = True
    if u" R " in output or u" Q " in output:
        doneOr = False
    if doneOr:
        for file in glob.glob(u"USPEX*"):
            os.remove(file)  # to remove the log file
    return doneOr


if __name__ == u"__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(u"-j", dest=u"jobID", type=int)
    args = parser.parse_args()

    isDone = checkStatus_local(jobID=args.jobID)
    print("<CALLRESULT>")
    print(int(isDone))
