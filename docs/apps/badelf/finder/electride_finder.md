
# The ElectrideFinder Class

## About

The first step of the BadELF algorithm is to determine whether there are bare electrons in the system and, if so, where they are located. In the original paper this was done by using relatively simple distance and ELF value cutoffs. Since then, the `ElectrideFinder` method has evolved to be significantly more advanced. Using exclusively the ELF, charge density, and crystal structure, the `ElectrideFinder` class now automatically detects not only bare electrons, but atom cores, atom chells, covalent bonds, metallic features, and lone-pairs.

While it was originally conceived to support the BadELF algorithm, the current ElectrideFinder class can be used as a general tool for analyzing the ELF, providing considerably more information on each ELF feature than the BadElfToolkit class.

## Theoretical Background


Since its conception in 1990 by [Becke and Edgecomb](https://doi.org/10.1063/1.458517), the Electron Localization Function (ELF) has been used by researchers as a tool for analyzing the bonding nature of molecules and solids. This is in large part due to the fact that the ELF tends to conveniently display many of the features familiar to chemists such as atomic orbital shells, covalent bonds, metallic interactions, and lone-pairs. 

(Insert images of chemical features)

This is made even more convenient by the fact that the ELF is very resilient to the level of theory used to calculate it ([see Savin et. al.](https://doi.org/10.1002/anie.199718081)]). Additionally, integration of charge in the regions associated with these features was shown to generate the expected values. For example, the regions associated with atomic shells contain electron counts that [closely match what is expected from the periodic table](https://doi.org/10.1002/(SICI)1097-461X(1996)60:4%3C875::AID-QUA10%3E3.0.CO;2-4). The ability of the ELF to consicely represent complex chemical features led researchers to develop methods for categorizing regions of the ELF, largely using ideas similar to those put forth in Bader's [Quantum Theory of Atoms in Molecules](https://onlinelibrary.wiley.com/doi/book/10.1002/9783527610709). These methods have been discussed extensively by many researchers, but we will attempt to summarize them here.

!!! note
     Much of this discussion is based on the review by Carlo Gatti: [Chemical bonding in crystals: new directions](https://doi.org/10.1524/zkri.220.5.399.65073). We highly recommend exploring this work if ELF topology analysis is of interest to you.
    
