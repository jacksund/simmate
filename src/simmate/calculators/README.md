This module is empty at the moment, but I plan for it to be extremely similar to pymatgen.io's module. It will have classes for parsing input and output files from other programs. More than that, it will have common tasks that you'd run with the program. I haven't decided on the name of the module yet but here are my thoughts so far:

io -- input/ouput. is consistent with other codes but I also
have this as a submodule for each program. I don't this io will fully capture what this module includes.

brokers -- captures the idea that these are intermediates and that simmate is using something else to run calculations. See definitions of "a person or firm who arranges transactions between a buyer and a seller".

thirdparty -- same idea implied with brokers but much more explicit and clear to the user right away

software -- might not be clear that it's other peoples code

thirdpartysoftware -- clear and gets the message accross but is too long. And tps is unclear at a glance.

calculators -- takes from ASE naming convention but uses it more broadly (beyond just DFT and geometry calculators). It would also help distinguish from what I want the "datamine" module to be -- because that would also suggest a broker.


External code includes those that...
run DFT or similar calculations
workup DFT calculations and run subsequent analysis
provide visualizaton, vesta files...? (or have this in visualization.thirdparty module)
What about cif and xyz files? (or have this in io module? Maybe visualization mod?)
Or pymatgen, jarvis, ase structures? (add this to io module as well)