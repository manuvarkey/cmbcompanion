#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# tableofpoints.py
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

# Item codes for schedule dialog * DONT CHANGE *
MEAS_NO = 1
MEAS_L = 2
MEAS_DESC = 3
MEAS_CUST = 4

# Define your latex strings here
latex_record = r"""        $slno$ & $data1$ & $data2$ & $data3$ & $data4$ & $data5$ & $data6$ & $data7$ \\
                """
latex_item = r"""
                % Item nnnnnT
                \fakesubsubsection{$cmbitemno1$}
                \noindent\textbf{Item No.$cmbitemno1$}\\
                \noindent $cmbitemdesc1$\\
                \noindent\emph{(Remarks:$cmbremark$)}\\
                \vspace*{-\baselineskip}
                \begin{longtabu} to \textwidth {|X[1,c]|X[10,l]|X[3,r]|X[3,r]|X[3,r]|X[3,r]|X[3,r]|X[5,r]|}
                   \hline
                    \textbf{Sl.\newline No.} & \textbf{N1} & \textbf{N2} & \textbf{N3} & \textbf{N4} & \textbf{N5} & \textbf{N6} & \textbf{Total} \\
                   \hline
                    \endhead
                $cmbrecords$
                    \hline
                      & \textbf{TOTAL} & &  &  &  &  & \textbf{$cmbtotal1$} \\
                   \hline
                      & \emph{Qty C/o MB.No. \nameref{$cmbcarriedover1$}} &  &  &  &  &  & \emph{Pg.No. \pageref{$cmbcarriedover1$}} \phantomsection\label{$cmblabel1$} \\
                   \hline
                \end{longtabu}

             """

class CustomItem:
    def __init__(self):
        def callback_total_item(values,row=None):
            # Populate data values
            data_str = values[1:6]
            data = []
            for x in data_str:
                try:
                    num = eval(x)
                    data.append(num)
                except:
                    data.append(0)
            # Evaluate total
            total = 0
            for x in data:
                total += x
            if len(data) == 0:
                return '0'
            else:
                return str(round(total,3))

        def total_func(item_list,userdata=None):
            total = [0]
            for item in item_list:
                if item is not None:
                    total[0] += item.find_total()[0]
                total[0] = round(total[0],3)
            return total
        
        def total_func_item(values):
            # Populate data values
            data = values[1:6]
            # Evaluate total
            total = 0
            for x in data:
                total += x
            if len(data) == 0:
                return [0]
            else:
                return [total]
                
        def latex_postproc_func(item_list,userdata,latex_buffer,isabstract=False):
            # Do nothing return as it is
            return latex_buffer
        
        # Define your variables here
        self.name = 'Item nnnnnT'
        self.itemnos_mask = [None]
        self.captions = ['Description','N1','N2','N3','N4','N5','Total']
        self.columntypes = [MEAS_DESC,MEAS_L,MEAS_L,MEAS_L,MEAS_L,MEAS_L,MEAS_CUST]
        self.latex_item = latex_item
        self.latex_record = latex_record
        self.captions_udata = []
        self.columntypes_udata = []
        self.user_data_default = []
        # Define functions here
        self.cust_funcs = [None, None, None, None, None, None, callback_total_item]
        self.total_func = total_func
        self.total_func_item = total_func_item
        self.latex_postproc_func = latex_postproc_func
        self.export_abstract = None
        self.dimensions = [[200,80,80,80,80,80,100], [True,False,False,False,False,False,False]]
          
        
        
