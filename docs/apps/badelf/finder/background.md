# Theoretical Background


Since its conception in 1990 by [Becke and Edgecomb](https://doi.org/10.1063/1.458517), the Electron Localization Function (ELF) has been used by researchers as a tool for analyzing the bonding nature of molecules and solids. This is in large part due to the fact that the ELF tends to conveniently display many of the features familiar to chemists such as atomic orbital shells, covalent bonds, metallic interactions, and lone-pairs. 

(Insert images of chemical features)

Integration of charge in the ELF regions associated with these features gives charges close to the expected values. For example, the regions associated with atomic shells contain electron counts that [closely match](https://doi.org/10.1002/(SICI)1097-461X(1996)60:4%3C875::AID-QUA10%3E3.0.CO;2-4)  what is expected from the periodic table. The use of the ELF to analyze useful chemical features is made even more convenient by the fact that the ELF is fairly consistent with respect to the level of theory used to calculate it ([see Savin et. al.](https://doi.org/10.1002/anie.199718081)).

The ability of the ELF to consicely represent complex chemical features led researchers to develop methods for categorizing regions of the ELF, largely using ideas similar to those put forth in Bader's [Quantum Theory of Atoms in Molecules](https://onlinelibrary.wiley.com/doi/book/10.1002/9783527610709). These methods have been discussed extensively by many researchers, but we will summarize them here.

## Basins, Attractors, and Bifurcation Plots

!!! note
     Much of this discussion is based on the review by Carlo Gatti: [Chemical bonding in crystals: new directions](https://doi.org/10.1524/zkri.220.5.399.65073). We highly recommend exploring this work if ELF topology analysis is of interest to you.

Similar to Bader analysis, the ELF of a system can be divided into regions separated by zero-flux surfaces. Doing so results in distinct regions of space known as basins, with each basin having a single maximum called an attractor.

Each basin represents a distinct chemical feature including atom core shells, lone-pairs, covalent bonds, metallic bonds, and bare electrons. The type of feature can be determined by characterizing features of the ELF around it. A particularly helpful method for assisting with this process is the construction of a type of tree diagram known as a bifurcation plot.

In this method, the regions bounded by an isosurface of the ELF are viewed at different values, *f*. These regions are called *f*-localized domains, and correspond to regions where the ELF is greater than or equal to the value *f*. Any *f*-domain contains at least one attractor. Domains containing more than one attractor is called reducible while those containing only one are called irreducible. As *f* is increased, reducible domains split into smaller topologically distinct domains with fewer attractors. The critical *f* values at which these splits occur are called bifurcations. The final irreducible domains are the exact same as the basin described above. This method also allows us to define a "depth" referring to the difference in a basin's maximum from the value at which it split from it's parent reducible domain. This idea of depth is one useful characteristic for distinguishing features in the ELF. Using bifurcation plots, we can begin to categorize each of the ELF attractors. 

## Atomic Attractors
Starting at an *f* value of 0, our entire system is one continuous domain. As we increase the *f* value, domains will begin to split off. Those that fully surround exactly one atom, can be thought of as atomic. 
These atomic domains can split further into one of several types:

1. **Atomic Core/Shell**. Core electrons fully surround the atom's nucleus and are nearly spherical. In simple ionic systems such as NaCl, this results in a simple bifurcation plot:

(insert picture of NaCl and bifurcation plot)

2. **Lone-Pairs**. Lone-pairs split off from the core/shell domains at relatively low (~0.2) ELF values and have high ELF values. They don't fully surround the atom and are not along an atomic bond.

(insert picture of SnO and bifurcation plot)

3. **Heterogenous Covalent Bonds**. In some cases, covalent bonds form a reducible domain that fully surrounds the more electronegative atom, similar to atomic shells. However, at higher *f* values, this domain further splits into smaller domains that do not surround the atom. These attractors have a large depth and are distinct from lone-pairs in that they are always along an atomic bond.

(insert picture of SiSn and bifurcation plot)

## Valence Attractors

Once the atomic domains have split from the ELF, anything left is one large valence domain. Again, these features can be one of several types:

1. **Homogenous Covalent Bonds**. In covalent bonds involving the same atom, the bonds will sit exactly between the two atoms and at low *f* values will form a network throughout the system surrounding multiple atoms. At higher *f* values, this network will split into individual covalent bonds. Just like heterogenous covalent bonds, these are characterized by high depth and their location along an atomic bond.

(Insert Si and bifurcation plot)

2. **Metallic Character**. In most metals, there will be a metallic domain similar to that of a homogenous covalent bond that forms a network throughout the system. However, the metallic domains making up this network have incredibly low depths (~0.02), low volumes and charges, and are typically not located along atomic bonds.

(Insert Ti, other? and bifurcation plot)

3. **Bare Electrons/Electrides**. Finally, anything else that splits from the valence domain has a large depth and doesn't sit directly along an atomic bond. These attractors tend to have a larger volume, ELF value, depth, and distance to nearby atoms. This type of feature is found in both electrides and metals, and how to distinguishing them is still up for debate. In our implementation they are separated by a series of user controlled cutoffs.

(Insert Ca2N and bifurcation plot)

