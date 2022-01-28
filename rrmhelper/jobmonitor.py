import os
import subprocess
from collections import namedtuple
from time import sleep

from rrmhelper import RRMHelper

class RRMJobMonitor:
    valid_steps = {'mesh', 'map', 'domain', 'topo', 'dry_dep', 'atm_ic'}
    valid_status = {None, 'in progress', 'complete', 'failed', 'to do'}
    TaskOutput = namedtuple('TaskOutput', ['returncode', 'stdout', 'stderr'])

    def __init__(self, **helper_kwargs):
        self.Helper = RRMHelper(**helper_kwargs)
        self.status_file = 'RRMStatus.log'
        self.status = {step: None for step in self.valid_steps}
        self.completed = {step: None for step in self.valid_steps}
        # initialize status based on whether all files are found

    def check_status(self, step=None, init=True, verbose=True):
        """Check current status, return list of tasks that can be started"""
        if init:
            # check if all files are created
            status = self.Helper._locate_files(date_match='latest', update_output=True, verbose=verbose)
            for step, value in status.items():
                self.status[step] = 'complete' if value else 'to do'
            return self.status
        else:
            return self.status[step] if step is not None else None
    
    def update_status(self, step, value):
        """Update status when job completes with success / failure / in progress"""
        self.status[step] = value

    def check_for_dependencies(self, step):
        """Determine which dependencies still need to be run"""
        depends_on = self.Helper.dependencies[step]
        # None - good to go
        # 'str' - just 1
        # tuple - several
        if depends_on is None:
            return None
        elif isinstance(depends_on, str):
            return depends_on if self.status[depends_on] != 'complete' else None
        else:
            return tuple(d for d in depends_on if self.status[d] != 'complete')

    def has_failed_dependencies(self, step):
        """Determine which dependencies still need to be run"""
        depends_on = self.Helper.dependencies[step]
        # None - good to go
        # 'str' - just 1
        # tuple - several
        if depends_on is None:
            return False
        elif isinstance(depends_on, str):
            return self.status[depends_on] == 'failed'
        else:
            return any(self.status[d] == 'failed' for d in depends_on)
        
    def launch_task(self, step, logfile=True):
        """Launch a task"""
        # first, check if task can be launched
        if self.check_for_dependencies(step):
            print(f'{step} cannot be run until after {self.check_for_dependencies(step)}')
            return None
        script_dir = self.Helper.script_dir if self.Helper.script_dir else os.getcwd()
        args = ['bash', self.Helper._links[step].script]
        if logfile:
            stdout = f'{script_dir}/{step}.out'
            stderr = f'{script_dir}/{step}.err'
            with open(stdout, 'w+') as FOUT:
                with open(stderr, 'w+') as FERR:
                    proc = subprocess.Popen(args, stdout=FOUT, stderr=FERR,
                                            universal_newlines=True, cwd=script_dir)
        else:
            PIPE = subprocess.PIPE
            proc = subprocess.Popen(args, stdout=PIPE, stderr=PIPE,
                                    universal_newlines=True, cwd=script_dir)
        return proc
    
    def query_task(self, step, proc, timeout=5, logfile=True):
        if proc.poll():  # returns None -> still running, 
            returncode = proc.returncode
            out, err = proc.communicate()
            return returncode, out, err            
        # alternatively, try this?    
        # try:
        #     out, err = proc.communicate(timeout=timeout)
        # except TimeoutExpired:
        #     # just keep waiting ...
        
    def check_completed_process(self, step, proc):
        returncode = proc.returncode
        out, err = proc.communicate()
        self.completed[step] = self.TaskOutput(returncode, out, err)
        if returncode == 0:
            self.status[step] = 'complete'
        else:
            self.status[step] = 'failed'
        return self.status[step]
            
    def run(self, init=True, logfile=True, retry_attempts=0, sleep_time=None, verbose=True, max_iter=3600):
        status = self.check_status(init=init)
        work_to_do = [step for step in self.valid_steps if self.status[step]=='to do']
        work_in_progress = [step for step in self.valid_steps if self.status[step]=='in progress']
        print('Steps remaining: ', work_to_do)
        running_processes = {step: None for step in self.valid_steps}
        retries = {step: 0 for step in self.valid_steps}
        ix = 0
        
        while work_to_do or work_in_progress:
            ix += 1
            if ix > max_iter:
                raise ValueError('max_iter exceeded!')
            if verbose:
                print(f'iteration: {ix}')
                print(f'work_to_do: {work_to_do}')
                print(f'work_in_progress: {work_in_progress}')
                print(f'status: {self.status}')
            for step in work_to_do:
                proc = self.launch_task(step, logfile=logfile)
                if proc is not None:
                    work_in_progress.append(step)
                    running_processes[step] = proc
                    self.status[step] = 'in progress'
            for step in work_in_progress:
                # check on each running job ...
                if running_processes[step].poll() is not None:
                    self.check_completed_process(step, running_processes[step])
                    self.Helper.update_output()  # update class copy of output dir contents
                    print(f'{step} exited. Status: {self.status[step]}')
            work_in_progress = [step for step in self.valid_steps if self.status[step] == 'in progress']
            work_failed = [step for step in self.valid_steps if self.status[step] == 'failed']
            # retry if necessary ...
            for step in work_failed:
                if retries[step] < retry_attempts:
                    retries[step] += 1
                    self.status[step] = 'to do'
                else:
                    print(f'{step} failed, exceed retry attempts')
            # if any jobs in 'work_to_do' have failed_dependencies, remove :(
            work_to_do = [step for step in self.valid_steps
                          if self.status[step]=='to do' and not self.has_failed_dependencies(step)]
            if sleep_time is not None:
                sleep(sleep_time)


class RRMTask:
    """Skeleton class to contain an RRMTask"""
    def __init__(self):
        self.run_script = None
        self.name = None
        self.dependencies = None
        self.status = None
        self.returncode = None
        self.stdout = None
        self.stderr = None
        self.files_generated = None
        pass

    def execute(self):
        """execute task script"""
        pass

    def report_status(self):
        """update status of task, report to log file or whatevs"""
        pass

    def clean(self):
        """clean output from previous job"""
        pass

    def postprocess(self):
        """Any post-processing needed after Task is executed"""
        pass