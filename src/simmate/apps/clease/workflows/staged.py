from simmate.apps.warren_lab.workflows import Relaxation__Vasp__Staged


class Relaxation__Vasp__StagedCluster(Relaxation__Vasp__Staged):
    subworkflow_names = [
        "relaxation.vasp.cluster-low-q",
        "relaxation.vasp.cluster-high-q",
        "static-energy.vasp.cluster-high-qe",
    ]
