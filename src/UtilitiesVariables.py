import os
import csv

## DNA Utilities
COMPLEMENTARY_BASES = {
    "A": "T",
    "T": "A",
    "G": "C",
    "C": "G",
    "N": "N"
}

## ID Separators
SEQUENCE_ID_SEPARATOR = "SEQ"
CONSTRUCT_GENSPECS_ID_SEPARATOR = "CGS"
CENTER_ID_SEPARATOR = "CEN"
CONSTRUCT_ID_SEPARATOR = "CON"

## Hardcoded Paths
CONSTRUCT_FOLDER = f"..{os.sep}Constructs{os.sep}"
ENERGY_FOLDER = f"..{os.sep}Energies{os.sep}"
FRAGILITY_FOLDER = f"..{os.sep}Fragility{os.sep}"
ENERGY_TEMP_FOLDER = f"{ENERGY_FOLDER}{os.sep}temp{os.sep}"
EXECUTION_FOLDER = f"..{os.sep}Executions{os.sep}"
INDIVIDUALS_FOLDER = f"..{os.sep}Individuals{os.sep}"
SEQUENCE_FOLDER = f"..{os.sep}Sequences{os.sep}"

REFERENCE_SEQUENCE_INFORMATION_PATH = f"{SEQUENCE_FOLDER}reference_sequence_information.json"
INDIVIDUALS_GROUPS_PATH = f"{INDIVIDUALS_FOLDER}group_file.json"
INDIVIDUALS_INFORMATION_PATH = f"{INDIVIDUALS_FOLDER}individuals_information.json"

## Settings keys
PIPELINE_EXECUTION_ID_KEY = "PipelineExecutionID"
PIPELINE_PROCESS_TO_RUN_KEY = "PipelineProcessesToRun"
REFERENCE_SEQUENCE_KEY =  "ReferenceSequence"
INDIVIDUALS_GROUP_KEY = "IndividualsGroup"
INDIVIDUALS_KEY = "Individuals"

CONSTRUCT_GENSPECS_KEY = "Construct Generation Specifications"
CENTER_STEP_SIZE_KEY = "CenterStepSize"
LOOP_1_STEP_SIZE_KEY = "Loop1StepSize"
LOOP_2_STEP_SIZE_KEY = "Loop2StepSize"
LOOP_1_MINIMAL_SIZE_KEY= "Loop1MinimalSize"
LOOP_2_MAXIMAL_SIZE_KEY = "Loop2MaximalSize"
ARM_SIZE_KEY = "ArmSize"

## Reference Sequence Information keys
PATH = "Path"
SUBSEQUENCES = "SubSequences"

## Steps
PROCESSES = {
    0: ("0 - Controller", "Controller"),
    1: ("1 - Reference Sequence Construct Generation", "ReferenceSequenceConstructGenerator"),
    2: ("2 - Reference Sequence Energies Calculation", "ReferenceSequenceEnergiesCalculation"),
    3: ("3 - Relative Sequence Generation", "RelativeSequenceGenerator"),
    4: ("4 - Relative Sequence Construct Generation", "RelativeSequenceConstructGenerator"),
    5: ("5 - Relative Sequence Energies Calculation", "RelativeSequenceEnergiesCalculation"),
    6: ("6 - Sequence Fragility Scoring", "SequenceFragilityScorer"),
 }

PROCCES_ACTIVE_FOR_STEPS = {
    0: [1, 2 ,3],
    1: [1, 2, 3, 4, 5],
    2: [6]
}

## Process Log
TIMEPOINTS_KEY =  "Timepoints"
START_APP_KEY = "Starting Application"
START_PROCESS_KEY = [f"Starting Process: " + process[0] for _, process in PROCESSES.items()]
FINISH_PROCESS_KEY = [f"Finishing Process:  " + process[0] for _, process in PROCESSES.items()]
END_APP_KEY = "Ending Application"
LOOP_KEY = "Loop Start"
LOOP_YIELD_KEY = "Loop Yield"
ERROR_KEY = "Error"

PROCESS_LOG = {
   TIMEPOINTS_KEY: {
       START_APP_KEY: None,
       START_PROCESS_KEY[1]: None,
       START_PROCESS_KEY[2]: None,
       START_PROCESS_KEY[3]: None,
       START_PROCESS_KEY[4]: None,
       START_PROCESS_KEY[5]: None,
       START_PROCESS_KEY[6]: None,
       FINISH_PROCESS_KEY[1]: None,
       FINISH_PROCESS_KEY[2]: None,
       FINISH_PROCESS_KEY[3]: None,
       FINISH_PROCESS_KEY[4]: None,
       FINISH_PROCESS_KEY[5]: None,
       FINISH_PROCESS_KEY[6]: None,
       END_APP_KEY: None
   },
   LOOP_KEY: {},
   LOOP_YIELD_KEY: {},
   ERROR_KEY : {}
}


## Queues reserved keywords
TASK = "Task"
RETURN = "Return"
ERRORS = "Errors"
DONE = "Done"