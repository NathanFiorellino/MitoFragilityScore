import os
import json
import subprocess
import uuid
import signal

import UtilitiesVariables as uv
import UtilitiesFunction as uf
import Configuration as cf


def read_settings():
    # The settings file path is set in configuration, a little check permits to tell the user what to do.
    if not os.path.isfile(cf.SETTINGS_FILE_PATH):
        raise f"No settings file at {cf.SETTINGS_FILE_PATH}, this path is set in the /src/Configuration.py file"
    
    with open(cf.SETTINGS_FILE_PATH, "r") as file:
        settings = json.load(file)

    return settings

def prepare_controller_instance(settings):
    
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
    return execution_ID


def launch_controller_instance(execution_ID):
    # Launching Controller
    process = subprocess.Popen([f"{cf.PYTHON_VERSION}", f"{uv.PROCESSES[0][1]}.py", execution_ID])
    with open(f"{uv.EXECUTION_FOLDER}{execution_ID}{os.sep}controller_pid.txt", "w") as file:
        file.write(str(process.pid))

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
    settings = read_settings()
    execution_ID = prepare_controller_instance(settings)
    process = launch_controller_instance(execution_ID)
    process.wait()