Deode-Plugin-Spaveripy
======================

Plugin to run the [spatial verification tool](https://github.com/DEODE-NWP/deode_spatial_verif) from Deode-Workflow.

# Installation
In order to run spatial verification exercises you need to have the [deode scripting system (DW)](https://github.com/destination-earth-digital-twins/Deode-Workflow) installed. Please read carefully and follow the steps in the documentation.

## Deode spatial verif
Clone the spatial verification tool into the working directory where you want to host the tool (if the machine where you are going to run the tool is ATOS, we highly recommend that the repository is cloned to $HPCPERM to avoid [problems reading netCDF](https://jira.ecmwf.int/servicedesk/customer/kb/view/278549648?applicationId=e701adce-e9f9-3560-a8b9-10145e45b5fb&spaceKey=UDOC&portalId=4&title=HPC2020%3A%20Reading%20a%20NetCDF%20or%20HDF5%20file%20gets%20stuck)):
```bash
git clone https://github.com/DEODE-NWP/deode_spatial_verif.git
```
Additionally, the HPC module python3/3.11 or larger must be loaded and pysteps installed as a user package before running a verification exercise:
```bash
module load python3
pip3 install --user pysteps==1.9.0  #Used by the spatial verification tool
```

Make sure that python3 (>=3.11) is loaded by default in your .bashrc file.

## spaveripy plugin
Clone this repository into the desired path, and install toml to read the configuration files of the DEODE runs to verify:
```bash
git clone https://github.com/DEODE-NWP/Deode-Plugin-Spaveripy.git
pip3 install toml
```

# Usage
The plugin is configured in the file verif_plugin.toml. Before running the a verification exercise, make sure to modify the file with paths and user information corresponding to your user, the user who ran the experiment to verify, etc:
```
[general.plugin_registry.plugins]
  spaveripy = "/home/sp3c/deode_project/deode_plugins/spaverifynew/" #Path to your plugin
[scheduler.ecfvars]
  ecf_host = "ecflow-gen-sp3c-001" # Hardcode your ecflow server (needed when using Deode-Workflow >~ v0.12.0)

[submission.spaveripy_group.ENV]
  VERIF_OBS = "IMERG_pcp" #Currently “IMERG_pcp” and “OPERA_rain” are available as observations. SEVIRI_bt is also under testing.
  # Please note that OPERA_rain compares total precipitation (models) against rain (OPERA), which is not correct
  DUSER = "aut6432"   #The user who ran the experiment
  VERIF_USER = "aut6432" # The user who verifies the experiment (you)
  PATH_REF_GRIBS="/ec/res4/scratch/aut6432/DE_Verification/GRIBS/GDT_iekm/" # Where to find gribs for the reference model (do not change)
  REF_NAME="Global_DT" # Name of your Reference model (do not change)
  ECFS_ARCHIVE_RELPATH_HARPOUTPUT="/deode/SPAVERIF/cases/" # Root directory where to store the verification results...
  # ...in permanent archive (create it if needed)
  ECFS_ARCHIVE_RELPATH_DEODEOUTPUT="/deode/" #Normally /deode/ for verifying experiments ran by generic users, and /DE_NWP/deode/ ...
  # ...for verifying experiments from the operational (aut6432) user
  USE_OPERATIONAL_INDEXING="yes" # Whether to use the operational indexing of experiments (use in combination with operational DUSER=aut6432)
  TOMLS_DIR="/ec/res4/hpcperm/sp3c/deode_project/deode_spatial_verif/tomls/"   # Where to store the toml files which configure the OD case...
  # ... and the spatial verification suite.
  PLUGIN_DIR="/home/sp3c/deode_project/deode_plugins/spaverifynew/" #Location of the spatial verification plugin
  DW_DIR="/home/sp3c/deode_project/Deode-Workflow/"                 #Location of your copy of Deode-Workflow
  TOOL_DIR="/ec/res4/hpcperm/sp3c/deode_project/deode_spatial_verif/"     #Location of the Spatial verification software
  LAUNCHS_DIR="/ec/res4/hpcperm/sp3c/deode_project/deode_spatial_verif/standalones/"  # Where to store the scripts that launch some verification...
  #...steps outside of the suites. This is useful sometimes to generate panels with different combinations of experiments to compare

```
Make sure that the folders specified in TOMLS_DIR and LAUNCHS_DIR exist.

## Full verification exercise
To run a verification of an OD case run with the Deode-Workflow , you need to generate a configuration_file with the original toml file from the case, and the plugin configuration:

--config-file
<path/to/toml_file_from_the_case>
<path/to/plugin>/verif_plugin.toml

Then, run:
```bash
deode case ?<path/to/plugin>/verif_configuration -o verif.toml --start-suite
```

## Full verification exercise
In order to make easier to run verification of OD cases run by the on-duty team (user aut6432), a [python-script](https://github.com/DEODE-NWP/Deode-Plugin-Spaveripy/blob/master/bin/run_full_verif.py) has been developed to automate the different steps of a complete verification exercise with the tool. It is used as follows:
run_full_verif.py [-h] -u U -c C -o O -y Y -m M -d D -t T -n N -s S
arguments:
  -h, --help  show this help message and exit
  -u U        ECFS user
  -c C        Case
  -o O        Observation verification
  -y Y        Year (YY)
  -m M        Month (MM)
  -d D        Day (DD)
  -t T        Type
  -n N        Number
  -s S        CSC + resolution


Example: To run a verification of the experiment HARMONIE_AROME_500m_NOR_20250408_storm_1_csc_lt1, run this command:
```
python3 run_full_verif.py -u aut6432 -c HARMONIE_AROME_500m_NOR_20250408_storm_1_csc_lt1 -o IMERG_pcp -y 2025 -m 04 -d 08 -t storm -n 1 -s HARMONIE_AROME_500m
```
This will directly download the configuration file for this case from ecfs, and will create the configuration file to run the verification suite, which looks like this:

![Screenshot from 2025-04-23 15-29-59](https://github.com/user-attachments/assets/331ade6c-d0f9-43ba-a6bf-16e816c6a1f8)


After all the verification steps are completed for the case and the reference and the comparison is generated, the main figures resulting from the verification exercise (FSS and SAL panels, pcp panels, etc) can be found in
the PLOTS folder from the spatial verification tool (TOOL_DIR).

