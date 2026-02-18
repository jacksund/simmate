
This is the maximum stoichiometric ratio that will be analyzed. In a binary system evolutionary search, this will only look at non-reduced compositions up to the max_stoich_factor. For example, this means Ca2N and max factor of 4 would only look up to Ca8N4 and skip any compositions with more atoms (e.g. Ca10N5 is skipped)

=== "yaml"
    ``` yaml
    max_stoich_factor: 5
    ```
=== "toml"
    ``` toml
    max_stoich_factor = 5
    ```
=== "python"
    ``` python
    max_stoich_factor = 5
    ```
