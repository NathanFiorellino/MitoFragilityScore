import argparse
import os
import json
import subprocess
import uuid
import signal

import UtilitiesVariables as uv
import UtilitiesFunction as uf
import Configuration as cf

def parse_launching_process_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--settings", default="STANDARD", help="Settings file path, that specifies details for the launch")
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-l", "--launch", action="store_true", help="Launch new execution")
    group.add_argument("-a", "--abort", action="store_true", help="Abort currently running execution")
    
    args = parser.parse_args()
    
    if args.settings != "STANDARD" and not os.path.isfile(args.settings):
        parser.error("Input for settings file is not valid, please choose an existing file.")
    
    return args


def launch_controller_instance(settings):
    
    # Preparing the execution id for the process
    if settings[uv.PIPELINE_EXECUTION_ID_KEY] == "New Execution":
        execution_ID = str(uuid.uuid4())
    else:
        execution_ID = settings[uv.PIPELINE_EXECUTION_ID_KEY]
    
    # Processes to run and create sets of instructions accordingly
    processes_to_run = settings[uv.PIPELINE_PROCESS_TO_RUN_KEY]
    processes_to_run.append(0)
    
    # Relocating settings information in Execution folder for each process
    os.mkdir(f"{uv.EXECUTION_FOLDER}{execution_ID}")
    for process_to_run in processes_to_run:
        uf.create_process_instructions(process_to_run, execution_ID, settings)

    settings[uv.INDIVIDUALS_KEY] = uf.infer_individuals(settings)
    # From here on the initial setting sbecome the instructions for all process
    uf.create_instructions(execution_ID, settings) 
    
    # Launching Controller
    process = subprocess.Popen([f"{cf.PYTHON_VERSION}", f"{uv.PROCESSES[0][1]}.py", execution_ID])
    with open(f"{uv.EXECUTION_FOLDER}{execution_ID}{os.sep}controller_pid.txt", "w") as file:
        file.write(str(process.pid))
    print("User Launched:", execution_ID)

    return process


def abort_controller_instance(execution_ID):
    with open(f"{uv.EXECUTION_FOLDER}{execution_ID}{os.sep}controller_pid.txt", "r") as file:
        controller_pid = int(file.read())
                             
    with open(f"{uv.EXECUTION_FOLDER}{execution_ID}{os.sep}subprocess_pids.txt", "r") as file:
        subprocess_pids = file.read().split("#")[:-1]
        
    pids = subprocess_pids[:] + [controller_pid]
    
    for pid in pids:
        try:
            os.kill(int(pid), signal.SIGKILL)
        except Exception as e:
            pass
    
    print("User Killed:", execution_ID, "and associated processes")
    
    os.remove(f"{uv.EXECUTION_FOLDER}{execution_ID}{os.sep}controller_pid.txt")
    os.remove(f"{uv.EXECUTION_FOLDER}{execution_ID}{os.sep}subprocess_pids.txt")

if __name__ == "__main__":
   SETTINGS_FILE_PATH = "settings.json"

   if not os.path.isfile(SETTINGS_FILE_PATH):
        raise "No settings file"
   
   with open(SETTINGS_FILE_PATH, "r") as file:
        settings = json.load(file)

   process = launch_controller_instance(settings)
   process.wait()