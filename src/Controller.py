import json
import sys
import os
import time
import multiprocessing as mp

import UtilitiesVariables as uv
import UtilitiesFunction as uf
import Configuration as cf

PROCESS_NUMBER = 0


def initialise_green_lights(processes_to_run):
    # Each process that is supposed to run in this execution will have a red light until condition are met
    # Note: processes that are not supposed to run in this execution are considered done and thus have a green light.
    # Thus we set lights to green by default and to red if they have to run. 
    green_lights = {1: True, 2: True, 3: True, 4:True, 5:True, 6:True}
    for process_number in processes_to_run:
        green_lights[process_number] = False
        
    return green_lights


def prepare_queues():
    queues = {
        "Task" :{
            1: mp.Queue(),
            2: mp.Queue(),
            3: mp.Queue(),
            4: mp.Queue(),
            5: mp.Queue(),
            6: mp.Queue(),
        },
        "Return" :{
            1: mp.Queue(),
            2: mp.Queue(),
            3: mp.Queue(),
            4: mp.Queue(),
            5: mp.Queue(),
            6: mp.Queue(),
        },
        "Errors": mp.Queue()
    }
    return queues


def initialise_process(process_number, conditions_met, queues, processes_to_run):
    # This function simply check for a given process number if it can be started and if it does
    # it import the corresponding python script and starts an mp Process

    process_can_be_started = False
    
    if process_number in [1,3]:
        # Processes 1 and 3 do not need inputs from other process and can thus start anytime
        process_can_be_started = True
    elif process_number == 2:
        # Reference sequence energy calculation requires reference sequence constructs
        process_can_be_started = conditions_met[1]
    elif process_number == 4:
        # Relative sequence constructs generation requires reference constructs and relative sequences
        process_can_be_started = conditions_met[1] and conditions_met[3]
    elif process_number == 5:
        # Relative sequence energy calculation requires relative sequence constructs
        process_can_be_started = conditions_met[4]
    elif process_number == 6:
        # Fragility scoring requires relative sequence energy and reference sequence energy
        process_can_be_started = conditions_met[2] and conditions_met[5]
        
    if process_can_be_started:
        module = __import__(uv.PROCESSES[process_number][1])
        process = mp.Process(target=module.run_process, args=(EXECUTION_ID, queues["Task"][process_number], queues["Return"][process_number], queues["Errors"]))
        process.start()
        processes_to_run.remove(process_number)
        print(f"Launched process, {uv.PROCESSES[process_number][0]}, execution ID: {process.pid}")
        
        # We keep track of the process ids so we can kill process if needed
        with open(f"{uv.EXECUTION_FOLDER}{EXECUTION_ID}{os.sep}subprocess_pids.txt", "a") as file:
            file.write(str(process.pid) + "#") 
            
    else:
        process = None
        
    return process


def except_errors(error_queue):
    return not error_queue.empty()


def close_processes(processes):
    for process_number, process in processes.items():
        if not process is None:
            process.terminate()
            processes[process_number] = None


def transmit_results(process_number, new_process_results, queues):
    
    if process_number == 1:
        for result in new_process_results:
            # Adding results from reference sequence construct generation to reference sequence energies calculation 
            queues["Task"][2].put(result) 
            # Adding results from reference sequence construct generation to relative construct generation
            queues["Task"][4].put(result)
    
    elif process_number == 2:
        for result in new_process_results:
            # Adding results from reference sequence energies calculation to fragility scoring
            queues["Task"][6].put(result) 
    
    elif process_number == 3:
        for result in new_process_results:
            # Adding results from relative sequence generation to relative sequence construct generation
            queues["Task"][4].put(result) 
    
    elif process_number == 4:
        for result in new_process_results:
            # Adding results from relative sequence construct generation to relative sequence energies calculation
            queues["Task"][5].put(result) 
    
    elif process_number == 5:
        for result in new_process_results:
            # Adding results from relative sequence energies calculation to fragility scoring
            queues["Task"][6].put(result) 
        
        
def check_if_condition_met(process_number, process_results):
    if process_number in [1, 2, 3, 4, 5]:
        conditon_met = len(process_results) > 0
    else:
        conditon_met = ((6,"Done") in process_results)
    
    return conditon_met


def control_processes(green_lights, queues, running_processes, results):
    for process_number, running_process in running_processes.items():
        if running_process is None:
            continue
        
        # Colletcting new results of the process
        new_process_results = []
        while not queues["Return"][process_number].empty():
            new_process_results.append(queues["Return"][process_number].get())
        
        # Transmitting new results to processes that depend on them
        transmit_results(process_number, new_process_results, queues)
        
        # Adding new results to final results
        results[process_number].extend(new_process_results)
        
        # Handling green lights
        if not green_lights[process_number]:
            green_lights[process_number] = check_if_condition_met(process_number, results[process_number])


if __name__ == "__main__":
    # ith    
    global EXECUTION_ID
    EXECUTION_ID = sys.argv[1]
    
    text_update = f"Application Started << {time.time()}"
    uf.dump_process_specific_log(EXECUTION_ID, PROCESS_NUMBER, text_update)
    print(f"Launching application, execution ID:{EXECUTION_ID}")
    
    with open(uf.process_instructions_path(PROCESS_NUMBER, EXECUTION_ID), "r") as file:
        instructions = json.load(file)
    
    # Preparing green lights for processes
    processes_to_run = instructions[uv.PIPELINE_PROCESS_TO_RUN_KEY]
    green_lights = initialise_green_lights(processes_to_run)
    
    # Preparing error handling
    queues = prepare_queues()
    
    # Prepare variables for loop
    running_processes = {1: None, 2: None, 3:None, 4:None, 5:None, 6: None}
    results = {1: [], 2: [], 3:[], 4: [], 5: [], 6: []}
    
    # Controller Instance, this loop should go on as long as the process runs
    running = True
    finished = False
    while running:
        
        for process_to_run in processes_to_run:
            new_process = initialise_process(process_to_run, green_lights, queues, processes_to_run)
            running_processes[process_to_run] = new_process
    
        time.sleep(20)
        
        if except_errors(queues["Errors"]):
            running = False
            close_processes(running_processes)
            break
        
        control_processes(green_lights, queues, running_processes, results)
        
        if green_lights[6]:
            finished = True
            running = False

    if finished:
        close_processes(running_processes)
        text_update = f"Process Finished Sucessfuly << {time.time()}"
        print(f"Finished application sucessfuly, execution ID: {EXECUTION_ID}")
        uf.dump_process_specific_log(EXECUTION_ID, PROCESS_NUMBER, text_update)
        uf.cleanup_instructions(EXECUTION_ID)
    else:
        #look at error queue and put error in process_log
        error = queues["Errors"].get()
        text_update = f"Process Finished with error: {error} << {time.time()}"
        print(f"Finished application with error, execution ID: {EXECUTION_ID}")
        uf.dump_process_specific_log(EXECUTION_ID, PROCESS_NUMBER, text_update)
        print(error)
        pass