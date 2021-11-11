from __future__ import with_statement
from __future__ import absolute_import
import argparse
import os
import re

from subprocess import check_output
from io import open

_author_ = u"etikhonov"


def submitJob_remote(workingDir, index, commandExecutable):
    u"""
    This routine is to submit job to remote cluster

    One needs to do a little edit based on your own case.

    Step 1: to prepare the job script which is required by your supercomputer
    Step 2: to submit the job with the command like qsub, bsub, llsubmit, .etc.
    Step 3: to get the jobID from the screen message

    :param workingDir: working directory on remote machine
    :param index: index of the structure.
    :param commandExecutable: command executable for current step of optimization
    :return:
    """

    # Step 1
    # Specify the PATH to put your calculation folder
    Home = u"/home/etikhonov"  # 'pwd' of your home directory of your remote machine
    Address = u"rurik"  # your target server: ssh alias or username@address
    Path = Home + u"/" + workingDir + u"/CalcFold" + unicode(index)  # Just keep it
    run_content = u""
    run_content += u"#!/bin/sh\n"
    run_content += u"#SBATCH -o out\n"
    run_content += u"#SBATCH -p cpu\n"
    run_content += u"#SBATCH -J USPEX-" + unicode(index) + u"\n"
    run_content += u"#SBATCH -t 06:00:00\n"
    run_content += u"#SBATCH -N 1\n"
    run_content += u"#SBATCH -n 8\n"
    run_content += u"cd " + Path + u"\n"
    run_content += commandExecutable + u"\n"

    with open(u"myrun", u"w") as fp:
        fp.write(run_content)

    # Create the remote directory
    # Please change the ssh/scp command if necessary.
    try:
        os.system(u"ssh -i ~/.ssh/id_rsa " + Address + u" mkdir -p " + Path)
    except:
        pass

    # Copy calculation files
    # add private key -i ~/.ssh/id_rsa if necessary
    os.system(u"scp POSCAR   " + Address + u":" + Path)
    os.system(u"scp INCAR    " + Address + u":" + Path)
    os.system(u"scp POTCAR   " + Address + u":" + Path)
    os.system(u"scp KPOINTS  " + Address + u":" + Path)
    os.system(u"scp myrun " + Address + u":" + Path)

    # Step 2
    # Run command
    output = unicode(
        check_output(
            u"ssh -i ~/.ssh/id_rsa " + Address + u" qsub " + Path + u"/myrun",
            shell=True,
        )
    )

    # Step 3
    # Here we parse job ID from the output of previous command
    jobNumber = int(re.findall(ur"\d+", output)[0])
    return jobNumber


if __name__ == u"__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(u"-i", dest=u"index", type=int)
    parser.add_argument(u"-c", dest=u"commnadExecutable", type=unicode)
    parser.add_argument(u"-f", dest=u"workingDir", type=unicode)
    args = parser.parse_args()

    jobNumber = submitJob_remote(
        workingDir=args.workingDir,
        index=args.index,
        commnadExecutable=args.commnadExecutable,
    )
    print("<CALLRESULT>")
    print(int(jobNumber))
