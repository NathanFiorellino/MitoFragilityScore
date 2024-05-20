
import os
import traceback
import csv

import UtilitiesVariables as uv
import UtilitiesFunction as uf

PROCESS_NUMBER = 4


def add_variants_to_sequence(sequence, sequence_variants, complementary):
    modified_sequence = list(sequence)
    sequence_adjustment = 0
    for sequence_variant in sequence_variants:
        index = sequence_variant[0]
        operation = sequence_variant[1]
        index += sequence_adjustment
        
        # Substitution, simple assigning character to the correct position
        if operation == "S":
            substituted_base = sequence_variant[2]
            if complementary:
                substituted_base = uv.COMPLEMENTARY_BASES[substituted_base]
            modified_sequence[index] = substituted_base
        # Insertion, need to change adjustement so that following variants are placed at the correct emplacement
        if operation == "I":
            inserted_base = sequence_variant[2]
            if complementary:
                inserted_base = uv.COMPLEMENTARY_BASES[inserted_base]
            modified_sequence.insert(index, inserted_base)
            sequence_adjustment += 1
            
        # deletion, need to change adjustement so that following variants are placed at the correct emplacement
        if operation == "D":
            del modified_sequence[index]
            sequence_adjustment -= 1
    
    modified_sequence = "".join(modified_sequence)
    
    return modified_sequence


def create_windows_from_relative_sequence(relative_sequence, arm_starts, sequence, complementary_sequence, arm_size):
    arm_variants = {0: [], 1: [] , 2: [], 3: []}
    
    for variant in relative_sequence:
        if variant == "Overshot":
            continue
        for arm in range(4):
            if arm_starts[arm]<= variant[0] and variant[0] < arm_starts[arm] + arm_size:
                arm_variants[arm].append((variant))
    
    #Preparing whole sequence to be modified
    sequence_variants = arm_variants[0]
    complementary_sequence_variants = arm_variants[1] + arm_variants[2] + arm_variants[3]
    
    # Modifing Light strand
    sequence = add_variants_to_sequence(sequence, sequence_variants, False)
    # Modifying hevy strand
    complementary_sequence = add_variants_to_sequence(complementary_sequence, complementary_sequence_variants, True)
    
    # Retrieving arms
    arm_1_sequence = sequence[arm_starts[0] : arm_starts[0] + arm_size]
    arm_2_sequence = complementary_sequence[arm_starts[1] : arm_starts[1] + arm_size]
    arm_3_sequence = complementary_sequence[arm_starts[2] : arm_starts[2] + arm_size]
    arm_4_sequence = complementary_sequence[arm_starts[3] : arm_starts[3] + arm_size]
    
    # Creating Windows
    window_1 = arm_2_sequence[::-1]
    window_2 = arm_3_sequence
    window_3 = arm_1_sequence
    window_4 = arm_4_sequence
    window_5 = window_1 + "NNN" + window_3
    window_6 = window_2 + "NNN" + window_4
    
    return window_1, window_2, window_3, window_4, window_5, window_6


def prepare_individuals(individuals, reference_sequence_ID, construct_generation_specification_id, relative_sequence_information, center, return_queue, execution_id):
    individuals_variables = {}
    
    for individual_ID in individuals:
        
        relative_sequence_ID = uf.form_relative_sequence_id(reference_sequence_ID, individual_ID)
        
        new_center_id = uf.form_center_id(relative_sequence_ID, construct_generation_specification_id, center)
        new_construct_file_path = f"{uv.CONSTRUCT_FOLDER}{relative_sequence_ID}{os.sep}{new_center_id}-CF.csv"
        relative_sequence = relative_sequence_information[relative_sequence_ID]
            
        # Verifying that constructs are not already generated
        if os.path.isfile(new_construct_file_path):
            return_queue.put((PROCESS_NUMBER, new_center_id))
            continue
        
        uf.create_construct_file(new_construct_file_path)
        
        individuals_variables[relative_sequence_ID] = [new_center_id, new_construct_file_path, relative_sequence]
    return individuals_variables
        

def create_construct_directories(new_pairs_to_treat, reference_sequence_ID):
    individuals = []
    for individuals_for_center in new_pairs_to_treat.values():
        individuals.extend([individual for individual in individuals_for_center])
    
    for individual_ID in individuals:
        relative_sequence_ID = uf.form_relative_sequence_id(reference_sequence_ID, individual_ID)
        
        if not os.path.isdir(f"{uv.CONSTRUCT_FOLDER}{relative_sequence_ID}"):
            os.mkdir(f"{uv.CONSTRUCT_FOLDER}{relative_sequence_ID}")


def load_relative_sequences(new_pairs_to_treat, reference_sequence_ID, reference_sequences_coordinates):
    
    relative_sequence_informations = {}
    individuals = []
    for individuals_for_center in new_pairs_to_treat.values():
        individuals.extend([individual for individual in individuals_for_center])
    
    # Removing duplicates    
    individuals = list(set(individuals))
    
    for individual_ID in individuals:
        relative_sequence_ID = uf.form_relative_sequence_id(reference_sequence_ID, individual_ID)
        relative_sequence_informations[relative_sequence_ID] = uf.load_relative_sequence(f"{uv.SEQUENCE_FOLDER}Relative{os.sep}{individual_ID}.csv", reference_sequences_coordinates)
    
    return  relative_sequence_informations



def generate_relative_sequence_constructs(execution_id, new_pairs_to_treat, instructions, return_queue):
        
    # Preparing generation level variables
    construct_generation_specification_id = uf.form_construct_generation_specification_id(instructions[uv.CONSTRUCT_GENSPECS_KEY])
    
    reference_sequence_name = instructions[uv.REFERENCE_SEQUENCE_KEY][0]
    subsequence_name = instructions[uv.REFERENCE_SEQUENCE_KEY][1]
    sequence, complementary_sequence, reference_sequences_coordinates = uf.load_reference_sequence(reference_sequence_name, subsequence_name)
    reference_sequence_ID = uf.form_reference_sequence_id(reference_sequence_name, subsequence_name)
    
    relative_sequence_information = load_relative_sequences(new_pairs_to_treat, reference_sequence_ID, reference_sequences_coordinates)
    
    create_construct_directories(new_pairs_to_treat, reference_sequence_ID)
    
    arm_size = instructions[uv.CONSTRUCT_GENSPECS_KEY][uv.ARM_SIZE_KEY]
    
    for center_ID, individuals in new_pairs_to_treat.items():
        
        # Preparing center level variables
        sequence_construct_folder_path = f"{uv.CONSTRUCT_FOLDER}{reference_sequence_ID}{os.sep}"
        construct_file_path = f"{sequence_construct_folder_path}{center_ID}-CF.csv"
        
        center = int(center_ID.split("-")[-1])
        
        # User progression update
        text_update = f"Generating Constructs for individuals >> {center_ID} >> {individuals} >> in sequence {reference_sequence_ID}"
        uf.dump_process_specific_log(execution_id, PROCESS_NUMBER, text_update)
        
        individuals_variables = prepare_individuals(individuals, reference_sequence_ID, construct_generation_specification_id, relative_sequence_information, center, return_queue, execution_id)
        treated_new_center_IDs = []
        
        with open(construct_file_path, "r") as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                if i == 0:
                    continue
                    
                # Gathering construct defining variables
                construct_id = row[0]
                
                arm_3_start = int(construct_id.split("-")[13])
                arm_4_start = int(construct_id.split("-")[14])
        
                for relative_sequence_ID, variables  in individuals_variables.items():
                    new_center_id = variables[0]
                    new_construct_file_path = variables[1]
                    relative_sequence = variables[2].copy()
                    
                    # Checking if construct needs to be recomputed
                    change_in_arms = False
                    for i, variant in enumerate(relative_sequence):
                        
                        if variant == "Overshot":
                            continue
                        
                        if ( (variant[0] >= center - arm_size and variant[0] < center)
                            or (variant[0] >= center + 1 and variant[0] <= center + arm_size) 
                            or (variant[0] >= arm_3_start and variant[0] < arm_3_start + arm_size)
                            or (variant[0] >= arm_4_start and variant[0] < arm_4_start + arm_size)
                        ):
                        
                            change_in_arms = True
                            break
                        
                        if variant[0] <= center - arm_size:
                            individuals_variables[relative_sequence_ID][2][i] =  "Overshot"
                    
                    if change_in_arms:
                        # Modiyfing windows according to relative sequence
                        new_construct_id = uf.form_construct_id(new_center_id, arm_3_start, arm_4_start)
                        windows = create_windows_from_relative_sequence(relative_sequence, [center - arm_size, center + 1, arm_3_start, arm_4_start], sequence, complementary_sequence, arm_size)
                        uf.dump_construct_file_line(
                            new_construct_file_path, [new_construct_id, row[1] , row[2], row[3], row[4], row[5],
                            windows[0], windows[1], windows[2], windows[3], windows[4], windows[5]]
                        )
        
        treated_new_center_IDs = [individuals_variables[relative_sequence_ID][0] for relative_sequence_ID in individuals_variables]        
        
        for new_center_id in treated_new_center_IDs:
            return_queue.put((PROCESS_NUMBER, new_center_id))


def get_new_pairs_from_new_center(new_pairs, new_center, individuals_to_treat):
        
    for individual_ID in individuals_to_treat:
        
        if new_center in new_pairs:
            new_pairs[new_center].append(individual_ID)
        else:
            new_pairs[new_center] = [individual_ID]


def get_new_pairs_from_new_individual(new_pairs, new_individual, centers_to_treat):
        
    for center_ID in centers_to_treat:
        if center_ID in new_pairs:
            new_pairs[center_ID].append(new_individual)
        else:
            new_pairs[center_ID] = [new_individual]


def get_new_individuals_to_treat(task_queue, individuals_to_treat, centers_to_treat, new_pairs_to_treat, proceses_done):
    
    while not task_queue.empty():
        
        new_task = task_queue.get()
        
        if new_task[0] == 1:
            if new_task[1]== "Done":
                proceses_done[0] = True
            else:
                centers_to_treat.append(new_task[1])
                get_new_pairs_from_new_center(new_pairs_to_treat, new_task[1], individuals_to_treat)
                
        elif new_task[0] == 3:
            if new_task[1]== "Done":
                proceses_done[1] = True
            else:
                individuals_to_treat.append(new_task[1])  
                get_new_pairs_from_new_individual(new_pairs_to_treat, new_task[1], centers_to_treat)
  

def relative_sequence_contruct_generation(execution_id, task_queue, return_queue):
    
    # Preapring generation level variables
    proceses_done = [False, False]
    individuals_to_treat = []
    centers_to_treat = []
    
    # Loading instructions
    instructions = uf.load_instructions(PROCESS_NUMBER, execution_id)
    
    while True:
            
        new_pairs_to_treat = {}
        get_new_individuals_to_treat(task_queue, individuals_to_treat, centers_to_treat, new_pairs_to_treat, proceses_done)
        generate_relative_sequence_constructs(execution_id, new_pairs_to_treat, instructions, return_queue)

        if proceses_done[0] and proceses_done[1]:
            return_queue.put((PROCESS_NUMBER, "Done"))
            text_update = f"Generating relative constructs done"
            uf.dump_process_specific_log(execution_id, PROCESS_NUMBER, text_update)
            break


def run_process(execution_id, task_queue, return_queue, error_queue):
    try:
        relative_sequence_contruct_generation(execution_id, task_queue, return_queue)
    except Exception as e:
        error_queue.put((PROCESS_NUMBER, traceback.format_exc()))