# MitoFragilityScore

## What is this for ?
The MitoFragilitySSCore application is a tool that permits to score mitochondrial genomes based on their fragility. Their fragility in the sense of [citation], so fragility as a potential to form a particular secondary structure that is thought to lead to large scale deletions. The output of the application is thus a score that rates different 

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

    python MitoFragility.py



## How to use the outputs



## What can go wrong



## Look under the hood 

### Idea of the pipeline

#### Inputs, Individuals and sequences


#### Construcs


#### Energies


#### Fragility



##### Details of code

###### Configuration


###### MitoFragilityScore
This is the main file of the programm it has the following responsabilities:
- Loading the settings file from the configured path (in Configuration.py)
- Generating an execution ID.
- Creating an exectuion folder that will hold all files relevant to the execution.
- Creating an Instruction file (JSON), which is a version of the settings file, to which the program adds information it has deduced.
- Launching the Controller.py module's function launch() which starts the programm.


###### Controller
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

- Volumes for docker, what is to be done.
- Unlawful options, for instance launching all proccess but process 4, how can you calculate fragility if there is no energies. SHould this be treated as it would if someone were to launch only process 5 while there are no energies present ?As we  check for previously existing csvs should user make the decision herself of which process should be run or eventually rerun ? Yes but with limitations ?
- Is there something to be done for construct genertors ? They are kind of heavy

- how to Kill a process
- how to kill an application
- Better comments overall.
- Write technical report.
- Visualisation of folders
- Visualisation of Process, green lights and outputs. (Less grandiose than last time)
- Unify Process Id tracking, One file to rule them all and do not use weird separators, use a json. 

## MitoFragilityScore

- > Tangeant code analyser. Python.

## Controller.py

### Main

- add statistics in main, actions per loop for different processes, study what is quick what is not.
- make specific logs optional


## RelativeSequenceGenerator

### cleanup_variants

- We could continue the search for a better alignment tool that does not need cleanup


