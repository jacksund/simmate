<< _register_calc >>
from_run_context
from_toolkit

<< _update_database_with_results >> 
This function retrieves from _register_calc and includes the following methods:
- update_database_from_results
- update_from_results
    - update_from_toolkit
        - from_toolkit(as_dict=True)
    - update_from_directory
        - from_directory(as_dict=True)
            - from_vasp_directory(as_dict=True) ---> Note: Unexpected as_dict
                - from_vasp_run(as_dict=True)
        - update_from_toolkit()
            - from_toolkit(as_dict=True)

<< load_completed_calc >>
This function includes the following methods:
- from_toolkit
- from_directory
    - from_vasp_directory
        - from_vasp_run