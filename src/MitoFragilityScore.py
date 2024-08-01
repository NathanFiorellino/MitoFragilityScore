import os
import json
import uuid

import UtilitiesVariables as uv
import UtilitiesFunction as uf
import Configuration as cf

import Controller as controller

def load_settings():
    """Load settings from file."""
    if not os.path.isfile(cf.SETTINGS_FILE_PATH):
        raise f"No settings file at {cf.SETTINGS_FILE_PATH}, this path is set in the /src/Configuration.py file"
    
    with open(cf.SETTINGS_FILE_PATH, "r") as file:
        settings = json.load(file)

    return settings


def get_execution_ID(settings):
    """Generate random ID for execution or read it from settings, """
    if settings[uv.PIPELINE_EXECUTION_ID_KEY] == "New Execution":
        execution_ID = str(uuid.uuid4())
    else:
        execution_ID = settings[uv.PIPELINE_EXECUTION_ID_KEY]

    return execution_ID


def prepare_execution_folder(execution_ID):
    """Creating execution folder"""
    os.mkdir(f"{uv.EXECUTION_FOLDER}{execution_ID}")
    

def prepare_instructions(execution_ID, settings):
    """Generate instruction file with additional information"""
    uf.add_individuals_to_settings(settings)
    uf.create_instructions(execution_ID, settings) 


if __name__ == "__main__":
    
    settings = load_settings()
    execution_ID = get_execution_ID(settings)
    print("Execution ID:",  execution_ID)
    prepare_execution_folder(execution_ID)
    prepare_instructions(execution_ID, settings)

    controller.launch(execution_ID)