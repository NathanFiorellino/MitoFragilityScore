import os
import traceback

import UtilitiesVariables as uv
import UtilitiesFunction as uf

PROCESS_NUMBER = 1

def create_windows(arm_starts, sequence, complementary_sequence, arm_size):
    
    arm_1_sequence = sequence[arm_starts[0] : arm_starts[0] + arm_size]
    arm_2_sequence = complementary_sequence[arm_starts[1] : arm_starts[1] + arm_size]
    arm_3_sequence = complementary_sequence[arm_starts[2] : arm_starts[2] + arm_size]
    arm_4_sequence = complementary_sequence[arm_starts[3] : arm_starts[3] + arm_size]
    
    window_1 = arm_2_sequence[::-1]
    window_2 = arm_3_sequence
    
    window_3 = arm_1_sequence
    window_4 = arm_4_sequence
    
    window_5 = window_1 + "NNN" + window_3
    window_6 = window_2 + "NNN" + window_4
    
    return [window_1, window_2, window_3, window_4, window_5, window_6]


def find_possible_centers(sequence_length, arm_size, loop_1_minimal_size, center_step_size):
    centers = list(
        range(arm_size,
              sequence_length - arm_size * 3 - loop_1_minimal_size,
              center_step_size
            ) 
    )
    return centers


def arm_3_starts_for_fixed_arm_2(arm_2_start, sequence_length, arm_size, loop_1_minimal_size, loop_1_step_size):
    arm_3_starts = list(
        range(arm_2_start + arm_size + loop_1_minimal_size,
              sequence_length + 1 - arm_size * 2,
              loop_1_step_size
            ) 
    )
    return arm_3_starts


def arm_4_starts_for_fixed_arm_3(arm_3_start, sequence_length, arm_size, loop_2_maximal_size, loop_2_step_size):
    arm_4_starts = list(
        range(arm_3_start + arm_size,
              min(sequence_length + 1 - arm_size, arm_3_start + arm_size + loop_2_maximal_size + 1),
              loop_2_step_size
            ) 
    )
    return arm_4_starts


def arms_from_center(center, sequence_coordinates, arm_size):
    
    initial_center = uf.get_initial_coordinates(center, sequence_coordinates)
    arm_1_start = center - arm_size
    initial_arm_1_start = uf.get_initial_coordinates(arm_1_start, sequence_coordinates)
    arm_2_start = center + 1
    initial_arm_2_start = uf.get_initial_coordinates(arm_2_start, sequence_coordinates)
    
    return initial_center, arm_1_start, initial_arm_1_start, arm_2_start, initial_arm_2_start


def constructs_from_reference_sequence(execution_id, instructions, return_queue):
    
    # Preparing Execution associated variables
    construct_generation_specification_ID = uf.form_construct_generation_specification_id(instructions[uv.CONSTRUCT_GENSPECS_KEY])
    arm_size = instructions[uv.CONSTRUCT_GENSPECS_KEY][uv.ARM_SIZE_KEY]
    center_step_size = instructions[uv.CONSTRUCT_GENSPECS_KEY][uv.CENTER_STEP_SIZE_KEY]
    loop_1_step_size = instructions[uv.CONSTRUCT_GENSPECS_KEY][uv.LOOP_1_STEP_SIZE_KEY]
    loop_2_step_size = instructions[uv.CONSTRUCT_GENSPECS_KEY][uv.LOOP_2_STEP_SIZE_KEY]
    loop_1_minimal_size = instructions[uv.CONSTRUCT_GENSPECS_KEY][uv.LOOP_1_MINIMAL_SIZE_KEY]
    loop_2_maximal_size = instructions[uv.CONSTRUCT_GENSPECS_KEY][uv.LOOP_2_MAXIMAL_SIZE_KEY]
        
    # Unpacking reference sequence as given in the settings by the user
    reference_sequence = instructions[uv.REFERENCE_SEQUENCE_KEY]
    reference_sequence_name = reference_sequence[0]
    subsequence_name = reference_sequence[1]
        
    # Preparing sequence associated variables
    sequence_ID = uf.form_reference_sequence_id(reference_sequence_name, subsequence_name)
    sequence_construct_folder_path = f"{uv.CONSTRUCT_FOLDER}{sequence_ID}{os.sep}"
    if not os.path.isdir(sequence_construct_folder_path):
        os.mkdir(sequence_construct_folder_path)
            
    # Gathering sequence information
    sequence, complementary_sequence, sequence_coordinates = uf.load_reference_sequence(reference_sequence_name, subsequence_name)
    sequence_length = len(sequence)
        
    # Identifying all possible centers
    possible_centers = find_possible_centers(sequence_length, arm_size, loop_1_minimal_size, center_step_size)
        
    for i, center in enumerate(possible_centers):
            
        # Preparing center associated variables
        center_ID = uf.form_center_id(sequence_ID, construct_generation_specification_ID, center)
        construct_file_path = f"{sequence_construct_folder_path}{center_ID}-CF.csv"
        initial_center, arm_1_start, initial_arm_1_start, arm_2_start, initial_arm_2_start = arms_from_center(center, sequence_coordinates, arm_size)
            
        # User progression update
        text_update = f"Generating Constructs >> {center_ID} >> Center {i + 1} of {len(possible_centers)} in sequence {sequence_ID}"
        uf.dump_process_specific_log(execution_id, PROCESS_NUMBER, text_update)
        
        # Verifying that constructs are not already identified, if there are we can pass the center to the next processes
        if os.path.isfile(construct_file_path):
            return_queue.put((PROCESS_NUMBER, center_ID))
            continue
            
        # Preparing construct file
        uf.create_construct_file(construct_file_path)
            
        # Identifying potential arm 3 starts
        arm_3_starts = arm_3_starts_for_fixed_arm_2(arm_2_start, sequence_length, arm_size, loop_1_minimal_size, loop_1_step_size)

        for arm_3_start in arm_3_starts:
                
            # Preparing arm_3 related variables
            initial_arm_3_start = uf.get_initial_coordinates(arm_3_start, sequence_coordinates)
                
            # Identifying potential arm 4 starts
            arm_4_starts = arm_4_starts_for_fixed_arm_3(arm_3_start, sequence_length, arm_size, loop_2_maximal_size, loop_2_step_size)
                
            for arm_4_start in arm_4_starts:
                
                # Preparing arm_4 related variables
                initial_arm_4_start = uf.get_initial_coordinates(arm_4_start, sequence_coordinates)
                    
                # Outputing information to construct file
                construct_id = uf.form_construct_id(center_ID, arm_3_start, arm_4_start)
                windows = create_windows([arm_1_start, arm_2_start, arm_3_start, arm_4_start], sequence, complementary_sequence, arm_size)
                uf.dump_construct_file_line(
                    construct_file_path,
                    [
                        construct_id, initial_center, initial_arm_1_start, initial_arm_2_start, initial_arm_3_start, initial_arm_4_start,
                        windows[0], windows[1], windows[2], windows[3], windows[4], windows[5]
                    ]
                )
            
        # All constructs for this center are generated we can thus pass the center to the next processes
        return_queue.put((PROCESS_NUMBER, center_ID))
        
    return_queue.put((PROCESS_NUMBER, "Done"))
    text_update = f"Generating reference constructs done"
    uf.dump_process_specific_log(execution_id, PROCESS_NUMBER, text_update)
            

def run_process(execution_id, _ , return_queue, error_queue):
    try:
        instructions = uf.load_instructions(PROCESS_NUMBER, execution_id)
        constructs_from_reference_sequence(execution_id, instructions, return_queue)
        
    except Exception as e:
        error_queue.put((PROCESS_NUMBER, traceback.format_exc()))