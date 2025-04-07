import argparse
import os
import subprocess
import time
import toml

# Function to parse command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Automates verification and comparison with Global DT")
    parser.add_argument("-u", required=True, help="ECFS user")
    parser.add_argument("-c", required=True, help="Case")
    parser.add_argument("-o", required=True, help="Observation verification")
    parser.add_argument("-y", required=True, help="Year (YY)")
    parser.add_argument("-m", required=True, help="Month (MM)")
    parser.add_argument("-d", required=True, help="Day (DD)")
    parser.add_argument("-t", required=True, help="Type")
    parser.add_argument("-n", required=True, help="Number")
    parser.add_argument("-s", required=True, help="CSC")
    return parser.parse_args()

# Function to load environment variables from verif_plugin.toml
def load_env_variables(toml_file):
    config = toml.load(toml_file)
    env_vars = config.get("submission", {}).get("spaveripy_group", {}).get("ENV", {})
    for key, value in env_vars.items():
        os.environ[key] = str(value)

# Main execution function
def main():
    args = parse_args()
    plugin_toml = "verif_plugin.toml"
    
    # Load environment variables
    load_env_variables(plugin_toml)
    
    required_env_vars = ["TOMLS_DIR", "PLUGIN_DIR", "DW_DIR", "TOOL_DIR", "LAUNCHS_DIR"]
    for var in required_env_vars:
        if var not in os.environ:
            print(f"Error: Missing required environment variable {var}")
            exit(1)
    
    # Define constants
    source_dir = f"ec:/{args.u}/DE_NWP/deode/{args.y}/{args.m}/{args.d}/00/{args.t}/{args.n}/{args.s}/"
    src_filename = f"{source_dir}config.toml"
    dest_filename = f"{os.environ['TOMLS_DIR']}/{args.y}/{args.d}/{args.m}/{args.t}/{args.n}/{args.s}/{args.c}.toml"
    verif_conf = f"{os.environ['PLUGIN_DIR']}/verif_configuration"
    verif_plugin_toml = f"{os.environ['PLUGIN_DIR']}/verif_plugin.toml"
    verif_toml = f"{os.environ['TOMLS_DIR']}/{args.y}/{args.d}/{args.m}/{args.t}/{args.n}/{args.s}/{args.c}_verif.toml"
    task = "updateref"
    task_log = f"{os.environ['LAUNCHS_DIR']}/{task}.log"
    launch_template_script = f"{os.environ['PLUGIN_DIR']}/bin/launch_spatial_verif.template.sh"
    
    # Create necessary directories
    os.makedirs(os.path.dirname(dest_filename), exist_ok=True)
    os.makedirs(os.environ['LAUNCHS_DIR'], exist_ok=True)
    
    # Perform the copy
    print(f"getting {src_filename} and copying to {dest_filename}")
    subprocess.run(["ecp", src_filename, dest_filename])
    
    # Replace arguments in configuration files
    with open(verif_conf, 'r+') as f:
        lines = f.readlines()
        lines[1] = dest_filename + "\n"
        f.seek(0)
        f.writelines(lines)
    
    for var, value in {"VERIF_OBS": args.o, "ECFS_USER": args.u}.items():
        subprocess.run(["sed", "-i", f"s/^  {var} = .*/  {var} = \"{value}\"/", verif_plugin_toml])
    
    # Start suite
    os.chdir(os.environ['DW_DIR'])
    subprocess.run(["poetry", "run", "deode", "case", f"?{verif_conf}", "-o", verif_toml, "--start-suite"])
    '''
    # Update config exp_ref
    subprocess.run([
        "poetry", "run", "deode", "run",
        "--config-file", verif_toml,
        "--task", task,
        "--template", f"{os.environ['DW_DIR']}/deode/templates/stand_alone.py",
        "--job", f"{task}.job",
        "--output", task_log
    ])
    
    # Wait 60 seconds
    time.sleep(160)
    
    # Extract values from log
    with open(task_log, 'r') as f:
        log_lines = f.readlines()
    
    case = next((line.split()[2] for line in log_lines if "CASE VALUE:" in line), "")
    exp = next((line.split()[2] for line in log_lines if "EXP VALUE:" in line), "")
    exp_ref = next((line.split()[3] for line in log_lines if "EXP REF VALUE:" in line), "")
    
    # Prepare launch script
    launch_script = f"{os.environ['LAUNCHS_DIR']}/launch_spatial_verif_{case}.sh"
    subprocess.run(["cp", launch_template_script, launch_script])
    
    replacements = {
        "#SBATCH --chdir=.*": f"#SBATCH --chdir={os.environ['LAUNCHS_DIR']}",
        "^VERIF_DIR=\".*\"": f"VERIF_DIR=\"{os.environ['TOOL_DIR']}\"",
        "^OBS=\".*\"": f"OBS=\"{args.o}\"",
        "^Case=\".*\"": f"Case=\"{case}\"",
        "^exp_ref=\".*\"": f"exp_ref=\"{exp_ref}\"",
        "^exp=\".*\"": f"exp=\"{exp}\""
    }
    
    for pattern, replacement in replacements.items():
        subprocess.run(["sed", "-i", f"s|{pattern}|{replacement}|", launch_script])
    
    # Submit job
    os.chdir(os.environ['LAUNCHS_DIR'])
    subprocess.run(["sbatch", launch_script])
    '''
if __name__ == "__main__":
    main()

