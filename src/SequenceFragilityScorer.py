import csv
import time
import os
import UtilitiesFunction as uf
import UtilitiesVariables as uv
PROCESS_NUMBER = 6



def score_centers(execution_id, new_centers_to_treat, return_queue):

    for disassembled_center_ID in new_centers_to_treat:
        # Preparing file paths.
        relative_sequence_name = f"{disassembled_center_ID[1]}-{disassembled_center_ID[0]}"
        reference_sequence_name = f"{disassembled_center_ID[1]}"
        relative_sequence_energies_folder_path = f"{uv.ENERGY_FOLDER}{relative_sequence_name}{os.sep}"
        reference_sequence_energies_folder_path = f"{uv.ENERGY_FOLDER}{reference_sequence_name}{os.sep}"

        relative_sequence_ID = f"{relative_sequence_name}-{disassembled_center_ID[2]}" # center id ?
        relative_energy_file_path = f"{relative_sequence_energies_folder_path}{relative_sequence_ID}-EF.csv"

        reference_sequence_ID = f"{reference_sequence_name}-{disassembled_center_ID[2]}" # center id ?
        reference_energy_file_path = f"{reference_sequence_energies_folder_path}{reference_sequence_ID}-EF.csv"

        fragility_folder_path = f"{uv.FRAGILITY_FOLDER}{relative_sequence_name}{os.sep}"
        if not os.path.isdir(fragility_folder_path):
            os.mkdir(fragility_folder_path)

        fragility_file_path  = f"{fragility_folder_path}{relative_sequence_ID}-FF.csv"
        
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

        # Fathering energies informaiton for the reference and scoring
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


def get_new_centers_to_treat(task_queue, available_reference_constructs, relative_constructs_to_score, scorable_constructs, proceses_done):
    
    while not task_queue.empty():
        
        new_task = task_queue.get()
        if new_task[0] == 2: # If the task is from process 2 then the task is the name of a reference center that corresponds to a reference construct file
            if new_task[1] == "Done":
                proceses_done[0] = True
            else:
                reference_sequence = uf.reference_sequence_from_ID(new_task[1], True)
                construct_generation_specification = uf.construct_generation_specification_from_ID(new_task[1])
                center = uf.center_from_ID(new_task[1], True)

                available_reference_constructs.append((reference_sequence,f"{construct_generation_specification}-{center}"))

                for individual, disassembled_center_IDs in relative_constructs_to_score.items():
                    for disassembled_center_ID in disassembled_center_IDs:
                        if disassembled_center_ID[0] == reference_sequence and disassembled_center_ID[1] == f"{construct_generation_specification}-{center}":
                            scorable_constructs.append((individual,disassembled_center_ID[0], disassembled_center_ID[1]))
                
        elif new_task[0] == 5:
            if new_task[1]== "Done":
                proceses_done[1] = True
            else:
                if new_task[1] in available_reference_constructs: # add for loop for each individual
                    scorable_constructs.append(new_task[1])
                else:
                    reference_sequence = uf.reference_sequence_from_ID(new_task[1], False)
                    individual = uf.individual_from_ID(new_task[1])
                    construct_generation_specification = uf.construct_generation_specification_from_ID(new_task[1])
                    center = uf.center_from_ID(new_task[1], True)
                    
                    relative_constructs_to_score[individual].append((reference_sequence,f"{construct_generation_specification}-{center}"))

                    for disassembled_center_ID in available_reference_constructs:
                        if disassembled_center_ID[0] == reference_sequence and disassembled_center_ID[1] == f"{construct_generation_specification}-{center}":
                            scorable_constructs.append((individual,disassembled_center_ID[0], disassembled_center_ID[1]))


def score_relative_sequences(execution_id, task_queue, return_queue):
    # Preapring generation level variables
    proceses_done = [False, False]
    available_reference_constructs = []
    individuals = uf.load_individuals(execution_id)
    relative_constructs_to_score = dict.fromkeys(individuals, [])
    
    while True:

        scorable_constructs = []
        get_new_centers_to_treat(task_queue, available_reference_constructs, relative_constructs_to_score, scorable_constructs, proceses_done)
        score_centers(execution_id, scorable_constructs, return_queue)

        if proceses_done[0] and proceses_done[1]:
            return_queue.put((PROCESS_NUMBER, "Done"))
            text_update = f"Fragility scoring done"
            uf.dump_process_specific_log(execution_id, PROCESS_NUMBER, text_update)
            break       


def run_process(execution_id, task_queue, return_queue, error_queue):
    try:
       score_relative_sequences(execution_id, task_queue, return_queue)
    except Exception as e:
        error_queue.put((PROCESS_NUMBER, str(e)))