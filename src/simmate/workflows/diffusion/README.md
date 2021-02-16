
## Fractured Hierarchical Architecture for High-Throughput Diffusion Analysis

While this module will eventually be for common diffusion analysis workflows, it is currently for my grad-school project on halide diffusion energies. I'm on a time-crunch to graduate (lmao) and thus take some shortcuts by using pymatgen and custodian -- rather than the functionality I've rewritten in simmate. This will allow me to have an easier time publishing because I can say I'm using well-established codes instead of my new simmate code. So instead of introducing a new
framework, this paper will be introducing the effectiveness of my "Fractured Hierarchical Architecture". This is breaking of a hierarchical workflow (i.e. one that has increasely accurate calculations separated by halting/filtering criteria) into individual ETL pipelines, each with their own table.


### Fixed-Workflow Architecture

You have an overall workflow where you pass in one structure at a time. The entire workflow for that structure is ran immediately and to completion (or until a check fails).


With this setup, it makes sense to publish on a well-designed workflow, and then have a separate paper where we scale to a full database.

Scaling your computation resources is tricky here because we want to run as many structure workflows in parallel as possible. The amount of resources the structure needs scales as the workflow progresses so we would need a complex Executor to handle this. An example of this is when the first task can be ran on one core in seconds while the final task needs >20 cores and hours to run. There may be a scenario where all structures make it far along the analysis and many resources are all needed at once (or resources underused if the reverse occurs). So you can set resources by calc/task but we will like over- or under-submit to that queue at any given time. There is one advantage though, and it’s that we can run all calculations in the same directory and utilize the previous output files for continuation on VASP calcs.


You can certainly move your code back and forth between these architectures, but it’s much easier said than done due to data storage. Further, converting from each isn’t equally easy depending on how you wrote your code.


### Fractured-Workflow Architecture

You have individual tasks (calcs) that are each applied to an entire database -- where the database can be structures, pathways, or outputs from a previous calculation. The input database for each task is constantly read by a ‘priority ranking’ function. The task runs independently and pulls the top priority entry (structure/pathway/etc) and runs it next. 


With this setup, we can have a single paper on the database and workflow architecture. The architecture encompasses how the workflow is constantly evolving, thus the initial publicized workflow doesn’t become immediately obsolete.


Scaling computational resources is very easy here as we can assign a set number of resources for each task - then those resources are always being utilized at the exact specified amount. The downside is that since the tasks are ran independently across differing computational resources, it’s no longer possible to run all of a given workflow in a single working directory (unless we only use a single cluster). Here, the database must carry any connecting information between calculations (if only one cluster is used, we can use a working directory name to connect information with ease). Therefore we can only utilize the previous output files for continuation on VASP calcs if we save them to a database somewhere. If the data is extremely large and expensive to store (or even time consuming to transfer!) this becomes an issue. In many cases, it may be simpler to just redo an analysis or calculation, which results in a decrease in overall workflow efficiency.


You can write your code for fixed-workflow architecture in a way where there is a high-level class that holds all data in memory for every analysis/task done. This uses more memory but ensures that no analysis needs to be repeated, saving on computational cost. Analogously, the other architecture can do the same by saving to a database, but this introduces large write/read times of that data. The solution is to introduce an abstraction of the database layer in fractured architecture, where we can use an in-memory database type (such as Pandas dataframe or Dask global variables) when speed is preferred.


This setup is extremely powerful because it focuses on depth-first scaling - that is, a single cheap calculation can be done on all structures and doesn’t have to wait for workflows to complete before moving on. For example, if one calculation finishes all of the queue pathways, it can trigger a request to broaden cutoff criteria such that more pathways are added to it’s queue. Thus we can change a task/calculation cutoff setting without disrupting the entire workflow.


Priority ranking can adapt overtime as well. For example, we may want to replace a generic priority ranking function with a new calculation entirely (such as a machine-learned descriptor). We could even produce a fork in the workflow for a specific application where priority is based on the target application.


## Stages in my workflow


NOTE: I am using... 
    - Materials Project database version '2020_09_08'
    - Pymatgen 2020.12.31
    - Pymatgen-diffusion 2020.10.8 (be extra careful here!)
    - Django 3.1.5
    - Prefect 0.14.5
    - Matminer forked + pip -e install because their conda is broken


1. We want to start with a clean database so let's reset ours:
```python
from simmate.configuration.manage_django import reset_db
reset_db()
```

2. For speed-up in the codes below, we want to use Dask. For that, we can setup a Dask cluster and tell Prefect to use it as our
executor. This also allows us to watch a progress bar at http://localhost:8787/status. In other cases, I run workflow.run in parallel rather than task.run. For that, I simply use client.map() instead of setting the workflow executor.
```python
# setup our Dask cluster
from dask.distributed import Client
client = Client()

# NOT SHOWN --> import our desired workflow

from prefect.executors import DaskExecutor
workflow.executor = DaskExecutor(address=client.scheduler.address)
```

3. For checkpointing my database progress, I do two things at each step below. First, I make a copy of the sqlite file and name it db_checkpoint00N.sqlite3 where N corresponds to the step number. I also save the entire table added for each step to a csv file too. This is just in case I accidently reset my database or want to test with the next step. Here I show an example of making a csv file with the Structure_DB model:
```python
# now convert the entire table to a csv file
from simmate.configuration import manage_django  # ensures django setup
from simmate.database.all import Structure as Structure_DB
queryset = Structure_DB.objects.all()
from django_pandas.io import read_frame
df = read_frame(queryset, index_col="id")
df.to_csv("initial_structuredb.csv")

# if you want to reload the csv
# import pandas
# df = pandas.read_csv("initial_structuredb.csv", index_col="id")
```

4. We want to add all of the Fluoride structures from the Materials Project to our own database. This includes some extra data such as the hull energy and also running some "sanitation" on the structures.
```python
# import all of the data to our sqlite database
from simmate.workflows.diffusion.add_structure import workflow
workflow.executor = DaskExecutor(address=client.scheduler.address)
status = workflow.run(criteria={"elements": {"$all": ["F"],}})
```

5. Using this database, let's make a table for the diffusion pathways. Note that I hardcode some options here, such as limiting each structure to 5 pathways. See the find_paths.py workflow for details.
```python
from simmate.workflows.diffusion.find_paths import workflow
from simmate.configuration import manage_django  # ensures django setup
from simmate.database.all import Structure as Structure_DB, Pathway as Pathway_DB

# grab all structure ids in our database
structure_ids = Structure_DB.objects.values_list("id", flat=True).all()

# Run the find_paths workflow for each individual id
futures = client.map(
    workflow.run,
    [{"structure_id": id} for id in structure_ids],
    pure=False,
)

# wait for all of the calls to finish and grab the results
results = client.gather(futures)

# for reference these are the structure ids that failed
# Note - it was easier to grab this list when not using dask
failed_ids = [134, 339, 465, 466, 479, 481, 482, 990, 995, 1037, 1486, 1487, 1639, 1880, 1928, 1994, 1996, 2482, 2531, 2815, 3113, 3489, 3529, 4044, 4415, 4478, 4480, 4488, 4491, 4997, 5464, 5739, 7911, 7929, 8452, 9327, 9450]
```

6. Make my table of empirical predictors.
oxidation, oxidation_radii_dict, atomic_fraction_fanion, nsites, path_len_cutoff_vsDmin, dimensionality(_cumlengths, _cumbarriers), ionic_radii_overlap, ewald_energy,


## TODO

1. Look at the ionic radii overlap along the pathway. Ewald Energy?
```python
#!!! This function should be moved elsewhere and further developed in the future
def get_ionic_radii_overlap(
    image_struct, 
    ion_index,
    oxidation_check=self.oxidation_check, #!!! is this line needed?
    ion_tested=self.ion_tested, #!!! is this line needed?
    ):

    moving_site = image_struct[path.iindex]
    moving_site_radius = self.oxidation_check.radii[self.ion_tested]
    moving_site_neighbors = image_struct.get_neighbors(moving_site, r=8.0, include_image=True) #!!! Hard-coding issue for cutoff radius?
    
    max_overlap_cation, max_overlap_anion, max_overlap_nuetral = [-999] * 3 # start as -999 to ensure its reset
    for neighbor_info in moving_site_neighbors:
        neighbor, distance, trash, trash = neighbor_info
        neighbor_radius = self.oxidation_check.radii[neighbor.species_string]
        overlap = moving_site_radius + neighbor_radius - distance
        # separate overlap analysis to oxidation types (+, -, or nuetral)
        if ('+' in neighbor.species_string) and (overlap > max_overlap_cation):
            max_overlap_cation = overlap
        elif ('-' in neighbor.species_string) and (overlap > max_overlap_anion):
            max_overlap_anion = overlap
        elif ('-' not in neighbor.species_string) and ('+' not in neighbor.species_string) and (overlap > max_overlap_nuetral):
            max_overlap_nuetral = overlap
    
    # I convert to numpy here so I can quickly subtract arrays below
    return numpy.array(max_overlap_cation, max_overlap_anion, max_overlap_nuetral)

valid_paths = []
for path in self.paths:

# we now run the idpp analysis on each pathway
# The idpp relaxation is computationally expensive, so I only look at the 
# start and midpoint images here.
path_structures = path.get_structures(
    nimages=1, # for speed, I only do one image here
    vac_mode=True, # vacancy-based diffusion
    idpp=True, # IDPP relaxation of the pathway
    # **idpp_kwargs,#species = 'Li', # Default is None. Set this if I only want the ion to move
    )
            
# only grab the first two images (start and midpoint images)
start_data = get_ionic_radii_overlap(path_structures[0], path.iindex)
midpoint_data = get_ionic_radii_overlap(path_structures[1], path.iindex)

# Compute the change in overlap for [cation, anion, nuetral]
delta_overlaps = midpoint_data - start_data

# See if any ion type changes ionic radii overlap over the allowed threshold
if max(delta_overlaps) > self.path_overlap_cutoff:
    print("Pathway removed based on change in the diffusing ion's ionic radii overlap")
    pass
else:
    valid_paths.append(path)

# now that we've identified the valid paths, update the class's paths variable
self.paths = valid_paths
```

```python
# METHOD 1
# Finding max change in anion and cation overlap
overlap_data_cations, overlap_data_anions, overlap_data_nuetral = [], [], []
for struct_index in range(len(idpp_structs)):
    image_struct = idpp_structs[struct_index]
    moving_site = image_struct[site1_shifted_index]
    moving_site_neighbors = idpp_structs[struct_index].get_neighbors(moving_site, r=8.0, include_image=True)
    moiving_site_radius = self.oxidation_check.radii[self.ion_tested]
    max_overlap_cation, max_overlap_anion, max_overlap_nuetral = -999, -999, -999 # reset value for each image
    for neighbor_info in moving_site_neighbors:
        neighbor, distance, trash, trash = neighbor_info
        neighbor_radius = self.oxidation_check.radii[neighbor.species_string]
        overlap = moiving_site_radius + neighbor_radius - distance
        # separate overlap analysis to oxidation types (+, -, or nuetral)
        if ('+' in neighbor.species_string) and (overlap > max_overlap_cation):
            max_overlap_cation = overlap
        elif ('-' in neighbor.species_string) and (overlap > max_overlap_anion):
            max_overlap_anion = overlap
        elif ('-' not in neighbor.species_string) and ('+' not in neighbor.species_string) and (overlap > max_overlap_nuetral):
            max_overlap_nuetral = overlap
    overlap_data_cations.append(max_overlap_cation)
    overlap_data_anions.append(max_overlap_anion)
    overlap_data_nuetral.append(max_overlap_nuetral) 
# make lists into relative values
overlap_data_cations_rel = [(image - overlap_data_cations[0]) for image in overlap_data_cations]
overlap_data_anions_rel = [(image - overlap_data_anions[0]) for image in overlap_data_anions]
overlap_data_nuetral_rel = [(image - overlap_data_nuetral[0]) for image in overlap_data_nuetral]
# append to self.unique_edges[edge]
edge.append([overlap_data_cations_rel,overlap_data_anions_rel, overlap_data_nuetral_rel])
#plotting
# pyplot.figure(figsize=(5,3), dpi=80)
# pyplot.plot(range(self.nimages+1),overlap_data_cations_rel, 'o-', label='Cation')
# pyplot.plot(range(self.nimages+1),overlap_data_anions_rel, 'o-', label='Anion')
# pyplot.plot(range(self.nimages+1),overlap_data_nuetral_rel, 'o-', label='Nuetral')
# pyplot.legend(loc='upper right',title='Neighbor Type', fontsize=8)    
# pyplot.xlabel('Diffusion Progress')
# pyplot.xticks([0, self.nimages + 1], [r'$Start$', r'$End$'])
# pyplot.ylabel('Max Overlap (A)') 
# pyplot.tight_layout()
# pyplot.savefig(filename_folder + "edgeoverlap_" + str(edge_index))
# pyplot.show()
# pyplot.close()
```

```python
# METHOD 2
from matminer.featurizers.site import EwaldSiteEnergy
sitefingerprint_method = EwaldSiteEnergy(accuracy=3) # 12 is default
# #!!! requires oxidation state decorated structure

images = path.get_structures(
    nimages=5, 
    vac_mode=True,
    idpp=True,
    # **idpp_kwargs,
    #species = 'Li', # Default is None. Set this if I only want one to move
    )

energy_ewald = []
for image in images:
    image_struct = idpp_structs[struct_index]
    # moving_site = image_struct[site1_shifted_index]
    image_fingerprint = numpy.array(sitefingerprint_method.featurize(image_struct, site1_shifted_index))
    image_fingerprint = image_fingerprint[1:] * (1/(numpy.array(range(len(image_fingerprint))))**2)[1:] #!!! RDF Scale down
    fingerprints.append(image_fingerprint)
# I don't want to save the full fingerprints, so I save the distances instead
# The distances are relative to the starting structure
energies_ewald = []
```

2. IDPP relaxed supercell. min_sl_vector=6, images=6, 
```python
supercell_size = [(min_sl_vector//length)+1 for length in structure_lll_supercell.lattice.lengths]
structure_lll_supercell.make_supercell(supercell_size)
```

3. visulizing pathways
```python
path_structures = path.get_structures(
    nimages=5, 
    vac_mode=True,
    idpp=True,
    # **idpp_kwargs,
    #species = 'Li', # Default is None. Set this if I only want one to move
    )
path.write_path('test15.cif', nimages=10, idpp=False, species = None,)

# write to cif file to visualize
dpf.write_all_paths('test.cif', nimages=10, idpp=False) # for speed, species kwarg isnt accepted here
```

4. write IDPP calc files. Remember ISYM=0.
```python
# make the VASP input files for a given path
from pymatgen.io.vasp.sets import MPStaticSet

filename_folder_edge = filename_folder + "/EdgeIndex_" + str(edge_index)
os.mkdir(filename_folder_edge) 
for struct_index in range(len(idpp_structs)):
    filename_folder_edge_image = filename_folder_edge + "/ImageIndex_" + str(struct_index)
    MPStaticSet(idpp_structs[struct_index], user_incar_settings={"ISYM":0}).write_input(filename_folder_edge_image) 
```


## Extra notes

I need a way to constantly have a steady flow of workflows going through, where I can up/downscale this value over time. Below are some options, where I think the best is option 1.


OPTION 1 -- we constantly loop to check number of running workflows and submit new one if needed. This requires a separate process to be constantly running. Or I can have this as a workflow that runs every few seconds.


psuedo-code:


    Connect Prefect client.
    
    
    Check number of workflow runs pending on Prefect. If it is less than our limit, we need to submit another.
    I can also write this to submit multiple at a time, rather than only one per check.
    
    
    Sort pathways by one calc column (priority) and then grab the first pathway where another
    column is null (not completed).
    https://docs.djangoproject.com/en/3.1/ref/models/querysets/#std:fieldlookup-isnull
    https://docs.djangoproject.com/en/3.1/ref/models/querysets/#first    
        filter isnull one column, orderby the other, then grab first
    
    
    Set that column to 'in progress' so that it's not grabbed again. Look at my custom executor class for tips.
    
    
    Submit the workflow via Prefect
    
    
    Sleep for a set amount of time before checking again
    
    
Want to manually submit a specific structure? You can do this through the Prefect UI or a separate script.

Option 2 -- We start a set number of workflows. We have the end of one workflow trigger the start of a new one. This doesn't require any separate running process but instead uses the Prefect Agents/Executors. I think this approach will give rise to messy code and issues where we want to increase/decrease the number of jobs.


Option 3 -- We control the number of jobs through PrefectCloud concurrency settings. This requires a paid method and may require submitting all jobs to the queue at once though (or in stages like option 1).


### extra utils to add...


Have a workflow that runs every month, day, etc. and deletes completed workflows to keep meta db size down


Check that pathways come out in the same order (index) despite cell shape
