import os
import sys
import traceback

import UtilitiesVariables as uv
import UtilitiesFunction as uf

PROCESS_NUMBER = 1

def create_windows(arm_starts, sequence, complementary_sequence, arm_size):
    """Creating standard construct windows, that contain the sequences of the different arms"""
    
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


def arm_4_starts_for_fixed_arm_3(arm_3_start, sequence_length, arm_size, loop_2_maximal_size, loop_2_step_size):
    """In a string of given size with fixed arm 2 position get the predictable amount of arm 3 positions"""
    arm_4_starts = list(
        range(arm_3_start + arm_size,
              min(sequence_length + 1 - arm_size, arm_3_start + arm_size + loop_2_maximal_size + 1),
              loop_2_step_size
            ) 
    )
    return arm_4_starts


def arm_3_starts_for_fixed_arm_2(arm_2_start, sequence_length, arm_size, loop_1_minimal_size, loop_1_step_size):
    """In a string of given size with fixed arm 2 position get the predictable amount of arm 3 positions"""
    arm_3_starts = list(
        range(arm_2_start + arm_size + loop_1_minimal_size,
              sequence_length + 1 - arm_size * 2,
              loop_1_step_size
            ) 
    )
    return arm_3_starts


def find_possible_centers(sequence_length, arm_size, loop_1_minimal_size, center_step_size):
    """In a string of given size get the predictable amount of centers"""
    centers = list(
        range(arm_size,
              sequence_length - arm_size * 3 - loop_1_minimal_size,
              center_step_size
            ) 
    )
    return centers


def arms_from_center(center, sequence_coordinates, arm_size):
    """Get coordinates of construct relative to reference sequence from coordinates relative to subsequence and calculate arm 1 and 2 position"""
    center_coordinates = uf.get_reference_coordinates(center, sequence_coordinates)
    arm_1_start = center - arm_size
    arm_1_start_coordinates = uf.get_reference_coordinates(arm_1_start, sequence_coordinates)
    arm_2_start = center + 1
    arm_2_start_coordinates = uf.get_reference_coordinates(arm_2_start, sequence_coordinates)
    
    return center_coordinates, arm_1_start, arm_1_start_coordinates, arm_2_start, arm_2_start_coordinates


def constructs_from_reference_sequence(instructions, return_queue):
    """Generates constructs from a given reference sequence"""

    # Preparing Execution associated variables
    construct_generation_specification_ID = uf.form_construct_generation_specification_ID(instructions[uv.CONSTRUCT_GENSPECS_KEY])
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
    sequence_ID = uf.form_reference_sequence_ID(reference_sequence_name, subsequence_name)
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
        center_ID = uf.form_center_ID(sequence_ID, construct_generation_specification_ID, center)
        construct_file_path = f"{sequence_construct_folder_path}{center_ID}-CF.csv"
        center_coordinates, arm_1_start, arm_1_start_coordinates, arm_2_start, arm_2_start_coordinates = arms_from_center(center, sequence_coordinates, arm_size)
        
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
            arm_3_start_coordinates = uf.get_reference_coordinates(arm_3_start, sequence_coordinates)
                
            # Identifying potential arm 4 starts
            arm_4_starts = arm_4_starts_for_fixed_arm_3(arm_3_start, sequence_length, arm_size, loop_2_maximal_size, loop_2_step_size)
                
            for arm_4_start in arm_4_starts:
                
                # Preparing arm_4 related variables
                arm_4_start_coordinates = uf.get_reference_coordinates(arm_4_start, sequence_coordinates)
                    
                # Outputing information to construct file
                construct_ID = uf.form_construct_ID(center_ID, arm_3_start, arm_4_start)
                windows = create_windows([arm_1_start, arm_2_start, arm_3_start, arm_4_start], sequence, complementary_sequence, arm_size)
                uf.dump_construct_file_line(
                    construct_file_path,
                    [
                        construct_ID, center_coordinates, arm_1_start_coordinates, arm_2_start_coordinates, arm_3_start_coordinates, arm_4_start_coordinates,
                        windows[0], windows[1], windows[2], windows[3], windows[4], windows[5]
                    ]
                )
            
        # All constructs for this center are generated we can thus pass the center to the next processes
        return_queue.put((PROCESS_NUMBER, center_ID))
        
    return_queue.put((PROCESS_NUMBER, uv.DONE))
            

def run_process(instructions, task_queue, return_queue, error_queue):
    """Permits running process from controller and handling error catching"""
    try:
        constructs_from_reference_sequence(instructions, return_queue)
    except Exception as error:
        excecution_information = sys.exc_info()
        formatted_exception =  traceback.format_exception( *excecution_information)
        error_queue.put((PROCESS_NUMBER, [error, formatted_exception]))