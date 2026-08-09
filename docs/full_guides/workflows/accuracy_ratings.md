# Accuracy Ratings

!!! warning
    Accuracy ratings are a **work in progress**. These values are heuristic estimates based on the level of theory and convergence settings. They should be used as a guide, not as an absolute measure of error. If you have suggestions on how to improve our rating system, please let us know!

Simmate assigns an **Accuracy Rating** to each workflow as these are helpful to beginners and also provide a quick way to sort workflows for those more experienced. This rating is a value from **0 to 5** that estimates how well the workflow's results (such as energy or geometry) are expected to predict experimental data.

## Rating Scale (0-5)

The current rating system is based on the following classification:

| Rating | Category | Description | Examples |
| :--- | :--- | :--- | :--- |
| **5** | **Hybrid DFT** | Uses hybrid functionals (e.g., HSE06). Currently the most accurate practical predictors for experimental results. | `matproj-hse`, `matproj-hsesol` |
| **4** | **Meta-GGA** | Uses Meta-GGA functionals (e.g., r2SCAN). More accurate than standard GGA for many systems. | `matproj-scan` |
| **3** | **Standard GGA+U** | Robust, modern production settings using GGA or GGA+U (e.g., PBE v2). The industry standard for high-throughput. | `matproj`, `mvl-slab`, `matproj-pbesol` |
| **2** | **Legacy / Older** | Uses older standard settings or less rigorous convergence criteria. | `mit` (Legacy Materials Project) |
| **1** | **Screening / LDA** | Better than tutorial settings but uses faster approximations like LDA or loose convergence. | `quality04`, `lda` presets |
| **0** | **Tutorial / Fast** | Minimal settings intended for learning, testing, or "rough" initial relaxations. Not for publication. | `quality00`, `evo-tutorial` |

## How Ratings are Determined

The `accuracy_rating` is determined by analyzing several factors:

1.  **Level of Theory**: Functional type (LDA < GGA < Meta-GGA < Hybrid).
2.  **Convergence Criteria**: Energy (`EDIFF`) and force (`EDIFFG`) tolerances.
3.  **Basis Set Quality**: Plane-wave cutoff (`ENCUT`) and k-point density (`KSPACING`).
4.  **Pseudopotentials**: Whether high-accuracy or low-accuracy (reduced electron count) potentials are used.
5.  **Benchmark History**: Known performance of the specific preset (e.g. Materials Project vs MIT Project) in the scientific literature.

For more details on the specific settings of a workflow, you can inspect the `_incar` or `_pwscf_options` attributes of the workflow class in the source code or web ui.
