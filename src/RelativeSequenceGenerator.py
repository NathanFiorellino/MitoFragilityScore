import sys
import json
import csv
import traceback

import Bio.Align as ba

import UtilitiesVariables as uv
import UtilitiesFunction as uf

PROCESS_NUMBER = 3

def variants_mergeable(current_variant, next_variant, reference_sequence):
    """Check if two differences can be merge into one"""
    
    # Mergeable variants are not, by definition, of same type or substitionts
    if current_variant[1] == next_variant[1]:
        return False
    if current_variant[1] == "S" or current_variant[1] == "S":
        return False
    
    # Note : If none of the previous conditions are met, then one variant is a deletion and the other is an insertion.

    # Getting sequence between variants
    if current_variant[1] == "D":
        sequence_between_variants = reference_sequence[current_variant[0] : next_variant[0] - 1]
    else:
        sequence_between_variants = reference_sequence[current_variant[0] : next_variant[0]]
    
    # Getting all bases present between variants
    bases = list(set([*sequence_between_variants]))
    
    # They are mergeable only if there is only one type of base.
    if len(bases)> 1:
        return False
    
    # In the case D-I and if there is at least one bases between the variants, they are mergeable if either
    # the deleted base or the added base are coresponding to the bases in between
    # In this example both variants are mergeable because of the added Guanine.
    # Reference sequence:   TAG-C
    #                       |-|-|
    # Relative sequence:    T-GGC
    # The same goes for the I-D case the same goes :
    # In this example both variants are mergeable because of the added Guanine.
    # Reference sequence:   T-GAC
    #                       |-|-|
    # Relative sequence:    TGG-C

    # If both bases(added and deleted) are not identical to the separting bases, then they are not mergeable
    if  len(bases) == 1 and current_variant[1] == "D" and (reference_sequence[current_variant[0] - 1] != bases[0] and next_variant[2] != bases[0]):
        return False
    
    # If both bases(added and deleted) are not identical to the separting bases, then they are not mergeable
    if  len(bases) == 1 and  next_variant[1] == "D" and (reference_sequence[next_variant[0] -1] != bases[0] and current_variant[2] != bases[0]):
        return False
    
    return True


def merge_variant_pair(current_variant, next_variant, reference_sequence):
    """Merge two variants that have been identified as beeing mergeable"""
    
    # Getting sequence between variants
    if current_variant[1] == "D":
        sequence_between_variants = reference_sequence[current_variant[0] : next_variant[0] - 1]
    else:
        sequence_between_variants = reference_sequence[current_variant[0] : next_variant[0]]

    # Getting all bases present between variants
    bases = list(set([*sequence_between_variants]))
    
    # Handling simple cases where no bases are in between of the two variants
    if len(bases) == 0 and current_variant[1] == "D":
        bases = [next_variant[2]]
    if len(bases) == 0 and next_variant[1] == "D":
        bases = [current_variant[2]]
    
    # Handling different cases, the next variant always gets deleted and the current one is changed to a substitution
    if current_variant[1] == "D" and next_variant[2] == bases[0]:
        current_variant = [current_variant[0], "S", bases[0]]
    elif current_variant[1] == "D" and next_variant[2] != bases[0]:
        current_variant = [next_variant[0] - 1, "S", next_variant[2]]
    elif next_variant[1] == "D" and current_variant[2] == bases[0]:
        current_variant = [next_variant[0], "S", bases[0]]
    elif next_variant[1] == "D" and current_variant[2] != bases[0]:
        current_variant = [current_variant[0], "S", current_variant[2]]
        
    return current_variant


def cleanup_variants(variants, reference_sequence):
    """Cleaning up output of biopython """
    
    # Quick explanation is needed here, the align module of biopython tends to do some errors like this:
    # Reference sequence:   CCT-AT                      TT-CCA
    #                       ||--||       or like this   ||-|-|
    # Relative sequences:   CC-CAT                      TTAC-A
    # In the first case there should not be one deletion and one addition but one substition.
    # In the second case is similar the should be a substitution instead of an addition and a substitution.
    # We try to overcome that issue by identify those variants that should be merged.
    # These are the conditions:
    # - Both variants that are mergeable are either a deletion and an insertion or the other way around
    # - If the distance between the variatns is more than 0 all base pairs in between are identical.

    result = []
    i = 0

    # Comparing each variants to the variants at most 10 bp downstream of them.
    # Why 10 ? The probability that there is a sequence of more than 10 identical
    # basepairs and a variant at exactly the extremity of it seems small enough.
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
    """Align sequences with theb BioAlign library and identify variants"""
    aligner = ba.PairwiseAligner()
    alignments = aligner.align(reference_sequence, individual_sequence)
    best_alignment = alignments[0]

    # If relative and reference base are different handling 1) Insertion (I) 2) Deletion (D) 3) Substitution (S)
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
    """Create relative sequence from a fasta file format"""
    # Load sequence
    reference_sequence = uf.load_fasta(f"{uv.SEQUENCE_FOLDER}{reference_sequence_information[reference_sequence_name][uv.PATH]}")
    
    # Load individual sequence
    individual_sequence = uf.load_fasta(f"{uv.INDIVIDUALS_FOLDER}{file_path}")

    relative_sequence = compare_subsequences(reference_sequence, individual_sequence)
    relative_sequence = cleanup_variants(relative_sequence, reference_sequence)
    
    return relative_sequence


def relative_sequence_from_csv(file_path):
    """Create relative sequence from a csv file format"""
    with open(f"{uv.INDIVIDUALS_FOLDER}{file_path}", "r") as file:
        reader = csv.reader(file)
        relative_sequence = list(reader)
    return relative_sequence


def relative_sequence_generation(instructions, return_queue):
    """Create relative sequences from different type of input files in order to have a standrad format that can be used in the rest of the application"""
    # Gathering individuals
    individuals = instructions[uv.INDIVIDUALS_KEY]
    
    # Loading individuals information
    with open(uv.INDIVIDUALS_INFORMATION_PATH, "r") as file:
        individuals_information = json.load(file)
    
    for individual_ID in individuals:
        
        reference_sequence_name = individuals_information[individual_ID][0]
        file_path = individuals_information[individual_ID][1]
    
        # Load sequence information
        with open(uv.REFERENCE_SEQUENCE_INFORMATION_PATH, "r") as file:
            reference_sequence_information = json.load(file)
        
        if ".fasta" in file_path:
            relative_sequence = relative_sequence_from_fasta(file_path, reference_sequence_name, reference_sequence_information)
        elif ".csv":
            relative_sequence = relative_sequence_from_csv(file_path)
        else:
            raise Exception(f"Error, Format not supported, In: Relative Sequence generation, Individual {individual_ID}, file is not .csv or .fasta")    

        uf.dump_relative_sequence(individual_ID, relative_sequence)
        
        return_queue.put((PROCESS_NUMBER, individual_ID))
            
    return_queue.put((PROCESS_NUMBER, "Done"))


def run_process(instructions, task_queue, return_queue, error_queue):
    """Permits running process from controller and handling error catching"""
    try:
        relative_sequence_generation(instructions, return_queue)

    except Exception as error:
        excecution_information = sys.exc_info()
        formatted_exception =  traceback.format_exception( *excecution_information)
        error_queue.put((PROCESS_NUMBER, [error, formatted_exception]))