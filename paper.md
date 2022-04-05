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

Over the past decade, the automation of electronic structure codes has led to many large-scale initiatives for materials discovery, such as the Materials Project `[@matproj]`, AFLOW `[@aflow]`, OQMD `[@oqmd]`, JARVIS `[@jarvis]`, and others. Each of these projects facilitate the creation and distribution of materials science data to the broader researcher community through databases, workflow libraries, and web interfaces. However, each of these software ecosystems (i.e. the collection of software used by a specific project) still possess several pain-points for users attempting to implement these new standards for computational research. Proper setup involves learning how (i) workflows are defined/orchestrated, (ii) how databases are built/accessed, and (iii) how website interfaces/APIs make results accessible to the community, where each component requires learning a new package and (more importantly) learning how that package integrates with others. As a result, it can be difficult to integrate several smaller packages when building a production-ready server and database for materials science research.

To address this, we developed the Simulated Materials Ecosystem (Simmate). Simmate strives to simplify the process for researchers who are  trying to set up a full-featured server. For the purposes of beginners, we desired a framework that could run locally without requiring any additional setup. For the purposes of experts, we sought to facilitate scaling of calculations across any number of resources. Simmate accomplishes this by building on top of popular, well-established packages for workflow orchestration, database management, and materials science analysis. This includes integration with high-level, beginner-friendly packages such as Django, Dask, Prefect, and PyMatGen. The use of popular packages also lets Simmate users take advantage of these packages' large user communities, abundant guides, and robust coding standards, while Simmate handles the integration of these packages in the context of materials science. Because Simmate removes many obstacles to advanced computation, we anticipate that this code will be utilized by beginners and experts alike. Thus, our tutorials are written for researchers that have never used the command-line or python However, as users become comfortable, they can begin exploring underlying API and integrated packages for advanced features.

Simmate is designed specifically for materials science research and the calculation of materials properties. While our current implementation is focused on periodic crystals and ab initio calculations, the framework is built around abstract data types and functionality; this allows easy integration of third-party software and databases. For example, we currently support the distribution of data from other providers (COD `[@cod]`, Materials Project `[@matproj]`, OQMD `[@oqmd]`, and JARVIS `[@jarvis]`) as well as orchestrate calculations from popular DFT codes (e.g. VASP `[@vasp]`). Each of these integrations benefit by inheriting from our core data types, which implement features such as error handling and job recovery for workflow integrations as well as the automatic generation of Python APIs, REST APIs, and website interfaces for results and databases. Moreover, data can be converted to other useful Python objects such as those from PyMatGen or ASE, allowing further analysis of the materials. Together, these features help Simmate bridge the gap between the existing ecosystems of materials science software, while making production-ready implementations as easy as possible.


# Acknowledgements

S.C.W. acknowledges support of this research by NSF grant DMR-1905294. L.M.M. acknowledges support
by the NSF Graduate Research Fellowship (GRF) under grant DGE-1650116. J.D.S acknowledges
support by the NSF GRF under grant DGE-1650114. While developing this software, computational resources were provided, in part, by the Research Computing Center at the University of North Carolina at Chapel Hill.

# References