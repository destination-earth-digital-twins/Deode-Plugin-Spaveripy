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
Additionally, the HPC module python3/3.11.8-01 must be loaded and the Python module [pysteps](https://github.com/pySTEPS/pysteps) must be installed on your user before running a verification exercise:
```bash
module load python3/3.11.8-01
pip install --user pysteps==1.9.0
```

## spaveripy plugin
Clone this repository into the desired path:
```bash
git clone https://github.com/DEODE-NWP/Deode-Plugin-Spaveripy.git
```

# Usage
Before running the project, make sure to create your own configuration files:
```bash
cp verif_configuration.template verif_configuration
cp verif_plugin.template.toml verif_plugin.toml
```
Edit the `verif_plugin.toml` and replace the values `spaveripy` and `VERIF_HOME` with your absolute paths to the plugin and the spatial verification tool respectively. Also edit the values of: `VERIF_OBS` (possible values: IMERG_pcp, SEVIRI_bt, OPERA_rain); and `ECFS_USER` (user that stores the experiment outputs). Include the config/modifications/include files into the `verif_configuration`. Note that the toml file is contained within this file. From the root level of the DW's install directory, activate the virtual environment with `poetry shell`.Then, run:
```bash
deode case ?<path/to/plugin>/verif_configuration -o verif.toml --start-suite
```
