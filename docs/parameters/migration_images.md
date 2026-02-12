## migration_images
The full set of images (including endpoint images) that should be analyzed. Inputs are anything compatible with the `MigrationImages` class of the `simmate.toolkit.diffusion` module, which is effectively a list of `structure` inputs. This includes:

**`MigrationImages` object**

**a list of `Structure` objects**

**a list of filenames (cif or POSCAR)**

=== "yaml"
    ``` yaml
    migration_images:
        - image_01.cif
        - image_02.cif
        - image_03.cif
        - image_04.cif
        - image_05.cif
    ```
=== "toml"
    ``` toml
    migration_images = [
        "image_01.cif",
        "image_02.cif",
        "image_03.cif",
        "image_04.cif",
        "image_05.cif",
    ]
    ```
=== "python"
    ``` python
    migration_images = [
        "image_01.cif",
        "image_02.cif",
        "image_03.cif",
        "image_04.cif",
        "image_05.cif",
    ]
    ```
