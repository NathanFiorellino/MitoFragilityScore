import os
import traceback
import csv
import subprocess
import re
import RNA
import time
import concurrent.futures

import UtilitiesVariables as uv
import UtilitiesFunction as uf
import Configuration as cf


PROCESS_NUMBER = 5


LOOP = 6
MAXIMUM = 10
PERCENT = 5
WINDOW = 0

def create_fasta_from_windows(construct_id, window_1, window_2):
    with open(f"{uv.ENERGY_TEMP_FOLDER}{construct_id}_1.fa", "w") as file:
        file.write(">Window_1\n")
        file.write(window_1)
    with open(f"{uv.ENERGY_TEMP_FOLDER}{construct_id}_2.fa", "w") as file:
        file.write(">Window_2\n")
        file.write(window_2[::-1])


def execute_duplex_fold(construct_id):
    cmd_str = (
        f"{cf.DUPLEX_FOLD_PATH} {uv.ENERGY_TEMP_FOLDER}{construct_id}_1.fa {uv.ENERGY_TEMP_FOLDER}{construct_id}_2.fa"
        + f" {uv.ENERGY_TEMP_FOLDER}{construct_id}.ct -d -l {LOOP} -m {MAXIMUM} -p {PERCENT} -w {WINDOW}"
    )
    subprocess.run(cmd_str, shell=True, stdout=subprocess.DEVNULL)


def read_and_delete_ct(construct_id):
    with open(f"{uv.ENERGY_TEMP_FOLDER}{construct_id}.ct", "r") as file:
        header_line = file.readlines()[0]
        
    match = re.search(r'(?<=ENERGY = )-?\d+(?:\.\d+)?', header_line)
    energy = float(match.group(0))
    os.remove(f"{uv.ENERGY_TEMP_FOLDER}{construct_id}.ct")
     
    return energy


def delete_fastas(construct_id):
    os.remove(f"{uv.ENERGY_TEMP_FOLDER}{construct_id}_1.fa")
    os.remove(f"{uv.ENERGY_TEMP_FOLDER}{construct_id}_2.fa")
    

def process_window_pair(construct_id, window_first, window_second):
    #create_fasta_from_windows(construct_id, window_first, window_second)
    #execute_duplex_fold(construct_id)
    #energy = read_and_delete_ct(construct_id)
    #delete_fastas(construct_id)
    #return energy
    duplex = RNA.duplexfold(window_first, window_second)
    return duplex.energy
    

def calculate_construct_energy(construct_id, window_sextuplet):
        
    # Process for window pair 1, left
    energy_left = process_window_pair(construct_id, window_sextuplet[0], window_sextuplet[1])
        
    # Process for window pair 2, right
    energy_right = process_window_pair(construct_id, window_sextuplet[2], window_sextuplet[3])
    
    # Process for window pair 3, std
    energy = process_window_pair(construct_id, window_sextuplet[4], window_sextuplet[5])
    
    return construct_id, (energy_left, energy_right, energy)


def constructs_parallel_thread(constructs):
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(cf.NCPUS, 61)) as executor:
        futures = [executor.submit(calculate_construct_energy, construct_id, sextuplet) for construct_id, sextuplet in constructs.items()]

        for future in concurrent.futures.as_completed(futures):
            
            result = future.result()
            results[result[0]] = result[1]
                
    return results


def get_new_centers(task_queue):
    new_constructs = []
    process_done = False
    
    while not task_queue.empty():
        
        new_task = task_queue.get()
        
        if new_task[1] == "Done":
            process_done = True
        else:
            new_constructs.append(new_task[1])
    
    return new_constructs, process_done


def energies_from_reference_sequence_constructs(execution_id, task_queue, return_queue):
     
    process_done = False
    while True:
            
        new_centers_to_treat, process_done = get_new_centers(task_queue)
        
        for center_ID in new_centers_to_treat:
            
            # Preparing sequence associated variables
            sequence_ID = uf.sequence_id_from_center_id(center_ID)
            sequence_energies_folder_path = f"{uv.ENERGY_FOLDER}{sequence_ID}{os.sep}"
            if not os.path.isdir(sequence_energies_folder_path):
                os.mkdir(sequence_energies_folder_path)
                
            energy_file_path = f"{sequence_energies_folder_path}{center_ID}-EF.csv"
                
            # User progression update
            text_update = f"Computing energies >> {center_ID} >> In sequence {sequence_ID} >> {time.time()}"
            uf.dump_process_specific_log(execution_id, PROCESS_NUMBER, text_update)
                
            if os.path.isfile(energy_file_path):
                return_queue.put((PROCESS_NUMBER, center_ID))
                continue
            
            # Preparing energy file
            uf.create_energy_file(energy_file_path)
            
            # Gathering constructs information
            constructs = {}
            with open(f"{uv.CONSTRUCT_FOLDER}{sequence_ID}{os.sep}{center_ID}-CF.csv", "r") as file:
                reader = csv.reader(file)
                for i, row in enumerate(reader):
                    if i == 0:
                        continue
                    constructs[row[0]] = (row[6], row[7], row[8], row[9], row[10], row[11])
            
            # Launching parallel computation of all constructs for one center
            results = constructs_parallel_thread(constructs)
            
            # Outputing results to energy file
            for construct_ID, energies in results.items():
                uf.dump_energy_file_line(
                    energy_file_path, 
                    [
                        construct_ID, energies[0], energies[1], energies[2]
                    ]
                )
                
            return_queue.put((PROCESS_NUMBER, center_ID))
            
        if process_done:
            return_queue.put((PROCESS_NUMBER, "Done"))
            text_update = f"Computing relative energies done {time.time()}"
            uf.dump_process_specific_log(execution_id, PROCESS_NUMBER, text_update)
            break 
    
    
def run_process(execution_id, task_queue, return_queue, error_queue):
    try:
        energies_from_reference_sequence_constructs(execution_id, task_queue, return_queue)
             
    except Exception as e:
        error_queue.put((PROCESS_NUMBER, traceback.format_exc()))