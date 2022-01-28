from pathlib import Path
from rrmhelper.jobmonitor import RRMJobmonitor

if __name__ == "__main__":
    try:
        script_dir = Path(__file__).resolve()
    except NameError:
        script_dir = Path().cwd().resolve()
    
    config_script = 'config.sh'
    JobMonitor = RRMJobmonitor(script_dir=script_dir,
                               config_script=config_script)
    JobMonitor.run(init=True, logfile=True, retry_attempts=0,
                   sleep_time=30, verbose=True, max_iter=2880)
