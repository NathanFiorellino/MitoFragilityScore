import sys
import csv
import traceback
import os
import UtilitiesFunction as uf
import UtilitiesVariables as uv

PROCESS_NUMBER = 6

def score_centers(new_centers_to_treat):
    """Extracts new centers to treat from task queue"""
    for ID_parts in new_centers_to_treat:
        
        #Note: ID_parts is composed like this [individual name, reference sequence ID, Construct generation specification and Center attached]

        # Reconstructing IDS
        reference_sequence_ID = f"{uv.SEQUENCE_ID_SEPARATOR}-{ID_parts[1]}"
        relative_sequence_ID = uf.form_relative_sequence_ID(reference_sequence_ID,ID_parts[0])
        reference_center_ID = f"{reference_sequence_ID}-{ID_parts[2]}"
        relative_center_ID = f"{relative_sequence_ID}-{ID_parts[2]}"

        # Preparing folder paths
        reference_sequence_energies_folder_path = f"{uv.ENERGY_FOLDER}{reference_sequence_ID}{os.sep}"
        relative_sequence_energies_folder_path = f"{uv.ENERGY_FOLDER}{relative_sequence_ID}{os.sep}"
        fragility_folder_path = f"{uv.FRAGILITY_FOLDER}{relative_sequence_ID}{os.sep}"

        # Preparing file paths
        reference_energy_file_path = f"{reference_sequence_energies_folder_path}{reference_center_ID}-EF.csv"
        relative_energy_file_path = f"{relative_sequence_energies_folder_path}{relative_center_ID}-EF.csv"
        fragility_file_path  = f"{fragility_folder_path}{relative_center_ID}-FF.csv"

        if not os.path.isdir(fragility_folder_path):
            os.mkdir(fragility_folder_path)
        
        if os.path.isfile(fragility_file_path):
            continue

        # Gathering energies information for the reference
        scores = {}
        energies = {}

        with open(reference_energy_file_path, "r") as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                if i == 0:
                    continue
                construct_name = uf.contruct_name_from_ID(row[0])
                energies[construct_name] = [float(row[1]), float(row[2]), float(row[3])]
                scores[construct_name] = uf.generate_base_score()

        # Gathering energies information for the reference and scoring
        with open(relative_energy_file_path, "r") as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                if i == 0:
                    continue
                construct_name = uf.contruct_name_from_ID(row[0])
                scores[construct_name][0] = uf.score_fragility(energies[construct_name][0], float(row[1]))
                scores[construct_name][1] = uf.score_fragility(energies[construct_name][1], float(row[2]))
                scores[construct_name][2] = uf.score_fragility(energies[construct_name][2], float(row[3]))
                scores[construct_name][3] = True

        uf.create_fragility_file(fragility_file_path)

        for construct_name, row in scores.items():
            construct_id = f"{relative_sequence_ID}-{construct_name}"
            uf.dump_fragility_file_line(fragility_file_path, [construct_id, row[0], row[1], row[2], row[3]])


def get_new_centers_to_treat(task_queue, available_reference_energies, relative_energies_to_score, scorable_constructs, proceses_done):
    """Extracts new centers to treat and new individuals from task queue and formats them in order for the process to be able to score"""
    while not task_queue.empty():
        
        new_task = task_queue.get()
        if new_task[1] == uv.DONE:
            if new_task[0] == 2:
                proceses_done[0] = True
            elif new_task[0] == 5:
                proceses_done[1] = True
            continue

        # Prepare variables for identyfing scorable constructs in reference        
        reference_sequence_name = uf.reference_sequence_name_from_ID(new_task[1])
        subsequence_name= uf.subsequence_name_from_ID(new_task[1])
        construct_generation_specification = uf.construct_generation_specification_from_ID(new_task[1])
        center = uf.center_from_ID(new_task[1], True)
                
        # Creating comaparable ID parts
        first_ID_part =  f"{reference_sequence_name}-{subsequence_name}"
        second_ID_part = f"{construct_generation_specification}-{center}"

        # Note :If the task is from process 2 then the task is the name of a reference center that corresponds to a reference energy file
        # If the task is from process 5 then the task is the name of a reference center that corresponds to a relative energy file

        if new_task[0] == 2:
            available_reference_energies.append((first_ID_part, second_ID_part))

            # Adding to scorable constructs all construct where the reference and relative energies have been calculated 
            for individual, ID_parts_individual in relative_energies_to_score.items():
                for ID_parts in ID_parts_individual:
                    if ID_parts[0] == first_ID_part and ID_parts[1] == second_ID_part:
                        scorable_constructs.append((individual, ID_parts[0], ID_parts[1]))
                
        elif new_task[0] == 5:
            individual = uf.individual_name_from_ID(new_task[1])

            relative_energies_to_score[individual].append((first_ID_part, second_ID_part))

            # Adding to scorable constructs all construct where the reference and relative energies have been calculated 
            for ID_parts in available_reference_energies:
                if ID_parts[0] == first_ID_part and ID_parts[1] == second_ID_part:
                    scorable_constructs.append((individual, ID_parts[0], ID_parts[1]))


def score_relative_sequences(instructions, task_queue, return_queue):
    """Generates scores from given sequences"""

    # Preapring generation level variables
    proceses_done = [False, False]
    available_reference_energies = []
    individuals = instructions[uv.INDIVIDUALS_KEY]
    relative_energies_to_score = dict.fromkeys(individuals, [])
    
    while True:

        scorable_constructs = []
        get_new_centers_to_treat(task_queue, available_reference_energies, relative_energies_to_score, scorable_constructs, proceses_done)
        score_centers(scorable_constructs)

        if proceses_done[0] and proceses_done[1]:
            return_queue.put((PROCESS_NUMBER, uv.DONE))
            break       


def run_process(instructions, task_queue, return_queue, error_queue):
    """Permits running process from controller and handling error catching"""
    try:
       score_relative_sequences(instructions, task_queue, return_queue)
    except Exception as error:
        excecution_information = sys.exc_info()
        formatted_exception =  traceback.format_exception( *excecution_information)
        error_queue.put((PROCESS_NUMBER, [error, formatted_exception]))