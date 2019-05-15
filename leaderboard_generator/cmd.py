from subprocess import Popen, PIPE
import os


def run(cmd, cwd=None, env=None, throw=True, verbose=True, print_errors=True,
        shell=False):
    def say(*args):
        if verbose:
            print(*args)
    say(cmd)
    env = env or dict(os.environ)
    if not isinstance(cmd, list):
        cmd = cmd.split()
    process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=cwd, env=env,
                    shell=shell)
    result, err = process.communicate()
    if process.returncode == 0:
        result = result + err
    if not isinstance(result, str):
        result = ''.join(map(chr, result))
    result = result.strip()
    say(result)
    if process.returncode != 0:
        if not isinstance(err, str):
            err = ''.join(map(chr, err))
        err_msg = ' '.join(cmd) + ' finished with error ' + err.strip()
        if throw:
            raise RuntimeError(err_msg)
        elif print_errors:
            print(err_msg)
    return result, process.returncode
