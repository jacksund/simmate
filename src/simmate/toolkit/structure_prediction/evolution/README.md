
:warning::warning::warning:
This module is still at the planning stage and should not be used at the moment.
:warning::warning::warning:


# To-do list
visualization / plotting / workup

search exits when I hit the structure limit -- I should wait until all submitted structures finish

restrict RandomSymStructure to the target nsites -- Symmetry sometimes returns fewer

consider making the in-memory database a pandas dataframe or Sample objects

Continue calc from previous csv/cifs

add database class that links to Postgres cloud (via sqlalchemy or django)

custom starting structures

fingerprinting -- inside Selector class?

"archive" structures -- remove them from the list of search.structures if they no longer have a
chance to be selected. This will help with the memory load for longer searches. 

update prefect workflow to multistep

multistep workflow have cutoffs as in input parameter...? This would be much 
easier than making a query - maybe future version can do that.



** For SearchEngine **
what if the workflow changes (e.g. starts with ML relax) but the
final table stays the same?

chemical system instead of composition input? Allow 1,2,3D?

I assume fitness_field="energy_per_atom" for now. Allow other fields from
the individuals_table, like "conductivity" or "electride character"

Specifying a stop_condition class to allow custom ones?
I just assume the stop condition is either (1) the maximum allowed
calculated structures or (2) how long a given structure has been
the "best" one.

add triggered_actions which can be things like "start_ml_potential" or
"update volume in sources" or "switch workflow to __"

I assume we are using Prefect for workflow submission right now. Add support
for local execution or even dask.

Add singleshot sources
"prototypes_aflow",
"substitution",
"third_party_structures",
"third_party_substitution",
"SomeOtherDatatable",  # e.g. best from table of lower quality calculations
