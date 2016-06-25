#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# cmbcompanion
#  
#  Copyright 2014 Manu Varkey <manuvarkey@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import logging, tempfile, sys, os, flask, json
from flask_socketio import SocketIO

from . import data, misc, undo

# Get logger object
log = logging.getLogger()
    
# Create flask app
app = flask.Flask(__name__)
# Configure flask app
app.config.from_object('config')
# Configure socketio
socketio = SocketIO(app)

class Project:
    """Class stores all data related to a single project file"""
    
    def __init__(self):
        """Initialise variables"""
        self.datamodel = data.datamodel.DataModel()
        self.project_settings = dict()
        for item_code in misc.global_vars:
            self.project_settings[item_code] = ''
        self.global_settings = {'project_path':'', 'current_page' : '/'}
        
        # Update undo/redo system
        self.stack = undo.Stack()
        undo.setstack(self.stack)
        
        # Setup custom measurement items
        file_names = [f for f in os.listdir(misc.abs_path('data/templates'))]
        module_names = []
        for f in file_names:
            if f[-3:] == '.py' and f != '__init__.py':
                module_names.append(f[:-3])
        module_names.sort()
        module_desc = []
        for module_name in module_names:
            try:
                module = getattr(data.templates, module_name)
                custom_object = module.CustomItem()
                module_desc.append(custom_object.name)
                log.info('Plugin loaded - ' + module_name)
            except ImportError:
                log.error('Error Loading plugin - ' + module_name)
        self.global_settings['module_group'] = zip(module_names, module_desc)
        
    def open_project(self, filename):
        # Get filename and set project as active
        fileobj = open(filename, 'r')
        if fileobj == None:
            log.error("open_project - Error opening file - " + filename)
        else:
            try:
                data_loaded = json.load(fileobj)  # load data structure
                fileobj.close()
                if data_loaded[0] == misc.PROJECT_FILE_VER:
                    self.datamodel.set_model(data_loaded[1])
                    self.project_settings = data_loaded[2]

                    log.info('open_project - Project successfully opened - ' + filename)
                else:
                    log.warning('open_project - Project could not be opened: Wrong file type selected - ' + filename)
                    return False
            except:
                log.exception("Error parsing project file - " + filename)
                return False
        return True
    
    def save_project(self, filename):
        # Parse data into object
        data = []
        data.append(misc.PROJECT_FILE_VER)
        data.append(self.datamodel.get_model())
        data.append(self.project_settings)
        # Try to open file
        fileobj = open(filename, 'w')
        if fileobj == None:
            log.error("save_project - Error opening file - " + filename)
            return False
        json.dump(data, fileobj)
        fileobj.close()
        log.info('save_project -  Project successfully saved')
        return True


    def undo(self):
        """Undo action from stack"""
        log.info('Undo:' + str(self.stack.undotext()))
        undo.setstack(self.stack)
        self.stack.undo()
        self.datamodel.update()
        
    def redo(self):
        """Redo action from stack"""
        log.info('Redo:' + str(self.stack.redotext()))
        undo.setstack(self.stack)
        self.stack.redo()
        self.datamodel.update()

# Create main data object
project = Project()

from . import views

