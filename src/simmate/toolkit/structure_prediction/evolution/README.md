
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

