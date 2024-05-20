# MitoFragilityScore

## Introduction, what for ?

## docker version


## Prerequisits


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

## MitoFragilityScore
- Better comments overall.
- Implement execution checkup
- handle process instruction differently, given to the process at laucnh ? -> implies following which process should be launched ?

### launch_controller_instance
- Check if settings file is a file and check if best way to do that

## Controller.py

### Main
- add statistics in main, actions per loop for different processes, study what is quick what is not.
- add comments on main
- unify log, separate human readable and analyser, make specific logs optional
- > Tangeant code analyser. Python.


## SequenceFragilityScorer
 - Finish it
 - ratio or difference for scores, define in settings
