import os
import json
import csv

import UtilitiesVariables as uv

### Hardcoded paths
def process_log_path(execution_ID):
    return f"{uv.EXECUTION_FOLDER}{execution_ID}{os.sep}{execution_ID}-process_log.json"


def instructions_path(execution_ID):
    return(f"{uv.EXECUTION_FOLDER}{execution_ID}{os.sep}{execution_ID}-instructions.json")


def process_instructions_path(process_number, execution_ID):
    return f"{uv.EXECUTION_FOLDER}{execution_ID}{os.sep}{execution_ID}-{uv.PROCESSES[process_number][1]}-instructions.json"


def process_specific_log_path(execution_ID, process_number):
    return f"{uv.EXECUTION_FOLDER}{execution_ID}{os.sep}{execution_ID}-{uv.PROCESSES[process_number][1]}-process_log.txt"


### Standardised file creation
def create_process_instructions(process_number, execution_ID, settings):
    if process_number in [0, 1, 3, 4]:
        with open(process_instructions_path(process_number, execution_ID), "w") as file:
            json.dump(settings, file)


def create_instructions(execution_ID, settings):
    with open(instructions_path(execution_ID), "w") as file:
        json.dump(settings, file)


def create_construct_file(construct_file_path):
    first_line = (
        ["ConstructID", "CenterPosition", "Arm1Start", "Arm2Start", " Arm3Start", "Arm4Start", "SequenceWindow1",
        "SequenceWindow2", "SequenceWindow3", "SequenceWindow4", "SequenceWindow5", "SequenceWindow6"]
    )
    
    with open(construct_file_path, "a", newline='') as file:
        csv.writer(file).writerow(first_line)


def create_energy_file(energy_file_path):
    first_line = (
        ["ConstructID", "EnergyLeft", "EnergyRight", "Energy"]
    )
    
    with open(energy_file_path, "a", newline='') as file:
        csv.writer(file).writerow(first_line)


def create_fragility_file(fragility_file_path):
    first_line = (
        ["ConstructID", "ScoreLeft", "ScoreRight", "DifferenceEnergy","ContainsVariant"]
    )
    
    with open(fragility_file_path, "a", newline='') as file:
        csv.writer(file).writerow(first_line)


### Standardised file dumping
def dump_process_specific_log(execution_id, process_number, text):
    with open(process_specific_log_path(execution_id, process_number), "a") as file:
        file.write(f"{text}\n")      


def dump_construct_file_line(construct_file_path, line):
    with open(construct_file_path, "a", newline='') as file:
        csv.writer(file).writerow(line)


def dump_energy_file_line(energy_file_path, line):
    with open(energy_file_path, "a", newline='') as file:
        csv.writer(file).writerow(line)


def generate_base_score():
    return [0, 0, 0, False]


def dump_fragility_file_line(fragility_file_path, line):
    with open(fragility_file_path, "a", newline='') as file:
        csv.writer(file).writerow(line)


def dump_relative_sequence(individual_ID, relative_sequence):
    with open(f"{uv.SEQUENCE_FOLDER}Relative{os.sep}{individual_ID}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        for row in relative_sequence:
            writer.writerow(row)


### Standardised file loading
def load_one_sequence_fasta(file_path):
    with open(file_path, "r") as fasta_file:
        lines = fasta_file.readlines()
    
    sequence =  ''.join(lines[1:]).replace("\n", "")
    
    return sequence


def load_instructions_base(execution_ID):
    with open(instructions_path(execution_ID), "r") as file:
        instructions = json.load(file)
    return instructions


def infer_individuals(settings):
    # Infer the individuals from the individual group, defined in the group file
    group_name = settings[uv.INDIVIDUALS_GROUP_KEY]
    with open(uv.INDIVIDUALS_GROUPS_PATH, "r") as file:
        groups = json.load(file)
    return groups[group_name]


def load_individuals(execution_ID):
    # Load individuals after they have been added to the instructions
    # Here we simply read the instructions
    instructions = load_instructions_base(execution_ID)
    return instructions[uv.INDIVIDUALS_KEY]


def load_instructions(process_number, execution_ID):
    with open(process_instructions_path(process_number, execution_ID), "r") as file:
        instructions = json.load(file)
    return instructions
      

def load_reference_sequence(sequence_name, subsequence_name):

    with open(uv.REFERENCE_SEQUENCE_INFORMATION_PATH, "r") as file:
        reference_sequence_information = json.load(file)
    
    sequence = load_one_sequence_fasta(f"{uv.SEQUENCE_FOLDER}{reference_sequence_information[sequence_name][uv.PATH]}")
    
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

    return sequence, complementary_sequence, sequence_coordinates # sequence corresponds to light and complementary to heavy


def load_relative_sequence(relative_sequence_path, sequence_coordinates):
    
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


def load_vcf(file_path):
    metadata = {}
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('##'):
                # Parse metadata
                if '=' in line:
                    key, value = line[2:].split('=', 1)
                    metadata[key] = value
            elif line.startswith('#'):
                # Parse column headers
                columns = line[1:].split('\t')
            else:
                # Parse data rows
                fields = line.split('\t')
                record = dict(zip(columns, fields))
                data.append(record)

    return metadata, data


## Standard file deleting
def cleanup_instructions(execution_id):
    for process_number in [0, 1, 3, 4]:
        os.remove(process_instructions_path(process_number, execution_id))


### Forming IDs
def form_reference_sequence_id(reference_sequence_name, subsequence_name):
    return f"{uv.SEQUENCE_ID_SEPARATOR}-{reference_sequence_name}-{subsequence_name}"


def form_relative_sequence_id(reference_sequence_ID, individual_ID):
    return f"{reference_sequence_ID}-{individual_ID}"


def form_construct_generation_specification_id(construct_generation_specifications):
    return ( 
        f"{uv.CONSTRUCT_GENSPECS_ID_SEPARATOR}-{construct_generation_specifications[uv.CENTER_STEP_SIZE_KEY]}"
        + f"-{construct_generation_specifications[uv.LOOP_1_STEP_SIZE_KEY]}-{construct_generation_specifications[uv.LOOP_2_STEP_SIZE_KEY]}"
        + f"-{construct_generation_specifications[uv.LOOP_1_MINIMAL_SIZE_KEY]}-{construct_generation_specifications[uv.LOOP_2_MAXIMAL_SIZE_KEY]}"
        + f"-{construct_generation_specifications[uv.ARM_SIZE_KEY]}"
    )


def form_center_id(sequence_id, construct_generation_specification_id, center):
    return f"{sequence_id}-{construct_generation_specification_id}-{uv.CENTER_ID_SEPARATOR}-{center}"


def form_construct_id(center_id, arm_3_start, arm_4_start):
    return f"{center_id}-{uv.CONSTRUCT_ID_SEPARATOR}-{arm_3_start}-{arm_4_start}"


### Gathering information from ID
def sequence_id_from_center_id(center_id): # TO recycle
    return center_id[: center_id.find(f"-{uv.CONSTRUCT_GENSPECS_ID_SEPARATOR}")]


def subsequence_name_from_sequence_ID(sequence_ID):
    return sequence_ID.split(f"-")[-1]


def sequence_name_from_sequence_ID(sequence_ID):
    return sequence_ID.split('-')[1]


def reference_sequence_from_ID(ID, is_reference):
    if is_reference:
        reference_sequence = ID[ID.find(f"{uv.SEQUENCE_ID_SEPARATOR}"):ID.find(f"-{uv.CONSTRUCT_GENSPECS_ID_SEPARATOR}")]
    else:
        reference_sequence = f"{ID.split('-')[0]}-{ID.split('-')[1]}-{ID.split('-')[2]}"
    return reference_sequence


def individual_from_ID(ID):
    return f"{ID.split('-')[3]}"


def construct_generation_specification_from_ID(ID):
    return ID[ID.find(f"{uv.CONSTRUCT_GENSPECS_ID_SEPARATOR}"):ID.find(f"-{uv.CENTER_ID_SEPARATOR}")]


def center_from_ID(ID, is_center_ID):
    if is_center_ID:
        center = ID[ID.find(f"{uv.CENTER_ID_SEPARATOR}"):]
    else:
        center = ID[ID.find(f"{uv.CENTER_ID_SEPARATOR}"):ID.find(f"-{uv.CONSTRUCT_ID_SEPARATOR}")]
    return center


def contruct_name_from_ID(ID):
    return ID[ID.find(f"{uv.CONSTRUCT_ID_SEPARATOR}"):]


### Squences coordinates
def get_initial_coordinates(bp, sequence_coordinates):
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
    return reference_energy - relative_energy