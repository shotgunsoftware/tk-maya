"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
"""
import os
import urllib
import uuid
import sys

from PySide import QtCore, QtGui

class Worker(QtCore.QThread):
    
    work_completed = QtCore.Signal(str, dict)
    work_failure = QtCore.Signal(str, str)
        
    
    def __init__(self, app, parent=None):
        QtCore.QThread.__init__(self, parent)
        self._execute_tasks = True
        self._app = app
        self._queue_mutex = QtCore.QMutex()
        self._queue = []
        self._receivers = {}
        
    def stop(self):
        """
        Stops the worker, run this before shutdown
        """
        self._execute_tasks = False

    def clear(self):
        """
        Empties the queue
        """
        self._queue_mutex.lock()
        try:
            self._queue = []
        finally:
            self._queue_mutex.unlock()
        
    def queue_work(self, worker_fn, params, asap=False):
        """
        Queues up some work.
        Returns a unique identifier to identify this item 
        """
        uid = uuid.uuid4().hex
        
        work = {"id": uid, "fn": worker_fn, "params": params}
        self._queue_mutex.lock()
        try:
            if asap:
                # first in the queue
                self._queue.insert(0, work)
            else:
                self._queue.append(work)
        finally:
            self._queue_mutex.unlock()
        
        return uid

    ############################################################################################
    #

    def run(self):
        
        
        while self._execute_tasks:
            
            self._queue_mutex.lock()
            try:
                queue_len = len(self._queue)
            finally:
                self._queue_mutex.unlock()
            
            if queue_len == 0:
                # polling. TODO: replace with semaphor!
                self.msleep(200)
            
            else:
                # pop queue
                self._queue_mutex.lock()
                try:
                    item_to_process = self._queue.pop(0)
                finally:
                    self._queue_mutex.unlock()

                data = None
                try:
                    data = item_to_process["fn"](item_to_process["params"])
                except Exception, e:
                    if self._execute_tasks:
                        self.work_failure.emit(item_to_process["id"], "An error occured: %s" % e)
                    
                else:
                    if self._execute_tasks:
                        self.work_completed.emit(item_to_process["id"], data)
                