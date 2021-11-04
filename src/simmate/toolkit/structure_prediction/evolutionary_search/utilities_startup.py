# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------

# DYNAMIC IMPORTS
from inspect import signature

# from importlib import import_module
# mutation_module = import_module('pymatdisc.transformations.mutation')

# DYNAMIC VARIABLE GRAB
# bar = globals()['foo'] # this is much faster than eval
# # or
# bar = eval('foo')


def dynamic_init_mutator(mutation_class, mutation_options, composition=None):

    # note that mutation_options is a dict of custom inputs to use on the class mutation_class

    import pymatdisc.core.transformations.all as mutation_module

    # if the mutation class is a string, then assume we want to import from the mutation_module
    if type(mutation_class) == str:
        mutation_class = getattr(mutation_module, mutation_class)
    # otherwise, the user is trying to use their own module/class and we already have that set

    # now that we have the class, we want to initiate it with the settings provided
    # we also need to see if composition is a required input, which we don't require the user to specify for convenience
    mutation_class_parameters = signature(mutation_class).parameters

    #!!! in the future, should I just require that all mutators take composition (or **kwargs) as an input even if they don't need it?
    # now we can init with the dictionary of options depending on if composition is needed or not
    if "composition" in mutation_class_parameters:
        mutation_object = mutation_class(composition, **mutation_options)
    else:
        mutation_object = mutation_class(**mutation_options)

    # we now have the final mutation object instance and can return it
    return mutation_object


def dynamic_init_creator(
    cs_class, cs_options, composition=None
):  #!!! change to name & custom_args?? Also what if composition is required?

    import pymatdisc.core.creators.structure as structure_creators_module
    import pymatdisc.core.creators.lattice as lattice_creators_module
    import pymatdisc.core.creators.sites as sites_creators_module
    import pymatdisc.core.creators.vector as vector_creators_module

    # There is a lot going on in this function because creation.structure functions can
    # have sub classes of creation.lattice/sites/vectors, which make this difficult to read.
    # To understand what's going on here, you should first look at the simpler case of
    # dynamically importing mutators (below). I leave comments out here, because I was
    # struggling to write this in a clean way -- and comments made it even harder.
    #!!! consider changing this method entirely or cleaning it up in the future

    # my variable names got too long below, so I used this shorthand:
    # cs_ = creation_structure_
    # cl_ = creation_lattice_
    # cx_ = creation_sites_

    if type(cs_class) == str:
        cs_class = getattr(structure_creators_module, cs_class)

    cs_parameters = signature(cs_class).parameters

    # really I have to ensure methods are Objects and not Strings
    # so you'll see me dynamically load a class and then override an options dictionary with the class
    if (
        "lattice_generation_method" in cs_parameters
        and "lattice_generation_method" in cs_options
    ):

        cl_class = cs_options["lattice_generation_method"]

        if type(cl_class) == str:
            cl_class = getattr(lattice_creators_module, cl_class)
            cs_options["lattice_generation_method"] = cl_class

        if "lattice_gen_options" in cs_options:
            cl_options = cs_options["lattice_gen_options"]
        else:
            cl_options = {}

        # cl_parameters = signature(cl_class).parameters # for reference, not used

        #!!! BUG - fails "'vector_generation_method' in cl_parameters and" check when support is in the kwargs...
        #!!! Therefore, I need to assume the user knows what they are doing. So I remove the check to see if
        #!!! the method accepts the given parameter.
        #!!! I could just remove all cases of thiss... Should remove the bug. Users will get an 'unexpected keyword' error which is fine
        if "vector_generation_method" in cl_options:

            cv_class = cl_options["vector_generation_method"]

            if type(cv_class) == str:
                cv_class = getattr(vector_creators_module, cv_class)
                cl_options["vector_generation_method"] = cv_class

        #!!! BUG - fails "angle_generation_method' in cl_parameters and" check (same bug as mention right above this)
        if "angle_generation_method" in cl_options:

            ca_class = cl_options["angle_generation_method"]

            if type(ca_class) == str:
                ca_class = getattr(vector_creators_module, ca_class)
                cl_options["angle_generation_method"] = ca_class

    if (
        "site_generation_method" in cs_parameters
        and "site_generation_method" in cs_options
    ):

        cx_class = cs_options["site_generation_method"]

        if type(cx_class) == str:
            cx_class = getattr(sites_creators_module, cx_class)
            cs_options["site_generation_method"] = cx_class

        if "site_gen_options" in cs_options:
            cx_options = cs_options["site_gen_options"]
        else:
            cx_options = {}

        # cx_parameters = signature(cx_class).parameters # for reference, not used

        #!!! BUG - fails "'coords_generation_method' in cx_parameters and " check (same bug as mention right above this)
        if "coords_generation_method" in cx_options:

            cc_class = cl_options["coords_generation_method"]

            if type(cc_class) == str:
                cc_class = getattr(vector_creators_module, cc_class)
                cx_options["coords_generation_method"] = cc_class

    # we have now converted of strings to classes
    # we can now run init on the structure creation class

    #!!! in the future, should I just require that all structure creators take composition (or **kwargs) as an input even if they don't need it?
    # now we can init with the dictionary of options depending on if composition is needed or not
    if "composition" in cs_parameters:
        cs_object = cs_class(composition, **cs_options)
    else:
        cs_object = cs_class(**cs_options)

    # we now have the final structure creation object instance and can return it
    return cs_object


def dynamic_init_stopcondition(sc_class, sc_options, composition=None):

    # note that sc_options is a dict of custom inputs to use on the class sc_class

    import pymatdisc.engine.stopconditions as sc_module

    # if the sc class is a string, then assume we want to import from the sc_module
    if type(sc_class) == str:
        sc_class = getattr(sc_module, sc_class)
    # otherwise, the user is trying to use their own module/class and we already have that set

    # now that we have the class, we want to initiate it with the settings provided
    # we also need to see if composition is a required input, which we don't require the user to specify for convenience
    sc_class_parameters = signature(sc_class).parameters

    #!!! in the future, should I just require that all mutators take composition (or **kwargs) as an input even if they don't need it?
    # now we can init with the dictionary of options depending on if composition is needed or not
    if "composition" in sc_class_parameters:
        sc_object = sc_class(composition, **sc_options)
    else:
        sc_object = sc_class(**sc_options)

    # we now have the final trigger object instance and can return it
    return sc_object


def dynamic_init_selector(s_class, s_options):

    # note that a_options is a dict of custom inputs to use on the class s_class

    import pymatdisc.engine.selectors as s_module

    # if the a class is a string, then assume we want to import from the a_module
    if type(s_class) == str:
        s_class = getattr(s_module, s_class)
    # otherwise, the user is trying to use their own module/class and we already have that set

    # init the class
    s_object = s_class(**s_options)

    # we now have the final trigger object instance and can return it
    return s_object


def dynamic_init_executor(e_class, e_options):

    # note that a_options is a dict of custom inputs to use on the class s_class

    import pymatdisc.engine.executors as e_module

    # if the a class is a string, then assume we want to import from the a_module
    if type(e_class) == str:
        e_class = getattr(e_module, e_class)
    # otherwise, the user is trying to use their own module/class and we already have that set

    # init the class
    e_object = e_class(**e_options)

    # we now have the final trigger object instance and can return it
    return e_object


#!!! Workflows are simply functions right now. This will likely change to Class in the future.
def dynamic_init_workflow(wf):

    # note that a_options is a dict of custom inputs to use on the class s_class

    import pymatdisc.engine.workflows as wf_module

    # if the a class is a string, then assume we want to import from the a_module
    if type(wf) == str:
        wf = getattr(wf_module, wf)
    # otherwise, the user is trying to use their own module/class and we already have that set

    # we now have the final trigger object instance and can return it
    return wf