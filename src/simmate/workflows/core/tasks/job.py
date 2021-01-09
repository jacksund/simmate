# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from subprocess import Popen


class Job(ABC):
    """
    Abstract base class defining a Job that should be used with SupervisedJobTask
    if you want error handling. Only use this if you have a bunch of Handlers
    to perform error correction on a running Job. 99% of the time you are doing
    this when you call some executable that creates a bunch of output files.
    For example, we may want to read VASP output files as the job runs and
    also after it finishes to look for errors and retry the calculation based
    off of those errors with updated settings.
    """

    @abstractmethod
    def setup(self):
        """
        This method is run before the start of a job. Allows for some
        pre-processing. This includes creating a directory, writing input files
        or any other function ran before calling the executable.
        """
        pass

    @abstractmethod
    def execute(self):
        """
        This method performs the actual work for the job. If parallel error
        checking (monitoring) is desired, this must return a Popen process.
        Otherwise, this code should wait until the calculation finishes.
        The return of conncurrent.futures is not yet supported.
        This is name execute instead of run to help stay consistent with
        Prefect Task formats used elsewhere.
        """
        # TODO I should make the default here a subprocess.Popen because its
        # used in 99% of the cases
        pass

    @abstractmethod
    def postprocess(self):
        """
        This method is called at the end of a job, *after* error detection.
        This allows post-processing, such as cleanup, analysis of results,
        etc. This should return the result of the entire job, such as a
        the final structure or final energy calculated.
        """
        pass

    def run(self):
        """
        Runs the entire job in the current working directory without any error
        handling. If you want robust error handling, then you should instead
        run this through the SupervisedJobTask class. This method should
        very rarely be used!
        """
        self.setup()
        future = self.run()
        if isinstance(future, Popen):
            future.wait()
        result = self.postprocess()
        return result

    @property
    def name(self):
        """
        A nice string name for the job. By default it just returns the name
        of this class.
        """
        return self.__class__.__name__
