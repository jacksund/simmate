#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  1 15:12:50 2023

@author: sweav
"""
import numpy as np
from itertools import combinations
from scipy.spatial import ConvexHull
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d.axes3d import Axes3D
from shapely.geometry import Polygon, MultiPoint
from shapely import errors as se

# %matplotlib qt



directory = Path(".")
structure_file = "POSCAR"
empty_structure_file = "POSCAR_empty"
partition_file = "ELFCAR"
empty_partition_file = "ELFCAR_empty"
charge_file = "CHGCAR"
valence_file = "POTCAR"
print_atom_voxels = False
algorithm = "badelf"# other option is voronoi


plane_points = [[1,0,0],[0,1,0],[0,0,1],[-1,0,0],[0,-1,0],[0,0,-1]]
plane_vectors = plane_points.copy()

planes = [{"point": i, "vector": j} for i, j in zip(plane_points,plane_vectors)]

def get_plane_equation(plane_point, plane_vector):
    x0, y0, z0 = plane_point
    a, b, c = plane_vector
    d = a * x0 + b * y0 + c * z0
    return a,b,c,d

def find_intersection_point(plane1, plane2, plane3):
    
    a1,b1,c1,d1 = get_plane_equation(plane1["point"], plane1["vector"])
    a2,b2,c2,d2 = get_plane_equation(plane2["point"], plane2["vector"])
    a3,b3,c3,d3 = get_plane_equation(plane3["point"], plane3["vector"])
    
    A = np.array([[a1, b1, c1], [a2, b2, c2], [a3, b3, c3]])
    b = np.array([d1, d2, d3])

    # Solve the system of equations
    intersection_point = np.linalg.solve(A, b)

    return intersection_point

def get_plane_sign(point, plane):
    """
    Gets the sign associated with a point compared with a plane. This should
    be negative for an atoms position compared with a plane dividing it from
    other atoms.
    """
    # get all of the points in cartesian coordinates
    x, y, z = plane["point"]
    a, b, c = plane["vector"]
    x1, y1, z1 = point
    value_of_plane_equation = a * (x - x1) + b * (y - y1) + c * (z - z1)
    # get the distance of the point from the plane with some allowance of error.
    if value_of_plane_equation > 1e-6:
        return "positive"
    elif value_of_plane_equation < -1e-6:
        return "negative"
    else:
        return "zero"

def get_all_nodes(planes):
    # create list for points where planes intersect
    intercepts = []
    # iterate through each set of 3 planes
    for combination in combinations(planes,3):
        # try to find an intersection point. We do a try except because if two
        # of the planes are parallel there wont be an intersect point
        try: 
            intercept = find_intersection_point(combination[0],combination[1],combination[2])
        except:
            continue
        
        # Check if the points are one or within the convex shape defined by the
        # planes. Assume this is true at first
        important_intercept = True
        # Check each plane versus the intercept point. If we plug the point into
        # the plane equation it should return as 0 or positive if it is within the
        # shape?
        for plane in planes:
            if get_plane_sign(intercept, plane) in ["positive", "zero"]:
                pass
            else:
                important_intercept = False
                break
        # If the point is bound by all planes, it is an important intercept.
        # append it to our list.
        if important_intercept:
            intercepts.append(intercept)

    return intercepts

def get_nodes_from_results(results):
    atoms_polygon_nodes = {}
    for site_index, neighs in results.items():
        planes = []
        for neigh in neighs.values():
            plane_point = neigh["real_min_point"]
            plane_vector = neigh["normal_vector"]
            planes.append({"point": plane_point, "vector": plane_vector})
        nodes = get_all_nodes(planes)
        atoms_polygon_nodes[site_index] = nodes
    
    return atoms_polygon_nodes

nodes = get_nodes_from_results(results)
# hull = ConvexHull(nodes)

def plot_points(points, ax, fig, color, size=20):
    x = []
    y = []
    z = []
    for point in points:
        x.append(point[0])
        y.append(point[1])
        z.append(point[2])
    ax.scatter(x,y,z, c = color, s = size)
    
def plot_unit_cell(lattice, ax, fig):
    a = np.array(lattice["a"])
    b = np.array(lattice["b"])
    c = np.array(lattice["c"])
    points = [np.array([0,0,0]), a, b, c, a+b, a+c, b+c, a+b+c]
    plot_points(points, ax, fig, "purple")
    
def set_axes_range(x_range, y_range, z_range, ax, fig):
    ax.set_xlim(x_range[0], x_range[1])
    ax.set_ylim(y_range[0], y_range[1])
    ax.set_zlim(z_range[0], z_range[1])    

def transform_list_of_points_to_xyz(points):
    x = []
    y = []
    z = []
    for point in points:
        x.append(point[0])
        y.append(point[1])
        z.append(point[2])
    return x,y,z
        
def plot_atom_vertices(atom_polygons: dict, lattice):
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")
    plot_unit_cell(lattice, ax, fig)
    # num_of_sites = len(atom_polygons)
    color_map = mpl.colormaps.get_cmap('tab10')
    for site, vertices in atom_polygons.items():
        for vertex in vertices:
            color = color_map(site)
            ax.scatter(vertex[0],vertex[1],vertex[2],c=color)
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

def plot_atom_shapes(atom_polygons: dict, lattice):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    plot_unit_cell(lattice, ax, fig)
    # num_of_sites = len(atom_polygons)
    color_map = mpl.colormaps.get_cmap('tab10')
    for site, vertices in atom_polygons.items():
        hull = ConvexHull(vertices)
        # vertices1 = hull.vertices
        triangles = hull.simplices
        
        x,y,z = transform_list_of_points_to_xyz(vertices)

        ax.plot_trisurf(x, y, z, triangles=triangles, color=color_map(site))#, alpha=0.5)

plot_atom_shapes(nodes, lattice)


    
