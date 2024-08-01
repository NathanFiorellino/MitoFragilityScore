import sys
import traceback

import SequenceEnergiesCalculator as sec

PROCESS_NUMBER = 2
    
def run_process(instructions, task_queue, return_queue, error_queue):
    """Permits running process from controller and handling error catching"""
    try:
        sec.energies_from_sequence_constructs(PROCESS_NUMBER, task_queue, return_queue)
             
    except Exception as error:
        excecution_information = sys.exc_info()
        formatted_exception =  traceback.format_exception( *excecution_information)
        error_queue.put((PROCESS_NUMBER, [error, formatted_exception]))