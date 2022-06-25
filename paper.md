---
title: 'Simmate: a framework for materials science'
tags:
  - Python
  - materials science
authors:
  - name: Jack D. Sundberg^[Corresponding author]
    orcid: 0000-0001-5739-8919
    affiliation: 1
  - name: Siona S. Benjamin
    orcid: 0000-0002-3822-9762
    affiliation: 1
  - name: Lauren M. McRae
    orcid: 0000-0002-0360-9626
    affiliation: 1
  - name: Scott C. Warren
    orcid: 0000-0002-2883-0204
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
affiliations:
 - name: Department of Chemistry, The University of North Carolina at Chapel Hill, Chapel Hill, North Carolina 27599, United States
   index: 1
 - name: Department of Applied Physical Sciences, The University of North Carolina at Chapel Hill, Chapel Hill, North Carolina 27599, United States
   index: 2
date: 29 March 2022
bibliography: paper.bib
---

# Summary

Over the past decade, the automation of electronic structure codes has led to many large-scale initiatives for materials discovery, such as the Materials Project [@matproj], AFLOW [@aflow], OQMD [@oqmd], JARVIS [@jarvis], and others [@matcloud; @nomad; @aiida]. Each of these projects facilitate the creation and distribution of materials science data to the broader researcher community through databases, workflow libraries, and web interfaces. However, each software ecosystem (i.e. the collection of software used by a specific project) still possesses several pain-points for users attempting to implement new standards for computational research. Proper setup involves learning how (i) workflows are defined/orchestrated, (ii) how databases are built/accessed, and (iii) how website interfaces/APIs make results accessible to the community, where each component requires learning a new package and, more importantly, learning how that package integrates with others. As a result, it can be difficult to integrate several smaller packages when building a production-ready server and database for materials science research. To address this, we developed the Simulated Materials Ecosystem (Simmate).

# Statement of Need

Simmate strives to simplify the process for researchers who are setting up a full-featured server. For the purposes of beginners, we desired a framework that could run locally without requiring any additional setup. For the purposes of experts, we sought to enable scaling of calculations across any number of resources and to facilitate the addition of new functionality. Simmate accomplishes these goals by (i) building on top of popular, well-established packages for workflow orchestration, database management, and materials science analysis and (ii) distributing our software as an "all-in-one" package that integrates all of these features. This is contrary to analogous software ecosystems that maintain custom packages and distribute solutions as separate programs.

For example, while other materials science ecosystems write workflow managers and task distribution from scratch (e.g. Fireworks [@fireworks] or AiiDA [@aiida]), we instead use high-level, beginner-friendly packages such as Dask [@dask] and Prefect [@prefect]. Using well-established packages also extends to our choice of website framework (Django [@django]) and underlying materials analysis toolkit (PyMatGen [@pymatgen]). The use of popular packages lets Simmate users take advantage of these packages' large user communities, abundant guides, and robust coding standards, while Simmate handles the integration of these packages in the context of materials science. This greatly facilitates the addition of new features while also enabling best-practices.

To understand our aim to be an “all-in-one” solution, it is useful to compare Simmate with the collection of packages developed by the Materials Project [@matproj]. The Materials Project is powered by many smaller packages, each with a specific use case – e.g. Atomate for a workflow library [@atomate], Fireworks for workflow orchestration [@fireworks], Custodian for error handling [@pymatgen], EMMET for schemas/APIs [@emmet], MPContribs for third-party data [@mpcontrib], and many others. Each of these are powerful tools, but it can require significant effort and expertise to properly integrate several packages into a full-feature server. Meanwhile, Simmate contains modules for each of these features within a single, larger package – e.g. within our `workflows`, `workflow_engine`, `database`, and `website` modules. By maintaining these features within a single space, high level integrated features can more readily be developed. This includes features that are unique to Simmate, such as dynamically built REST APIs and website interfaces. There is also a `run-server` command that compiles all features (including user-defined projects) with minimal setup. Many comparisons can be made between Simmate modules and existing packages from the materials science community, but most notably, Simmate focuses on the unification of components for high-level features and capabilities.

At the lowest level, Simmate is designed specifically for materials science research and the calculation of materials properties. While our current implementation is focused on periodic crystals and *ab-initio* calculations, the framework is built around abstract data types and functionality. This allows easy integration of third-party software and databases. For example, we currently distribute data from other providers (COD [@cod], Materials Project [@matproj], OQMD [@oqmd], and JARVIS [@jarvis]) as well as orchestrate calculations from popular DFT codes (e.g. VASP [@vasp]). Each of these integrations benefit by inheriting from our core data types, which implement features such as error handling and job recovery for workflow integrations as well as the automatic generation of Python APIs, REST APIs, and website interfaces for results and databases. Moreover, data can be converted to other useful Python objects such as those from PyMatGen [@pymatgen] or ASE [@ase], allowing further analysis of the materials. 

Because Simmate removes many obstacles to advanced computation, we anticipate that this code will be utilized by beginners and experts alike. Thus, our tutorials are written for researchers that have never used the command-line or python. However, as users become comfortable, they can begin exploring underlying API and integrated packages for advanced features. Together, these features help Simmate bridge the gap between the existing ecosystems of materials science software, while making production-ready implementations as easy as possible.




# Acknowledgements

S.C.W. acknowledges support of this research by NSF grant DMR-1905294. L.M.M. acknowledges support
by the NSF Graduate Research Fellowship (GRF) under grant DGE-1650116. J.D.S acknowledges
support by the NSF GRF under grant DGE-1650114. While developing this software, computational resources were provided, in part, by the Research Computing Center at the University of North Carolina at Chapel Hill.

# References