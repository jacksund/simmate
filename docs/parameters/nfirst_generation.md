## nfirst_generation
For evolutionary searches, no mutations or "child" individuals will be scheduled until this
number of individuals have been calculated. This ensures we have a good pool of candidates calculated before we start selecting parents and mutating them.

=== "yaml"
    ``` yaml
    nfirst_generation: 15
    ```
=== "toml"
    ``` toml
    nfirst_generation = 15
    ```
=== "python"
    ``` python
    nfirst_generation = 15
    ```
