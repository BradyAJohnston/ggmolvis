import bpy
from abc import ABC, abstractmethod
import molecularnodes as mn
from molecularnodes.entities.trajectory import Trajectory
from molecularnodes.entities.trajectory.selections import Selection
import MDAnalysis as mda
import numpy as np
from typing import Union
from pydantic import BaseModel, Field, validator, ValidationError

from . import SESSION
from .base import GGMolvisArtist

from .world import World
from .camera import Camera
from .light import Light
from .properties import Color, Material
from .sceneobjects import SceneObject, Text
from .sceneobjects import Shape, Line
from .sceneobjects import Molecule


class GGMolVis(GGMolvisArtist):
    """Top level class that contains all the elements of the visualization."""
    def __new__(cls):
        if hasattr(SESSION, 'ggmolvis'):
            # If SESSION already has an instance, return that instance
            return SESSION.ggmolvis
        print("Creating new GGMolVis")
        # Otherwise, create a new instance
        instance = super().__new__(cls)
        SESSION.ggmolvis = instance  # Store the instance in SESSION
        instance._initialized = False
        return instance
    

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        super().__init__()
        self.session.ggmolvis = self
        self._artists_dict = {
            'molecules': [],
            'shapes': [],
            'texts': [],
            'cameras': [Camera(name='global_camera')],
            'lights': [],
            'worlds': [World(name='global_world')]
        }
        self._global_world = self.worlds[0]

        self._global_camera = self.cameras[0]

        self._subframes = 0

        # pre-defined camera position
        self._global_camera.world.location.set_coordinates((0, -4, 1.3))
        self._global_camera.world.rotation.set_coordinates((83, 0, 0))

        # set up the scene
        self.set_scene()

        self._update_frame(bpy.context.scene.frame_current)


    def _update_frame(self, frame_number):
        """Update the camera's state for the given frame"""
        for artist in self._artists:
            artist._update_frame(frame_number)

        self._global_camera.world.apply_to(self._global_camera.object, frame_number)

    @property
    def _artists(self):
        return [item for sublist in self._artists_dict.values() for item in sublist]

    @property
    def molecules(self):
        return self._artists_dict['molecules']
    
    @property
    def shapes(self):
        return self._artists_dict['shapes']
    
    @property
    def texts(self):
        return self._artists_dict['texts']
    
    @property
    def cameras(self):
        return self._artists_dict['cameras']
    
    @property
    def lights(self):
        return self._artists_dict['lights']
    
    @property
    def worlds(self):
        return self._artists_dict['worlds']

    @property
    def global_world(self):
        return self._global_world
    
    @property
    def global_camera(self):
        return self._global_camera
    
    @property
    def subframes(self):
        return self._subframes
    
    @subframes.setter
    def subframes(self, value):
        self._subframes = value
        for molecule in self.molecules:
            molecule.trajectory.subframes = value

    def set_scene(self):
        """Set up the scene with transparent background and CYCLES rendering."""
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.render.film_transparent = True

    def molecule(self,
                 universe: Union[mda.AtomGroup, mda.Universe],
                 style: str = 'spheres',
                 name: str = 'atoms',
                 world: World = None,
                 color='default',
                 material='default'):
        molecule = Molecule(atomgroup=universe,
                            style=style,
                            name=name,
                            color=color,
                            material=material)

        if world is not None:
            molecule.world = world
        else:
            molecule.world = self.global_world
        self.molecules.append(molecule)
        return molecule

    def line(self,
             start_points: np.ndarray,
             end_points: np.ndarray,
             world: World = None,
             color='black',
             material='backdrop'
             ):
        
        line = Line(start_points, end_points, color=color, material=material)
        if world is not None:
            line.world = world
        else:
            line.world = self.global_world
        self.shapes.append(line)
        return line