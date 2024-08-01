
import os
import csv
import RNA
import concurrent.futures

import UtilitiesVariables as uv
import UtilitiesFunction as uf
import Configuration as cf

def calculate_construct_energy(construct_id, window_sextuplet):
    """Calculate energy based on pairing of the construct windows"""
    test = f"{construct_id.split('-')[-2]}-{construct_id.split('-')[-1]}"
    # Process for window pair 1, left
    energy_left = RNA.duplexfold(window_sextuplet[0], window_sextuplet[1]).energy
        
    # Process for window pair 2, right
    energy_right = RNA.duplexfold(window_sextuplet[2], window_sextuplet[3]).energy
    
    # Process for window pair 3, std
    energy = RNA.duplexfold(window_sextuplet[4], window_sextuplet[5]).energy
    return construct_id, (energy_left, energy_right, energy)


def constructs_parallel_thread(constructs):
    """Calculating energies """
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=cf.NCPUS_FOR_ENERGY_CALCULATIONS) as executor:
        futures = [executor.submit(calculate_construct_energy, construct_ID, sextuplet) for construct_ID, sextuplet in constructs.items()]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results[result[0]] = result[1]
                
    return results


def get_new_centers(task_queue):
    """Extracts new centers to treat from task queue"""
    new_constructs = []
    process_done = False
    
    while not task_queue.empty():
        new_task = task_queue.get()
        if new_task[1] == uv.DONE:
            process_done = True
        else:
            new_constructs.append(new_task[1])
    return new_constructs, process_done


def energies_from_sequence_constructs(process_number, task_queue, return_queue):
    """Calculates energies from given relative sequence constructs"""
    process_done = False
    while True:
            
        new_centers_to_treat, process_done = get_new_centers(task_queue)
        for center_ID in new_centers_to_treat:
            
            # Preparing sequence associated variables
            sequence_ID = uf.sequence_ID_from_ID(center_ID)
            sequence_energies_folder_path = f"{uv.ENERGY_FOLDER}{sequence_ID}{os.sep}"
            if not os.path.isdir(sequence_energies_folder_path):
                os.mkdir(sequence_energies_folder_path) 
            energy_file_path = f"{sequence_energies_folder_path}{center_ID}-EF.csv"
                
            # Verifying that energies are not already calculated, if there are we can pass the center to the next processes
            if os.path.isfile(energy_file_path):
                return_queue.put((process_number, center_ID))
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
                
            return_queue.put((process_number, center_ID))
            
        if process_done:
            return_queue.put((process_number, uv.DONE))
            break 
    