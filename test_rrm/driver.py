from pathlib import Path
import sys

# add rrmhelper path
sys.path.append(str(Path('../rrmhelper').resolve()))
from jobmonitor import RRMJobMonitor

if __name__ == "__main__":
    try:
        script_dir = Path(__file__).resolve().parent
        print(script_dir)
    except NameError:
        script_dir = Path().cwd().resolve()
    
    config_script = 'config.sh'
    JobMonitor = RRMJobMonitor(script_dir=script_dir,
                               config_script=config_script)
    JobMonitor.run(init=True, logfile=True, retry_attempts=0,
                   sleep_time=30, verbose=True, max_iter=2880)
