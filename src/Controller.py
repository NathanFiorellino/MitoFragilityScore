import os
import time
import logging
import multiprocessing as mp

import UtilitiesVariables as uv
import UtilitiesFunction as uf
import Configuration as cf

PROCESS_NUMBER = 0

def prepare_logs(execution_ID):
    """Preparing human readable and machine readable logs."""
    log_file_paths = f"{uv.EXECUTION_FOLDER}{execution_ID}{os.sep}{execution_ID}-process_log"

    # Text log, human readable log
    text_logger = logging.getLogger(__name__)
    text_log_path = log_file_paths + ".txt"
    logging.basicConfig(filename=text_log_path, encoding='utf-8', level=logging.DEBUG)

    # Json log, machine readable log
    json_log_path = log_file_paths + ".json"
    uf.create_json_log(json_log_path)

    def json_logger(category, key, value):
        uf.dump_log(json_log_path, category, key, value)

    return text_logger, json_logger


def prepare_queues():
    """Preparing multiprossesing queues for processing feedback to the controller."""
    queues = {
        uv.TASK :{
            1: mp.Queue(),
            2: mp.Queue(),
            3: mp.Queue(),
            4: mp.Queue(),
            5: mp.Queue(),
            6: mp.Queue(),
        },
        uv.RETURN :{
            1: mp.Queue(),
            2: mp.Queue(),
            3: mp.Queue(),
            4: mp.Queue(),
            5: mp.Queue(),
            6: mp.Queue(),
        },
        uv.ERRORS: mp.Queue()
    }
    return queues


def prepare_signal_lights():
    """Preparing signalisation for launching processes."""
    signal_lights = {1: False, 2: False, 3: False, 4:False, 5:False, 6: False} 
    # These signal if the process has already some results or in the case of process 6 if the pipeline is done
        
    return signal_lights


def prepare_running_processess():
    """Preparing dictionary to record active processes."""
    running_processes = {1: None, 2: None, 3:None, 4:None, 5:None, 6: None}
        
    return running_processes


def prepare_results():
    """Preparing dictionary to record results."""
    results = {1: [], 2: [], 3:[], 4: [], 5: [], 6: []}
        
    return results


def check_process_start_condition(process_number, signal_lights):
    """Check if conditions are met for launching specific process."""
    process_can_be_started = False
    
    if process_number in [1,3]:
        # Processes 1 and 3 do not need inputs from other process and can thus start anytime
        process_can_be_started = True
    elif process_number == 2:
        # Reference sequence energy calculation requires reference sequence constructs
        process_can_be_started = signal_lights[1]
    elif process_number == 4:
        # Relative sequence constructs generation requires reference constructs and relative sequences
        process_can_be_started = signal_lights[1] and signal_lights[3]
    elif process_number == 5:
        # Relative sequence energy calculation requires relative sequence constructs
        process_can_be_started = signal_lights[4]
    elif process_number == 6:
        # Fragility scoring requires relative sequence energy and reference sequence energy
        process_can_be_started = signal_lights[2] and signal_lights[5]

    return process_can_be_started


def initialise_process(instructions, process_number, queues):
    """Initialising processes with adequate inputs."""
    module = __import__(uv.PROCESSES[process_number][1])
    process = mp.Process(target=module.run_process, args=(instructions, queues[uv.TASK][process_number], queues[uv.RETURN][process_number], queues[uv.ERRORS]))
    process.start()
        
    return process


def transmit_results(process_number, new_process_results, queues):
    "Trasmit results of processes to the corresponding processes that continue the treatment of the data."
    if process_number == 1:
        for result in new_process_results:
            # Adding results from reference sequence construct generation to reference sequence energies calculation 
            queues[uv.TASK][2].put(result) 
            # Adding results from reference sequence construct generation to relative construct generation
            queues[uv.TASK][4].put(result)
    
    elif process_number == 2:
        for result in new_process_results:
            # Adding results from reference sequence energies calculation to fragility scoring
            queues[uv.TASK][6].put(result) 
    
    elif process_number == 3:
        for result in new_process_results:
            # Adding results from relative sequence generation to relative sequence construct generation
            queues[uv.TASK][4].put(result) 
    
    elif process_number == 4:
        for result in new_process_results:
            # Adding results from relative sequence construct generation to relative sequence energies calculation
            queues[uv.TASK][5].put(result) 
    
    elif process_number == 5:
        for result in new_process_results:
            # Adding results from relative sequence energies calculation to fragility scoring
            queues[uv.TASK][6].put(result) 


def update_signal_light(process_number, process_results):
    """Turning on signal light for different processes if the corresponding conditions are met."""
    if process_number in [1, 2, 3, 4, 5]:
        turn_on = len(process_results) > 0
    else:
        turn_on = ((6,uv.DONE) in process_results)
    
    return turn_on


def control_processes(signal_lights, queues, running_processes, results, loop_number, json_logger, text_logger):
    """Collecting results of process transmiting them, saving the results and handling signal lights."""
    for process_number, running_process in running_processes.items():
        if running_process is None:
            continue
        
        # Collecting new results of the process
        new_process_results = []
        while not queues[uv.RETURN][process_number].empty():
            new_process_results.append(queues[uv.RETURN][process_number].get())
        
        # Transmitting new results to processes that is next in line to treat the data.
        transmit_results(process_number, new_process_results, queues)
        
        # Saving results
        results[process_number].extend(new_process_results)

        # Logging results
        json_logger(uv.LOOP_YIELD_KEY, f"{loop_number}-{process_number}", len(new_process_results))
        text_logger.info(f"{uv.LOOP_YIELD_KEY}, (loop {loop_number}, process number {process_number}) : {len(new_process_results)}")
        
        # If finished Logging approximate process finish time and deleting reference to process.
        if (process_number, uv.DONE) in new_process_results:
            log_event_time(json_logger, text_logger, uv.TIMEPOINTS_KEY, uv.FINISH_PROCESS_KEY[process_number], uv.FINISH_PROCESS_KEY[process_number])
            running_processes[process_number] = None


        # Handling signal lights
        if not signal_lights[process_number]:
            signal_lights[process_number] = update_signal_light(process_number, results[process_number])


def log_event_time(json_logger, text_logger, json_category, json_key, event_name):
    "Standard human readable and machine readable information logging"
    info_time = time.time()
    json_logger(json_category, json_key, info_time)
    text_logger.info(f"{event_name} at {info_time}")


def log_exception(json_logger, text_logger, error):
    "Standard human readable and machine readable exception logging"
    process_number = error[0]
    json_logger(uv.ERROR_KEY, error[1][1][-1], error[1][1])
    text_logger.error(f"Error in process {process_number}")
    for line in error[1][1]:
        text_logger.error(line)


def close_processes(processes):
    """Manually terminating processes"""
    for process_number, process in processes.items():
        if not process is None:
            process.terminate()
            processes[process_number] = None


def launch(execution_ID):
    """Prepares everything that is handled on the controller level and Launches the program"""
    # Preparing neccesary objects
    instructions = uf.load_instructions_base(execution_ID)
    text_logger, json_logger  = prepare_logs(execution_ID)
    queues = prepare_queues()
    signal_lights = prepare_signal_lights()
    running_processes = prepare_running_processess()
    results = prepare_results()

    processes_to_start = instructions[uv.PIPELINE_PROCESS_TO_RUN_KEY]
    running = True

    # Logging start of application
    log_event_time(json_logger, text_logger, uv.TIMEPOINTS_KEY, uv.START_APP_KEY, uv.START_APP_KEY)

    loop_number = 0
    while running:
        loop_number = loop_number + 1

        # Log start of loop
        log_event_time(json_logger, text_logger, uv.LOOP_KEY, loop_number, f"{uv.LOOP_KEY}, loop {loop_number},")

        processes_left_to_start = []
        for process_to_start in processes_to_start:
            # For each process to start, check if ready to start and launch 
            if check_process_start_condition(process_to_start, signal_lights):
                running_processes[process_to_start] = initialise_process(instructions, process_to_start, queues)
                
                # Log start of process
                log_event_time(json_logger, text_logger, uv.TIMEPOINTS_KEY, uv.START_PROCESS_KEY[process_to_start], uv.START_PROCESS_KEY[process_to_start])

            else:
                processes_left_to_start.append(process_to_start)
        
        processes_to_start = processes_left_to_start

        # Give launched processes time to work
        time.sleep(cf.WAITING_TIME)
        
        # Check for errors
        if not queues[uv.ERRORS].empty():
            close_processes(running_processes)
            running = False
            error = queues[uv.ERRORS].get()

            # Log error
            log_exception(json_logger, text_logger, error)
            del error
            log_event_time(json_logger, text_logger, uv.TIMEPOINTS_KEY, uv.END_APP_KEY,  f"{uv.END_APP_KEY} with error")

            break
        
        # Update on advancements in processes
        control_processes(signal_lights, queues, running_processes, results, loop_number, json_logger, text_logger)

        # Check if application finished
        if signal_lights[6]:
            running = False

            # Log end of application
            log_event_time(json_logger, text_logger, uv.TIMEPOINTS_KEY, uv.END_APP_KEY,  f"{uv.END_APP_KEY} sucessfully")