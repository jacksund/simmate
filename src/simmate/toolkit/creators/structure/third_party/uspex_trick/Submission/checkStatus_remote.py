from __future__ import absolute_import
import argparse
import os

from subprocess import check_output


def checkStatus_remote(jobID, workingDir, index):
    u"""
    This routine is to check if the submitted job is done or not
    One needs to do a little edit based on your own case.
    Step1: Specify the PATH to put your calculation folder
    Step2: Check JobID, the exact command to check job by jobID
    :param jobID:
    :param index:
    :param workingDir:
    :return:
    """
    # Step 1
    Home = u"/home/etikhonov"  # 'pwd' of your home directory of your remote machine
    Address = u"rurik"  # Your target supercomputer: username@address or ssh alias
    # example of address: user@somedomain.edu -p 2222
    Path = Home + u"/" + workingDir + u"/CalcFold" + unicode(index)  # just keep it

    # Step 2
    output = unicode(
        check_output(u"ssh " + Address + u" qstat " + unicode(jobID), shell=True)
    )
    # If you using full adress without ssh alias, you must provide valid ssh private key like there:
    # output = str(check_output('ssh -i ~/.ssh/id_rsa ' + Address + ' /usr/bin/qstat ' + str(jobID), shell=True))

    if not u" R " in output or not u" Q " in output:
        doneOr = True
        # [nothing, nothing] = unix(['scp -i ~/.ssh/id_rsa ' Address ':' Path '/OUTCAR ./']) %OUTCAR is not necessary by default
        os.system(
            u"scp " + Address + u":" + Path + u"/OSZICAR ./"
        )  # For reading enthalpy/energy
        os.system(
            u"scp " + Address + u":" + Path + u"/CONTCAR ./"
        )  # For reading structural info
        # Edit ssh command as above!
    else:
        doneOr = False
    return doneOr


if __name__ == u"__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(u"-j", dest=u"jobID", type=int)
    parser.add_argument(u"-i", dest=u"index", type=int)
    parser.add_argument(u"-f", dest=u"workingDir", type=unicode)
    args = parser.parse_args()

    isDone = checkStatus_remote(
        jobID=args.jobID, workingDir=args.workingDir, index=args.index
    )
    print("<CALLRESULT>")
    print(int(isDone))
