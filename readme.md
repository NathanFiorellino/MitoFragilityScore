# MitoFragilityScore

## What is this for ?

MitoFragilityScore is a    

## How to launch this application ?

### Option 1: Docker

#### Prerequisits

- [Docker](https://www.docker.com/get-started/)

#### Procedure

Download this repository, run the docker compose tool in the repository, with the following command:

    docker compose up


### Option 2:  Python

#### Prerequisits

- [Python 3.11](https://www.python.org/downloads/)
- [bio 1.7.0](https://pypi.org/project/bio/)
- [ViennaRNA 2.6.4](https://pypi.org/project/ViennaRNA/)

#### Procedure

Download this repository, run the MitoFragilityScore.py in /src with python, with the following command:
    python MitoFragility

## Launch 


## Hot to use the outputs



## What can go wrong



## Look under the hood 

### Idea of the pipeline

#### Inputs, Individuals and sequences


#### Construcs


#### Energies


#### Fragility



##### Details of code

###### Configuration
###### Controller
###### MitoFragilityScore
###### ReferenceSequenceConstructGenerator
###### ReferenceSequenceEnergiesCalculation
###### RelativeSequenceConstructGenerator
###### RelativeSequenceEnergiesCalculation
###### RelativeSequenceGenerator
###### SequenceFragilityScorer
###### UtilitiesFunction
###### UtilitiesVariables

# Notes on improvements

## General

- Write technical report.
- Visualisation of folders
- Visualisation of Process, green lights and outputs. (Less grandiose than last time)
- Unify terminal prompts, if done in docker where will it be prompted
- Unify Process Id tracking, One file to rule them all and do not use weird separators, use a json. 
- Volumes for docker, what is to be done.
- Check that errors everywhere stop all processes and clean up
- how to Kill a process
- Better comments overall.

## MitoFragilityScore

- Implement execution checkup
- handle process instruction differently, given to the process at laucnh ? -> implies following which process should be launched ?

### launch_controller_instance

- Check if settings file is a file and check if best way to do that

## Controller.py

### Main

- add statistics in main, actions per loop for different processes, study what is quick what is not.
- unify log, separate human readable and analyser, make specific logs optional
- > Tangeant code analyser. Python.


## SequenceFragilityScorer

 - ratio or difference for scores, define in settings
