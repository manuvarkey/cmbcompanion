#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# views.py
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

import os, logging, copy, re

import flask, flask_socketio
from werkzeug.utils import secure_filename

from . import misc, undo
from .data.measurement import MeasurementItemCustom, RecordCustom

from cmbcompanion import app, project, socketio

# Get logger object
log = logging.getLogger(__name__)

## Module methods

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

def remove_tags(text):
    new_text = re.sub('<[^>]*>', '', text)
    return new_text
    
def render_measurement(path_str=None, activepath_str=None, softload=False):
    # Initialise variables
    if path_str == None:
        project.global_settings['current_page'] = '/measurements'
    else:
        project.global_settings['current_page'] = '/measurements/' + str(path_str)
    activepath = eval(str(activepath_str))
    meas = dict()
    item_list = []
    item_paths = []
    meas['cmb_path'] = None
    meas['cmb_name'] = ''
    meas['meas_path'] = None
    meas['meas_name'] = ''
    meas['measitem_path'] = None
    meas['measitem_name'] = ''
    meas['active'] = None
    path = None
    
    # Evaluate path
    if path_str is not None:
        try:
            path = eval(path_str)
        except:
            log.error("Bad path specified")
            return flask.redirect(project.global_settings['current_page'])
    
    # Case 1: Path is for Root
    if path == None:
        for p1, cmb in enumerate(project.datamodel.cmbs):
            item_list.append(flask.Markup(cmb.get_text()))
            item_paths.append([p1])
    else:
        # Case 2: Path is for CMB
        if len(path) >= 1:
            if len(project.datamodel.cmbs) > path[0]:
                p1 = path[0]
                cmb = project.datamodel.cmbs[p1]
                meas['cmb_path'] = [p1]
                meas['cmb_name'] = cmb.name
            else:
                return flask.redirect(project.global_settings['current_page'])
            if len(path) == 1:
                for p2, measurement in enumerate(cmb.items):
                    item_list.append(flask.Markup(measurement.get_text()))
                    item_paths.append([p1,p2])
        # Case 3: Path is for Measurements
        if len(path) >= 2:
            if len(cmb.items) > path[1]:
                p2 = path[1]
                measurement = cmb.items[p2]
                meas['meas_path'] = [p1,p2]
                meas['meas_name'] = measurement.date
            else:
                return flask.redirect(project.global_settings['current_page'])
            if len(path) == 2:
                for p3, measurement_item in enumerate(measurement.items):
                    item_list.append(flask.Markup(measurement_item.get_text()))
                    item_paths.append([p1,p2,p3])
                if activepath != None:
                    meas['active'] = activepath
        # Case 4: Path is for Measurement Item
        if len(path) == 3:
            if len(measurement.items) > path[2]:
                p3 = path[2]
                measurement_item = measurement.items[p3]
                project.global_settings['measitem_path'] = [p1,p2,p3]
                meas['measitem_path'] = [p1,p2,p3]
                meas['measitem_name'] = flask.Markup('<b>#' + str(p3+1) + '</b>')
                
                # If item already loaded
                if softload:
                    items = project.global_settings['measitem'].get_model()[1][1]
                else:
                    project.global_settings['measitem'] = copy.deepcopy(measurement_item)
                    items = measurement_item.get_model()[1][1]
                meas['measitem_table'] = items
                if not isinstance(measurement_item, MeasurementItemCustom):
                    return flask.redirect('/measurements/' + str(path[0:2]))
                else:
                    meas['measitem_captions'] = ['Sl.No.'] + measurement_item.captions
                    meas['measitem_columntypes'] = measurement_item.columntypes
                    item_itemnos = measurement_item.itemnos
                    item_item_remarks = measurement_item.item_remarks
                    meas['item_remark'] = measurement_item.remark
                    meas['item_itemnos_group'] = zip(item_itemnos, item_item_remarks)
                    
                    sch_items = []
                    # Populate schedule for selection
                    for itemno in project.datamodel.schedule.get_itemnos():
                        item = project.datamodel.schedule[itemno]
                        sch_items.append([item.itemno, item.extended_description_limited, item.unit, item.reference])
                    meas['item_schedule'] = sch_items
        if len(path) > 3:
            return flask.redirect(project.global_settings['current_page'])
        
    meas['items'] = zip(item_paths, item_list)

    return flask.render_template('measurements.html', active='measurements', meas=meas, settings=copy.deepcopy(project.global_settings))

## Sockets,IO methods

@socketio.on('measitem_save')
def measitem_save():
    path = project.global_settings['measitem_path']
    measitem = project.global_settings['measitem']
    model = measitem.get_model()
    project.datamodel.cmbs[path[0]][path[1]][path[2]].set_model(model)
    
@socketio.on('measitem_header_value_changed')
def measitem_header_value_changed(data):
    print(data)
    measitem = project.global_settings['measitem']
    if 'remark' in data:
        measitem.remark = str(data['remark'])
    elif 'item_remark' in data:
        measitem.item_remarks[data['item_remark']] = str(data['value'])
    elif 'itemno' in data:
        if str(data['value']) is 'None':
            measitem.itemnos[data['itemno']] = None
        else:
            measitem.itemnos[data['itemno']] = str(data['value'])
    
    
@socketio.on('measitem_value_changed')
def measitem_value_changed(data):
    row = data['row']
    column = data['column']
    value = remove_tags(data['html'])
    
    # Update duplicate item
    measitem = project.global_settings['measitem']
    record = measitem[row].get_model()
    record[column] = value
    measitem[row].set_model(record, measitem.cust_funcs, measitem.total_func_item, measitem.columntypes)
    
@socketio.on('measitem_page_refresh')
def measitem_page_refresh():
    measitem = project.global_settings['measitem']
    items = []
    for item in measitem:
        items.append(item.get_model_rendered())
    flask_socketio.emit('meas_item_update', items)
            
    
## Route functions

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    filename = None
    # Handle project file opening
    if flask.request.method == 'POST':
        if 'file' not in flask.request.files:
            flask.flash('No Project file Selected','warning')
        else:
            file=flask.request.files['file']
            if file.filename == '':
                flask.flash('No Project file Selected','warning')
            elif file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], 'project.proj')
                file.save(path)
                # Try opening project
                if project.open_project(path):
                    project.global_settings['project_path'] = path
                    flask.flash('Project file loaded sucessfully','success')
                else:
                    project.global_settings['project_path'] = ''
                    flask.flash('Bad project file','danger')
    project.global_settings['current_page'] = '/'
    return flask.render_template('index.html', active='index', filename=filename, settings=project.global_settings)

@app.route('/schedule')
def schedule():
    schedule = project.datamodel.schedule.get_model()
    project.global_settings['current_page'] = '/schedule'
    return flask.render_template('schedule.html', active='schedule', schedule=schedule, settings=project.global_settings)

@app.route('/measurements')
@app.route('/measurements/<path_str>', methods=['GET', 'POST'])
@app.route('/measurements/<path_str>/<activepath_str>', methods=['GET', 'POST'])
def measurements(path_str=None, activepath_str=None):
    
    # Handle button requests
    if flask.request.method == 'POST':
        path = eval(path_str)
        activepath = eval(str(activepath_str))
        # Measurement Items
        if len(path) == 2:
            if 'add' in flask.request.form and flask.request.form['add'] != 'None':
                plugin = flask.request.form.get('add')
                model = MeasurementItemCustom(None, plugin).get_model()
                if activepath:
                    project.datamodel.add_measurement_item_at_node(model, activepath)
                else:
                    project.datamodel.add_measurement_item_at_node(model, path)
            if 'edit' in flask.request.form:
                if activepath != None:
                    return render_measurement(activepath_str)
            elif 'undo' in flask.request.form:
                project.undo()
            elif 'redo' in flask.request.form:
                project.redo()
            elif 'delete' in flask.request.form:
                measurement = project.datamodel.cmbs[path[0]][path[1]]
                if measurement.items:
                    if activepath:
                        project.datamodel.delete_row_meas(activepath)
                    else:
                        project.datamodel.delete_row_meas(path + [measurement.length()-1])
        elif len(path) == 3:
            if 'measitem_add' in flask.request.form:
                measitem = project.global_settings['measitem']
                measitem.append_record(RecordCustom(['']*measitem.model_width() , measitem.cust_funcs, measitem.total_func_item, measitem.columntypes))
            elif 'measitem_addn' in flask.request.form:
                try:
                    no = int(flask.request.form['measitem_addn_no'])
                    if no > 25:
                        no = 25
                    measitem = project.global_settings['measitem']
                    for i in range(no):
                        measitem.append_record(RecordCustom(['']*measitem.model_width() , measitem.cust_funcs, measitem.total_func_item, measitem.columntypes))
                except:
                    flask.flash('Wrong number of rows input', 'error')
            elif 'measitem_delete' in flask.request.form:
                measitem = project.global_settings['measitem']
                if measitem.length() > 0:
                    measitem.remove_record(measitem.length()-1)
            return render_measurement(str(project.global_settings['measitem_path']), None, softload=True)
        
        return flask.redirect(project.global_settings['current_page'])
        
    # Handle website requests
    elif flask.request.method == 'GET':
        return render_measurement(path_str, activepath_str)
        
    
@app.route('/contactus')
def contactus():
    project.global_settings['current_page'] = '/contactus'
    return flask.render_template('contactus.html', active='contactus', settings=project.global_settings)
    
@app.route('/save')
def save():
    path = project.global_settings['project_path']
    if path is not '':
        if project.save_project(path):
            flask.flash('Project successfully saved','success')
        else:
            flask.flash('Error saving project','danger')
    else:
        flask.flash('Project not opened','warning')
    return flask.redirect(project.global_settings['current_page'])
    
@app.route('/close', methods=['GET', 'POST'])
def close():
    # Reset Project
    project.global_settings['project_path'] = ''
    flask.flash('Project successfully closed','success')
    return flask.redirect('/')
    
@app.route('/download')
def download():
    file_ = open(project.global_settings['project_path'], 'r')
    if file_ is not None:
        body = file_.read()
        response = flask.make_response(body)
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = "attachment; filename=project.proj"
        return response
    else:
        return flask.redirect('/')

    
