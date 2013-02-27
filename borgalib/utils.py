# -*- coding: utf-8 -*-

import os
import sys
import threading
import subprocess


__all__ = ('run', )


# Taken from fedorahosted.org/kobo
def run(cmd, show_cmd=False, stdout=False, logfile=None, can_fail=False,
        workdir=None, stdin_data=None, return_stdout=True,
        buffer_size=4096):
    """Run a command in shell.

    @param show_cmd: show command in stdout/log
    @type show_cmd: bool
    @param stdout: print output to stdout
    @type stdout: bool
    @param logfile: save output to logfile
    @type logfile: str
    @param can_fail: when set, retcode is returned instead of raising RuntimeError
    @type can_fail: bool
    @param workdir: change current directory to workdir before starting a command
    @type workdir: str
    @param stdin_data: stdin data passed to a command
    @type stdin_data: str
    @param buffer_size: size of buffer for reading from proc's stdout, use -1 for line-buffering
    @type buffer_size: int
    @return_stdout: return command stdout as a function result (turn off when working with large data, None is returned instead of stdout)
    @return_stdout: bool
    @return: (command return code, merged stdout+stderr)
    @rtype: (int, str) or (int, None)
    """
    if logfile:
        logfile = os.path.join(workdir or "", logfile)

    if type(cmd) in (list, tuple):
        import pipes
        cmd = " ".join(( pipes.quote(i) for i in cmd ))

    if show_cmd:
        command = "COMMAND: %s\n%s\n" % (cmd, "-" * (len(cmd) + 9))
        if stdout:
            print command,
        if logfile:
            save_to_file(logfile, command)

    stdin = None
    if stdin_data is not None:
        stdin = subprocess.PIPE

    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, stdin=stdin,
                            cwd=workdir)

    if stdin_data is not None:
        class StdinThread(threading.Thread):
            def run(self):
                proc.stdin.write(stdin_data)
                proc.stdin.close()
        stdin_thread = StdinThread()
        stdin_thread.daemon = True
        stdin_thread.start()

    output = ""
    while True:
        if buffer_size == -1:
            lines = proc.stdout.readline()
        else:
            lines = proc.stdout.read(buffer_size)
        if lines == "":
            break
        if stdout:
            print lines,
        if logfile:
            save_to_file(logfile, lines, append=True)
        if return_stdout:
            output += lines
    proc.wait()

    if stdin_data is not None:
        stdin_thread.join()

    err_msg = "ERROR running command: %s" % cmd
    if proc.returncode != 0 and show_cmd:
        print >> sys.stderr, err_msg

    if proc.returncode != 0 and not can_fail:
        raise RuntimeError(err_msg)

    if not return_stdout:
        output = None

    return (proc.returncode, output)
