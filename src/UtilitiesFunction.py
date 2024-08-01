import os
import json
import csv

import UtilitiesVariables as uv

### Hardcoded paths
def instructions_path(execution_ID):
    """Standard function to generate patth to instructions"""
    return(f"{uv.EXECUTION_FOLDER}{execution_ID}{os.sep}{execution_ID}-instructions.json")


### Standardised file creation
def create_instructions(execution_ID, settings):
    """Standard function for creating instruction file"""
    with open(instructions_path(execution_ID), "w") as file:
        json.dump(settings, file)


def create_json_log(json_log_path):
    """Function that creates the empty json log"""
    with open(json_log_path, "w") as file:
        json.dump(uv.PROCESS_LOG, file)


def create_construct_file(construct_file_path):
    """Function that creates the empty construct file"""
    first_line = (
        ["ConstructID", "CenterPosition", "Arm1Start", "Arm2Start", " Arm3Start", "Arm4Start", "SequenceWindow1",
        "SequenceWindow2", "SequenceWindow3", "SequenceWindow4", "SequenceWindow5", "SequenceWindow6"]
    )
    with open(construct_file_path, "a", newline='') as file:
        csv.writer(file).writerow(first_line)


def create_energy_file(energy_file_path):
    """Function that creates the empty energy file"""
    first_line = (
        ["ConstructID", "EnergyLeft", "EnergyRight", "Energy"]
    )
    with open(energy_file_path, "a", newline='') as file:
        csv.writer(file).writerow(first_line)


def create_fragility_file(fragility_file_path):
    """Function that creates the empty fragility file"""
    first_line = (
        ["ConstructID", "ScoreLeft", "ScoreRight", "DifferenceEnergy","ContainsVariant"]
    )
    with open(fragility_file_path, "a", newline='') as file:
        csv.writer(file).writerow(first_line)


### Standardised file dumping
def dump_log(log_file_path, category, key, value):
    """Standard function for adding entries to the json log"""
    with open(log_file_path, "r") as file:
        log = json.load(file)
    
    log[category][key] = value

    with open(log_file_path, "w") as file:
        json.dump(log, file) 


def dump_construct_file_line(construct_file_path, line):
    """Standard function for adding entries to the construct file"""
    with open(construct_file_path, "a", newline='') as file:
        csv.writer(file).writerow(line)


def dump_energy_file_line(energy_file_path, line):
    """Standard function for adding entries to the energy file"""
    with open(energy_file_path, "a", newline='') as file:
        csv.writer(file).writerow(line)


def dump_fragility_file_line(fragility_file_path, line):
    """Standard function for adding entries to the fragility file"""
    with open(fragility_file_path, "a", newline='') as file:
        csv.writer(file).writerow(line)


def dump_relative_sequence(individual_ID, relative_sequence):
    """Standard function for populating a relative sequence file"""
    with open(f"{uv.SEQUENCE_FOLDER}Relative{os.sep}{individual_ID}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        for row in relative_sequence:
            writer.writerow(row)


### Standardised file loading
def load_fasta(file_path):
    """Standard function for loading onse sequence fasta file"""
    with open(file_path, "r") as fasta_file:
        lines = fasta_file.readlines()
    
    sequence =  ''.join(lines[1:]).replace("\n", "")
    
    return sequence


def load_instructions_base(execution_ID):
    """Standard function for loading instruction file"""
    with open(instructions_path(execution_ID), "r") as file:
        instructions = json.load(file)
    return instructions
      

def load_reference_sequence(sequence_name, subsequence_name):
    """Finding location of reference sequence file and reading subsequence"""
    # Finding and loading reference sequence
    with open(uv.REFERENCE_SEQUENCE_INFORMATION_PATH, "r") as file:
        reference_sequence_information = json.load(file)
    sequence = load_fasta(f"{uv.SEQUENCE_FOLDER}{reference_sequence_information[sequence_name][uv.PATH]}")
    
    # Loading instructions to load only subsequence of reference
    subsequence_instruction = reference_sequence_information[sequence_name][uv.SUBSEQUENCES][subsequence_name]
    initial_sequence_lengh = len(sequence)
    
    if len(subsequence_instruction) == 2 and subsequence_instruction[0] < subsequence_instruction[1]:
        # If the subsequence does not pass through the end of the circular sequence all coordinates need simply to be shifted
        sequence = sequence[subsequence_instruction[0] - 1 : subsequence_instruction[1] - 1]
        sequence_coordinates = [subsequence_instruction[0]]
        
    elif len(subsequence_instruction) == 2 and subsequence_instruction[0] > subsequence_instruction[1]:
        # If the subsequences does pass through the end of the circular sequence we need to handle coordinates differently according on what part of the chromosome the bp is situated
        sequence = sequence[subsequence_instruction[0] - 1 :] + sequence[: subsequence_instruction[1]  - 1]
        sequence_coordinates = [initial_sequence_lengh - subsequence_instruction[0], subsequence_instruction[0]]
        
    complementary_sequence = ''.join(uv.COMPLEMENTARY_BASES[nucleic_acid] for nucleic_acid in sequence)

    return sequence, complementary_sequence, sequence_coordinates # Note: sequence corresponds to light chain and complementary to heavy chain


def load_relative_sequence(relative_sequence_path, sequence_coordinates):
    """Reading subsequence of a located relative sequence"""
    
    relative_sequence = []
    
    with open(relative_sequence_path, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            position = int(row[0])
            # Correcting the variant position based on the subsequence instructions
            if len(sequence_coordinates) == 1:
                corrected_index = position - sequence_coordinates[0]
            else:
                if position < sequence_coordinates[1]:
                    corrected_index = position + sequence_coordinates[0]
                else:
                    corrected_index = position - sequence_coordinates[1]
                    
            # Gathering the variant
            if len(row) ==  3:
                relative_sequence.append((corrected_index, row[1], row[2]))
            elif len(row)== 2:
                relative_sequence.append((corrected_index, row[1]))
    return relative_sequence


### Instructions preparation
def add_individuals_to_settings(settings):
    """From settings and group file get individuals to launch and add them to the settings"""
    with open(uv.INDIVIDUALS_GROUPS_PATH, "r") as file:
        groups = json.load(file)
    settings[uv.INDIVIDUALS_KEY]  = groups[settings[uv.INDIVIDUALS_GROUP_KEY]]


### Forming IDs
def form_reference_sequence_ID(reference_sequence_name, subsequence_name):
    """Forms the standard reference sequence ID from the given instructions"""
    # Template SEQ-[Official_Name]-[SubSequence_Name]
    return f"{uv.SEQUENCE_ID_SEPARATOR}-{reference_sequence_name}-{subsequence_name}"


def form_relative_sequence_ID(reference_sequence_ID, individual_ID):
    """Forms the standard relative sequence ID from the given instructions"""
    # Template [RefSeqID]-[Individual_Identifier]
    return f"{reference_sequence_ID}-{individual_ID}"


def form_construct_generation_specification_ID(construct_generation_specifications):
    """Forms the standard construct genreration specification ID from the given specifications"""
    # Template CGS-[Center_Step_Size]-[Loop_1_Step_Size]-[Loop_2_Step_Size]-[Loop_1_Minimal_Size]-[Loop_2_Maximal_Size]-[Arm_Size]
    return ( 
        f"{uv.CONSTRUCT_GENSPECS_ID_SEPARATOR}-{construct_generation_specifications[uv.CENTER_STEP_SIZE_KEY]}"
        + f"-{construct_generation_specifications[uv.LOOP_1_STEP_SIZE_KEY]}-{construct_generation_specifications[uv.LOOP_2_STEP_SIZE_KEY]}"
        + f"-{construct_generation_specifications[uv.LOOP_1_MINIMAL_SIZE_KEY]}-{construct_generation_specifications[uv.LOOP_2_MAXIMAL_SIZE_KEY]}"
        + f"-{construct_generation_specifications[uv.ARM_SIZE_KEY]}"
    )


def form_center_ID(sequence_ID, construct_generation_specification_ID, center):
    """Forms the standard center ID from the given instructions"""
    # Template RefSeqID-ConstructGenSpecsID-CEN-[center]
    return f"{sequence_ID}-{construct_generation_specification_ID}-{uv.CENTER_ID_SEPARATOR}-{center}"


def form_construct_ID(center_ID, arm_3_start, arm_4_start):
    """Forms the standard construct ID from the given instructions"""
    # Template CenterID-CON-[arm_3_start]-[arm_4_start]
    return f"{center_ID}-{uv.CONSTRUCT_ID_SEPARATOR}-{arm_3_start}-{arm_4_start}"


### Gathering information from IDs
def reference_sequence_name_from_ID(ID):
    """Takes any ID as input and finds reference sequence name"""
    return ID.split('-')[1]

def subsequence_name_from_ID(ID):
    """Takes any ID as input and finds subsequence name"""
    return ID.split('-')[2]

def individual_name_from_ID(ID):
    """Takes any ID as input and finds individuale name"""
    return ID.split('-')[3]


def reference_sequence_ID_from_ID(ID, is_reference):
    """Takes any ID as input and finds reference sequence ID"""
    if is_reference:
        reference_sequence = ID[ID.find(f"{uv.SEQUENCE_ID_SEPARATOR}"):ID.find(f"-{uv.CONSTRUCT_GENSPECS_ID_SEPARATOR}")]
    else:
        reference_sequence = f"{ID.split('-')[0]}-{ID.split('-')[1]}-{ID.split('-')[2]}"
    return reference_sequence


def sequence_ID_from_ID(ID):
    """Takes any ID as input and finds reference or relative sequence ID"""
    sequence_ID = ID[ID.find(f"{uv.SEQUENCE_ID_SEPARATOR}"):ID.find(f"-{uv.CONSTRUCT_GENSPECS_ID_SEPARATOR}")]
    return sequence_ID


def center_from_ID(ID, is_center_ID):
    """Takes any ID as input and finds center."""
    if is_center_ID:
        center = ID[ID.find(f"{uv.CENTER_ID_SEPARATOR}"):]
    else:
        center = ID[ID.find(f"{uv.CENTER_ID_SEPARATOR}"):ID.find(f"-{uv.CONSTRUCT_ID_SEPARATOR}")]
    return center


def construct_generation_specification_from_ID(ID):
    """Takes any ID as input and finds CGS."""
    return ID[ID.find(f"{uv.CONSTRUCT_GENSPECS_ID_SEPARATOR}"):ID.find(f"-{uv.CENTER_ID_SEPARATOR}")]


def contruct_name_from_ID(ID):
    """Takes any ID as input and finds construct name."""
    return ID[ID.find(f"{uv.CONSTRUCT_ID_SEPARATOR}"):]


### Squences coordinates
def get_reference_coordinates(bp, sequence_coordinates):
    """Translates relative coordinates in the subsequence to coordinates inside the reference sequence (to keep biological relevance)"""
    if len(sequence_coordinates) == 1:
        initial_coordinates = bp + sequence_coordinates[0]
    else:
        if bp < sequence_coordinates[0]:
            initial_coordinates = bp + sequence_coordinates[1]
        else:
            initial_coordinates = bp - sequence_coordinates[0]
        
    return initial_coordinates

### Score fragility
def score_fragility(reference_energy, relative_energy):
    """Standard fragility scoring"""
    return reference_energy - relative_energy

def generate_base_score():
    """Standard base score"""
    return [0, 0, 0, False]