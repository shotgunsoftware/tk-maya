"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
"""
import urlparse
import os
import urllib
import shutil
import sys

try:
    from PyQt4 import QtCore, QtGui
    from .ui_pyqt.item import Ui_Item
    USING_PYQT = True
except:
    from PySide import QtCore, QtGui
    from .ui_pyside.item import Ui_Item
    USING_PYQT = False 

from .list_base import ListBase

class ListItem(ListBase):
    
    def __init__(self, app, worker, parent=None):
        ListBase.__init__(self, app, worker, parent)

        # set up the UI
        self.ui = Ui_Item() 
        self.ui.setupUi(self)
        self._selected = False
        self._worker = worker
        self._worker_uid = None
        
        # spinner
        self._spin_icons = []
        self._spin_icons.append(QtGui.QPixmap(":/res/thumb_loading_1.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/thumb_loading_2.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/thumb_loading_3.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/thumb_loading_4.png")) 
        
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect( self._update_spinner )
        self._current_spinner_index = 0

    def supports_selection(self):
        return True

    def set_selected(self, status):
        self._selected = status
        if self._selected:
            self.ui.background.setStyleSheet("background-color: #707070; border: none")
        else:
            self.ui.background.setStyleSheet("")
            
    def is_selected(self):
        return self._selected
            
    def set_details(self, txt):
        self.ui.details.setText(txt)

    def get_details(self):
        return self.ui.details.text()

    def set_thumbnail(self, url):
        
        if url.startswith("http"):
            # start spinning
            self._timer.start(100)
            
            self._worker_uid = self._worker.queue_work(self._download_thumbnail, {"url": url})
            self._worker.work_completed.connect(self._on_worker_task_complete)
        else:
            # assume url is a path on disk or resource
            self.ui.thumbnail.setPixmap(QtGui.QPixmap(url))
            
        
    ############################################################################################
    # internal stuff
        
    def _update_spinner(self):
        """
        Animate spinner icon
        """
        self.ui.thumbnail.setPixmap(self._spin_icons[self._current_spinner_index])
        self._current_spinner_index += 1
        if self._current_spinner_index == 4:
            self._current_spinner_index = 0            
        
    def _download_thumbnail(self, data):
        url = data["url"]
        
        # first check in our thumbnail cache
        thumb_cache_root = os.path.join(self._app.tank.project_path, "tank", "cache", "thumbnails")
        
        url_obj = urlparse.urlparse(url)
        url_path = url_obj.path
        path_chunks = url_path.split("/")
        
        path_chunks.insert(0, thumb_cache_root)
        # now have something like ["/studio/proj/tank/cache/thumbnails", "", "thumbs", "1", "2", "2.jpg"]
        
        # treat the list of path chunks as an arg list
        path_to_cached_thumb = os.path.join(*path_chunks)
        
        if os.path.exists(path_to_cached_thumb):
            # cached! sweet!
            return {"thumb_path": path_to_cached_thumb }
        
        # ok so the thumbnail was not in the cache. Get it.
        try:
            (temp_file, stuff) = urllib.urlretrieve(url)
        except Exception, e:
            print "Could not download data from the url '%s'. Error: %s" % (url, e)
            return None

        # now try to cache it
        try:
            self._app.tank.execute_hook("create_folder", path=os.path.dirname(path_to_cached_thumb))
            shutil.copy(temp_file, path_to_cached_thumb)
        except Exception, e:
            print "Could not cache thumbnail %s in %s. Error: %s" % (url, path_to_cached_thumb, e)
        
        return {"thumb_path": temp_file }
        
    def _on_worker_task_complete(self, uid, data):
        if uid != self._worker_uid:
            return
            
        # stop spin
        self._timer.stop()
            
        # set thumbnail! 
        try:
            path = data.get("thumb_path")
            self.ui.thumbnail.setPixmap(QtGui.QPixmap(path))
        except:
            self.ui.thumbnail.setPixmap(QtGui.QPixmap(":/res/thumb_empty.png"))

