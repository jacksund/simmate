# Explore & Run Workflows

## Quick Start

!!! tip
    Most of this guide is for first-time setup. Only steps 7 and 8 are necessary for any subsequent workflow runs.

----------------------------------------------------------------------

### 1. Database Setup
Initialize your Simmate database (if you haven't already from the "Initial Setup" guide). 

!!! warning
    Running `simmate database reset` will delete any existing data in your database.

```bash
simmate database reset
```

### 2. Explore Workflows
View a list of all available workflows and explore them interactively:
```bash
# List all names
simmate workflows list-all

# Explore documentation and parameters
simmate workflows explore
```

### 3. Configure Quantum Espresso (QE)
Simmate uses Quantum Espresso for these tutorials. Ensure it is installed and configured:

- **Option A (Recommended for beginners):** Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and enable Docker in Simmate:
    ```bash
    simmate config update "quantum_espresso.docker.enable=True"
    ```
- **Option B:** Install QE manually and ensure `pw.x` is in your `PATH`.

### 4. Load Potentials
Download the SSSP pseudopotential library:
```bash
simmate-qe setup sssp
```

### 5. Test Configuration
Verify everything is ready:
```bash
simmate config test quantum_espresso
```

### 6. Create an Input Structure
Create a file named `POSCAR` (no extension) and add the following coordinates for Sodium Chloride:
``` text
Na1 Cl1
1.0
3.485437 0.000000 2.012318
1.161812 3.286101 2.012318
0.000000 0.000000 4.024635
Na Cl
1 1
direct
0.000000 0.000000 0.000000 Na
0.500000 0.500000 0.500000 Cl
```

### 7. Create a Workflow Config
Create a file named `example.yaml` to define your calculation:
```yaml
workflow_name: static-energy.quantum-espresso.quality00
structure: POSCAR
```

### 8. Run the Workflow
Execute the workflow using the YAML file:
```bash
simmate workflows run example.yaml
```

### 9. Review Results
Check the newly created folder (e.g., `simmate-task-abcd1234`) for a summary of the results:
```bash
# View the summary file
cat simmate-task-*/simmate_summary.yaml
```
