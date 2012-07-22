"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
"""
import os
import sys

from PySide import QtCore, QtGui 

class ThumbnailLabel(QtGui.QLabel):

    def __init__(self, parent=None):
        QtGui.QLabel.__init__(self, parent)

    def setPixmap(self, pixmap):
        
        if pixmap.height() > 80 or pixmap.width() > 120:
            # scale it down to 120x80
            pixmap = pixmap.scaled( QtCore.QSize(120,80), QtCore.Qt.KeepAspectRatio)
        
#        # now add a drop shadow
#        # todo - perhaps later?
#        rendered_pixmap = QtGui.QPixmap(130, 90)
#        rendered_pixmap.fill(QtCore.Qt.transparent)
#        
#        painter = QtGui.QPainter(rendered_pixmap)
#        
#        # first draw a rectangle in the background
#        gradient = QtGui.QLinearGradient() 
#        gradient.setStart(0,0)
#        gradient.setFinalStop(120,80);
#        #grad_start = QtGui.QColor(150,150,150,125)
#        #grand_end = QtGui.QColor(225,225,225,125)
#
#        grad_start = QtGui.QColor(255,0,0,125)
#        grand_end = QtGui.QColor(0,0,255,125)
#
#        gradient.setColorAt(0, grad_start )
#        gradient.setColorAt(1, grand_end )
#        brush = QtGui.QBrush(gradient)
#        rect = QtCore.QRectF(8, 8, 120, 80)
#        painter.fillRect(rect, brush)
#        
#        # and the image on top
#        painter.drawPixmap(QtCore.QPointF(5,5), pixmap)
#        
#        painter.end()
#        # process the pixmap to fit it into a 130x90 px continer
        
        
        QtGui.QLabel.setPixmap(self, pixmap)

