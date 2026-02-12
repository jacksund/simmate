## nsteadystate
This parameter sets the number of individual workflows to be scheduled at once, effectively setting the queue size of an evolutionary search. The number of workflows run in parallel is determined by the number of `Workers` started. However, the `nsteadystate` value sets the **maximum** number of parallel runs as the queue size will never exceed this value. This parameter is closely tied with `steadystate_sources`.

=== "yaml"
    ``` yaml
    nsteadystate: 50
    ```
=== "toml"
    ``` toml
    nsteadystate = 50
    ```
=== "python"
    ``` python
    nsteadystate = 50
    ```
