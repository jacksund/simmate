Where to add parts of a calculation, where the overall calc looks like...
- Write Input Files based on custom+defualt settings
- Run the calculation by calling the program 
- Load ouput files
- check for errors
- [correct them, rerun]
- postprocess/analysis

I want modules to be organized based on logic & application, rather than by
the program they are using. For example, I would find Bader in a population
analysis module, rather than just io.bader or exe.bader. Based on that, I
will separate the input/output load and running into the io module, while
the setup, running, error checking, and workup tasks are located in matsci. 
Lastly, the overall prebuilt workflows will be in one easy-to-find module 
located in a workflows.vasp. The separation of io parsing, tasks, and workflows
may be difficult for users, so I'm going to think about this more. But for
now how I envision module organization:

io.vasp.inputs (analogous to pymatgen.io.vasp.inputs)
    INCAR
    POSCAR
    POTCAR
    KPOINTS
    InputSet (base class -- libraries located elsewhere, see below)

io.vasp.outputs (analogous to pymatgen.io.vasp.inputs)
    CONTCAR
    WAVECAR
    CHGCAR
    ELFCAR
    vasprun.xml

** do I need to separate inputs and outputs module...? I really could have them
in the same module. Also some files like CHGCAR can be both an input and an output
such as a continuation calc that uses another calc's CHGCAR as a staring point

matsci.dft.vasp
    setup (analogous to pymatgen.io.vasp.sets) (this is where inputs.InputSet is implemented!)
    run (wraps commandline util) (analogous to custodian.vasp.jobs)
    error
        check (analogous to custodian.vasp.validators)
        correct (analogous to custodian.vasp.handlers)
    workup

workflows.dft (maybe have a Calculator class somewhere in here -- analogous to ase.calculators)
    relax.vasp
    static.vasp
    pdos.vasp
    bandstructure.vasp



Likewise for Bader:

io.bader.inputs
    inputs
    outputs
        ACF.dat
matsci.population_analysis.bader
    setup
    run
    error
    workup
workflows.population_analysis
    bader
    elf
    pdos_integration



VERSION 2 organization:

io.bader
    io
        input (analogous to pymatgen.io.vasp.inputs)
        outputs (analogous to pymatgen.io.vasp.outputs)
    tasks
        setup (analogous to pymatgen.io.vasp.sets)
        run (wraps commandline to bader.exe and options)
        error
            check (analogous to custodian.vasp.validators)
            correct (analogous to custodian.vasp.handlers)
        workup/postprocessing (writing summary files, renaming, moving, or compressing output files...?)
    jobs (workflow/job) (actually a single function or prefect task in the form of a CustodianJob)
workflows.population_analysis
    bader (a prefect workflow that includes StaticVASP and then BaderAnalysis "jobs")
    elf
    pdos_integration

And then instead of Calculator objects, I would have...
structure.get_potential_energy(method="StaticVaspWorkflow")
structure.get_population_data(method=workflows.population_analysis.bader)
where the method loads from the workflows module!

Should I adapt to Prefect naming (Workflow -> Tasks -> [stages?])
What I have now is (Workflow -> Jobs -> Tasks)

```
project
│   README.md
│   file001.txt    
│
└───folder1
│   │   file011.txt
│   │   file012.txt
│   │
│   └───subfolder1
│       │   file111.txt
│       │   file112.txt
│       │   ...
│   
└───folder2
    │   file021.txt
    │   file022.txt
```
