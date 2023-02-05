#

import os
import sys

# from https://stackoverflow.com/questions/11130156/suppress-stdout-stderr-print-from-python-functions

# This one fails in Python 3.7.4 on Windows due to a bug in os.dup2
# It also fails in Python 3.7.5 on Windows as it fails to close the file handles in __exit__ opened in __init__


# Define a context manager to suppress stdout and stderr.
class suppress_stdout_stderr():
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).

    '''
    def __init__(self) -> None:
        # Open a pair of null files
        try:
            self.null_fds = [os.open(os.devnull,os.O_RDWR) for _ in range(2)]
            # Save the actual stdout (1) and stderr (2) file descriptors.
            try:
                self.save_fds = [os.dup(1), os.dup(2)] # fails on Windows 7 under Python 3.7.4 with "OSError: [WinError 87] The parameter is incorrect"
            except Exception: # pylint: disable=broad-except
                try:
                    self.save_fds = [os.dup(sys.stdout.fileno()), os.dup(sys.stderr.fileno())]
                except Exception: # pylint: disable=broad-except
                    self.save_fds = []
        except Exception: # pylint: disable=broad-except
            self.null_fds = []
            self.save_fds = []

    def __enter__(self) -> None:
        # Assign the null pointers to stdout and stderr.
        if self.save_fds:
            os.dup2(self.null_fds[0],1)
            os.dup2(self.null_fds[1],2)

    def __exit__(self, *_) -> None:
        # Re-assign the real stdout/stderr back to (1) and (2)
        try:
            if self.save_fds:
                os.dup2(self.save_fds[0],1)
                os.dup2(self.save_fds[1],2)
        except Exception: # pylint: disable=broad-except
            pass
        # Close all file descriptors
        for fd in self.null_fds + self.save_fds:
            try:
                os.close(fd)
            except Exception: # pylint: disable=broad-except
                pass

#
#from contextlib import contextmanager,redirect_stderr,redirect_stdout
#from os import devnull
#
#@contextmanager
#def suppress_stdout_stderr():
#    """A context manager that redirects stdout and stderr to devnull"""
#    with open(devnull, 'w') as fnull:
#        with redirect_stderr(fnull) as err, redirect_stdout(fnull) as out:
#            yield (err, out)
