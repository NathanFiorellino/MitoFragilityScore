import traceback
import json
import csv

import Bio.Align as ba

import UtilitiesVariables as uv
import UtilitiesFunction as uf

PROCESS_NUMBER = 3

MAX_CHAR = 199
OVERLAP_LENGTH = 30


def variants_mergeable(current_variant, next_variant, reference_sequence):
    
    if current_variant[1] == next_variant[1]:
        return False
    
    if current_variant[1] == "S" or current_variant[1] == "S":
        return False
    
    if current_variant[1] == "D":
        sequence_between_variants = reference_sequence[current_variant[0] : next_variant[0] - 1]
        
    else:
        sequence_between_variants = reference_sequence[current_variant[0] : next_variant[0]]
        
    bases = list(set([*sequence_between_variants]))
    
    if len(bases)> 1:
        return False
    
    if not len(bases) == 0 and current_variant[1] == "D" and (reference_sequence[current_variant[0] - 1] != bases[0] and next_variant[2] != bases[0]):
        return False
    
    if  not len(bases) == 0 and  next_variant[1] == "D" and (reference_sequence[next_variant[0] -1] != bases[0] and current_variant[2] != bases[0]):
        return False
    
    return True


def merge_variant_pair(current_variant, next_variant, reference_sequence):
    
    if current_variant[1] == "D":
        sequence_between_variants = reference_sequence[current_variant[0] : next_variant[0] - 1]
    else:
        sequence_between_variants = reference_sequence[current_variant[0] : next_variant[0]]
    
    bases = list(set([*sequence_between_variants]))
    
    if len(bases) == 0 and current_variant[1] == "D":
        bases = [next_variant[2]]
    
    if len(bases) == 0 and next_variant[1] == "D":
        bases = [current_variant[2]]
    
    if current_variant[1] == "D" and next_variant[2] == bases[0]:
        current_variant = [current_variant[0], "S", bases[0]]
    elif current_variant[1] == "D" and next_variant[2] != bases[0]:
        current_variant = [next_variant[0] - 1, "S", next_variant[2]]
    elif next_variant[1] == "D" and current_variant[2] == bases[0]:
        current_variant = [next_variant[0], "S", bases[0]]
    elif next_variant[1] == "D" and current_variant[2] != bases[0]:
        current_variant = [current_variant[0], "S", current_variant[2]]
        
    return current_variant


def merge_variants(variants, reference_sequence):
    result = []
    i = 0

    while i < len(variants):
        current_variant = variants[i]
        next_variant_index = i + 1
        next_index = i
        
        while next_variant_index < len(variants) and variants[next_variant_index][0] - current_variant[0] < 10:
            if variants_mergeable(current_variant, variants[next_variant_index], reference_sequence):
                current_variant = merge_variant_pair(current_variant, variants[next_variant_index], reference_sequence)
                next_index = next_variant_index
            next_variant_index += 1
            
        result.append(current_variant)
        i = next_index + 1

    return result


def compare_subsequences(reference_sequence, individual_sequence):
    aligner = ba.PairwiseAligner()

    alignments = aligner.align(reference_sequence, individual_sequence)

    best_alignment = alignments[0]
    relative_sequence = []
    
    reference_coordinates_adjustement = 0
    
    for i, (ref_base, rel_base) in enumerate(zip(best_alignment[0], best_alignment[1])):
        if ref_base != rel_base:
            if ref_base == '-':
                relative_sequence.append([i + 1 - reference_coordinates_adjustement, 'I', rel_base])
                reference_coordinates_adjustement += 1
            elif rel_base == '-':
                relative_sequence.append([i + 1 - reference_coordinates_adjustement, 'D'])
            else:
                relative_sequence.append([i + 1 - reference_coordinates_adjustement, 'S', rel_base])

    return relative_sequence


def relative_sequence_from_fasta(file_path, reference_sequence_name, reference_sequence_information):
    
    # Load sequence
    reference_sequence = uf.load_one_sequence_fasta(f"{uv.SEQUENCE_FOLDER}{reference_sequence_information[reference_sequence_name][uv.PATH]}")
    
    # Load individual sequence
    individual_sequence = uf.load_one_sequence_fasta(f"{uv.INDIVIDUALS_FOLDER}{file_path}")

    relative_sequence = compare_subsequences(reference_sequence, individual_sequence)
    relative_sequence = merge_variants(relative_sequence, reference_sequence)
    
    return relative_sequence


def relative_sequence_from_csv(file_path):
    with open(f"{uv.INDIVIDUALS_FOLDER}{file_path}", "r") as file:
        reader = csv.reader(file)
        relative_sequence = list(reader)
    return relative_sequence


def relative_sequence_generation(return_queue, execution_ID):
    # Gathering individuals
    individuals = uf.load_individuals(execution_ID)
    
    # Loading individuals information
    with open(uv.INDIVIDUALS_INFORMATION_PATH, "r") as file:
        individuals_information = json.load(file)
    
    for individual_ID in individuals:
        
        reference_sequence_name = individuals_information[individual_ID][0]
        file_path = individuals_information[individual_ID][1]
    
        # Load sequence information
        with open(uv.REFERENCE_SEQUENCE_INFORMATION_PATH, "r") as file:
            reference_sequence_information = json.load(file)
        
        if ".vcf" in file_path:
            #relative_sequence = relative_sequence_from_vcf(file_path)
            raise Exception(f"Error, Format not supported, In: Relative Sequence generation, Individual {individual_ID}, file is not  .csv .fasta") 
        elif ".fasta" in file_path:
            relative_sequence = relative_sequence_from_fasta(file_path, reference_sequence_name, reference_sequence_information)
        elif ".csv":
            relative_sequence = relative_sequence_from_csv(file_path)
        else:
            raise Exception(f"Error, Format not supported, In: Relative Sequence generation, Individual {individual_ID}, file is not .csv or .fasta")    

        uf.dump_relative_sequence(individual_ID, relative_sequence)
        
        return_queue.put((PROCESS_NUMBER, individual_ID))
            
    return_queue.put((PROCESS_NUMBER, "Done"))
    text_update = f"Generating relative sequences done"
    uf.dump_process_specific_log(execution_ID, PROCESS_NUMBER, text_update)


def run_process(execution_ID, _, return_queue, error_queue):
    try:
        relative_sequence_generation(return_queue, execution_ID)
        
    except Exception as e:
        error_queue.put((PROCESS_NUMBER, traceback.format_exc()))