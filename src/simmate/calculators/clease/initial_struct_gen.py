from simmate.workflow_engine import Workflow
from ase import Atoms
from clease.settings import Concentration, CECrystal
from clease import NewStructures
from ase.db import connect

class ClusterExpansion__Python__InitialStructureGen(Workflow):
    use_database = False

    @staticmethod #method bound to a class rather than its object; knows nothing about class and just deals with parameters
    def run_config(
        basis_elements: list[list[str]] = [['Al','Sc'],['C'],['Sc','Al']],
        #to vary some elements in your CE, use the format <y-x>X<x> and define your x as the threshold of variance
        #for ex. in this we have "C<1>" because we want the concentration to remain constant and we have Al/Sc<1-x>X<x>
        #because we want there to be maximum 2 atoms of one or the other to 1 carbon atom
        formula_unit: list[str] = ["Al<x>Sc<1-x>","C<1>", "Sc<y>Al<1-y>"],
        variable_range: dict = {"x": (0, 1), "y": (0, 1)},
        atoms: str = 'AlScC',
        lattice: list[tuple[float]] = [
            (0.74276, 0.74276, 0.74276), 
            (0.0000, 0.0000, 0.0000), 
            (0.25724, 0.25724, 0.25274),
        ],
        a: float = 5.78605,
        b: float = 5.78605,
        c: float = 5.78605,
        alph: float = 33.7158,
        beta: float = 33.7158,
        gamma: float = 33.7158,
        db_name: str = "database.db",
        space_group: int = 1,
        supercell: int = 64, #threshold on max size of supercell
        cluster_diameter: list[int] = [7, 5, 5], #distance between atoms in cluster in angstroms, number of values increase w/ max cluster size
        generationnumber: int = 0,
        structure_per_generation: int = 10,
        **kwargs
    ):

        #define concentration
        conc = Concentration(basis_elements=basis_elements)
        conc.set_conc_formula_unit(formula_unit, variable_range=variable_range)

        #define lattice
        latt = Atoms(atoms, lattice)
        settings = CECrystal(concentration=conc,
            spacegroup=space_group,
            cellpar=[a, b, c, alph, beta, gamma], #data from lattice definition
            supercell_factor=supercell,
            basis=latt.get_positions(),
            db_name=db_name,
            max_cluster_dia=cluster_diameter)
        
        #generate initial pool of structures
        ns = NewStructures(settings, generation_number=generationnumber, struct_per_gen=structure_per_generation) #specifies the number of structures you want and the generation number for organization
        ns.generate_initial_pool()

        #connect to database
        db=connect(db_name)

        #update database with new structures
        for row in db.select(converged=False): #identifies the rows in the database that haven't converged
            atms = row.toatoms()
            atms.write("structure_%s.cif" % row.id, format='cif') #creates cif files of each structure and names them based on their row id number
