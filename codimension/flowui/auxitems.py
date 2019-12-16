# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2015-2016  Sergey Satskiy <sergey.satskiy@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Auxiliary items on a canvas which do not derive from CellElement"""

# pylint: disable=C0305
# pylint: disable=R0902
# pylint: disable=R0913


from sys import maxsize
from ui.qt import (QPen, QBrush, QPainterPath, Qt, QGraphicsSvgItem,
                   QGraphicsSimpleTextItem, QGraphicsRectItem,
                   QGraphicsPathItem, QGraphicsLineItem)
from .cellelement import CellElement


class SpacerCell(CellElement):

    """A cell which may take some space horizontally or vertically"""

    def __init__(self, ref, canvas, x, y, width=None, height=None):
        CellElement.__init__(self, ref, canvas, x, y)
        self.kind = CellElement.SPACER
        self.height = height
        self.width = width

    def render(self):
        """Renders the cell"""
        if self.width is None:
            self.width = self.canvas.settings.hSpacer
        if self.height is None:
            self.height = self.canvas.settings.vSpacer
        self.minWidth = self.width
        self.minHeight = self.height
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY


class VacantCell(SpacerCell):

    """A vacant cell which can be later used for some other element"""

    def __init__(self, ref, canvas, x, y):
        SpacerCell.__init__(self, ref, canvas, x, y, width=0, height=0)
        self.kind = CellElement.VACANT


class VSpacerCell(SpacerCell):

    """Represents a vertical spacer cell"""

    def __init__(self, ref, canvas, x, y, height=None):
        SpacerCell.__init__(
            self, ref, canvas, x, y, width=0,
            height=canvas.settings.vSpacer if height is None else height)
        self.kind = CellElement.V_SPACER


class HSpacerCell(SpacerCell):

    """Represents a horizontal spacer cell"""

    def __init__(self, ref, canvas, x, y, width=None):
        SpacerCell.__init__(
            self, ref, canvas, x, y,
            width=canvas.settings.hSpacer if width is None else width)
        self.kind = CellElement.H_SPACER


class SVGItem(CellElement, QGraphicsSvgItem):

    """Wrapper for an SVG items on the control flow"""

    def __init__(self, canvas, fName, ref):
        CellElement.__init__(self, ref, canvas, x=None, y=None)
        self.kind = CellElement.SVG

        self.__fName = fName
        QGraphicsSvgItem.__init__(self, self.__getPath(fName))
        self.__scale = 0

    @staticmethod
    def __getPath(fName):
        """Tries to resolve the given file name"""
        from utils.pixmapcache import getPixmapLocation
        path = getPixmapLocation(fName)
        if path is not None:
            return path
        return ''

    def setIconHeight(self, height):
        """Scales the svg item to the required height"""
        rectHeight = float(self.boundingRect().height())
        if rectHeight != 0.0:
            self.__scale = float(height) / rectHeight
            self.setScale(self.__scale)

    def setIconWidth(self, width):
        """Scales the svg item to the required width"""
        rectWidth = float(self.boundingRect().width())
        if rectWidth != 0.0:
            self.__scale = float(width) / rectWidth
            self.setScale(self.__scale)

    def iconHeight(self):
        """Provides the height"""
        return self.boundingRect().height() * self.__scale

    def iconWidth(self):
        """Provides the width"""
        return self.boundingRect().width() * self.__scale

    def mouseDoubleClickEvent(self, event):
        """Handling double click events"""
        if self.ref.kind == CellElement.EXCEPT_MINIMIZED:
            return self.ref.mouseDoubleClickEvent(event)
        return QGraphicsSvgItem.mouseDoubleClickEvent(self, event)

    def getSelectTooltip(self):
        """Provides the tooltip"""
        return "SVG picture for " + self.__fName

    def getProxiedItem(self):
        """Provides the real item for the proxy one"""
        return self.ref


class BadgeItem(CellElement, QGraphicsRectItem):

    """Serves the scope badges"""

    def __init__(self, ref, text):
        CellElement.__init__(self, ref, ref.canvas, None, None)
        QGraphicsRectItem.__init__(self)
        self.kind = CellElement.BADGE
        self.__text = text

        s = ref.canvas.settings

        self.__textRect = s.badgeFontMetrics.boundingRect(0, 0, maxsize,
                                                          maxsize, 0, text)

        self.width = self.__textRect.width() + 2 * s.badgeHSpacing
        self.height = self.__textRect.height() + 2 * s.badgeVSpacing

        self.__bgColor = s.badgeBGColor
        self.__fgColor = s.badgeFGColor
        self.__frameColor = s.badgeBorderColor
        self.__needRect = True

    def setBGColor(self, bgColor):
        """Sets the background color"""
        self.__bgColor = bgColor

    def setFGColor(self, fgColor):
        """Sets the foreground color"""
        self.__fgColor = fgColor

    def setFrameColor(self, frameColor):
        """Sets the frame color"""
        self.__frameColor = frameColor

    def setNeedRectangle(self, value):
        """Sets the need rectangle flag"""
        self.__needRect = value

    def moveTo(self, xPos, yPos):
        """Moves to the specified position"""
        # This is a mistery. I do not understand why I need to divide by 2.0
        # however this works. I tried various combinations of initialization,
        # setting the position and mapping. Nothing works but ../2.0. Sick!
        self.setPos(float(xPos) / 2.0, float(yPos) / 2.0)
        self.setRect(float(xPos) / 2.0, float(yPos) / 2.0,
                     self.width, self.height)

    def withinHeader(self):
        """True if it is within a header"""
        if self.ref.kind in [self.ref.ELSE_SCOPE,
                             self.ref.FINALLY_SCOPE,
                             self.ref.TRY_SCOPE]:
            return True
        if self.ref.kind == self.ref.EXCEPT_SCOPE:
            return self.ref.ref.clause is None
        return False

    def paint(self, painter, option, widget):
        """Paints the badge item"""
        del option
        del widget

        s = self.ref.canvas.settings

        if self.__needRect:
            pen = QPen(self.__frameColor)
            pen.setWidth(s.badgeLineWidth)
            painter.setPen(pen)
            painter.setBrush(QBrush(self.__bgColor))
            painter.drawRoundedRect(self.x(), self.y(),
                                    self.width, self.height,
                                    s.badgeRadius, s.badgeRadius)

        pen = QPen(self.__fgColor)
        painter.setPen(pen)
        painter.setFont(s.badgeFont)
        painter.drawText(self.x() + s.badgeHSpacing,
                         self.y() + s.badgeVSpacing,
                         self.__textRect.width(),
                         self.__textRect.height(),
                         Qt.AlignCenter, self.__text)

    def getSelectTooltip(self):
        """Provides the tooltip"""
        return "Badge '" + self.__text + "'"

    def getProxiedItem(self):
        """Provides the real item for a proxy one"""
        return self.ref



class Connector(CellElement, QGraphicsPathItem):

    """Implementation of a connector item"""

    def __init__(self, canvas, x1, y1, x2, y2):
        CellElement.__init__(self, None, canvas, x=None, y=None)
        QGraphicsPathItem.__init__(self)
        self.kind = CellElement.DEPENDENT_CONNECTOR

        path = QPainterPath()
        path.moveTo(x1, y1)
        path.lineTo(x2, y2)
        self.setPath(path)

        self.penStyle = None
        self.penColor = None
        self.penWidth = None

    def paint(self, painter, option, widget):
        """Paints the connector"""
        color = self.canvas.settings.cfLineColor
        if self.penColor:
            color = self.penColor
        width = self.canvas.settings.cfLineWidth
        if self.penWidth:
            width = self.penWidth

        pen = QPen(color)
        pen.setWidth(width)
        pen.setCapStyle(Qt.FlatCap)
        pen.setJoinStyle(Qt.RoundJoin)
        if self.penStyle:
            pen.setStyle(self.penStyle)
        self.setPen(pen)
        QGraphicsPathItem.paint(self, painter, option, widget)

    @staticmethod
    def getSelectTooltip():
        """Provides the tooltip"""
        return 'Connector'



class RubberBandItem(CellElement, QGraphicsRectItem):

    """Custom rubber band for selection"""

    def __init__(self, canvas):
        CellElement.__init__(self, None, canvas, x=None, y=None)
        QGraphicsRectItem.__init__(self)

        self.kind = CellElement.RUBBER_BAND
        self.__settings = canvas.settings
        self.__x = None
        self.__y = None
        self.__width = None
        self.__height = None

    def setGeometry(self, rect):
        """Sets the geometry"""
        # This is a mistery. I do not understand why I need to divide by 2.0
        # however this works. I tried various combinations of initialisation,
        # setting the position and mapping. Nothing works but ../2.0. Sick!
        self.__x = rect.x() / 2.0
        self.__y = rect.y() / 2.0
        self.__width = rect.width()
        self.__height = rect.height()

        self.setPos(self.__x, self.__y)
        self.setRect(self.__x, self.__y, self.__width, self.__height)

        self.update()

    def paint(self, painter, option, widget):
        """Paints the rubber band"""
        del option
        del widget

        pen = QPen(self.__settings.rubberBandBorderColor)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.__settings.rubberBandFGColor))
        painter.drawRect(self.__x, self.__y,
                         self.__width, self.__height)



class Text(CellElement, QGraphicsSimpleTextItem):

    """Implementation of a text item"""

    def __init__(self, canvas, text):
        CellElement.__init__(self, None, canvas, None, None)
        QGraphicsSimpleTextItem.__init__(self)
        self.kind = CellElement.TEXT

        self.setFont(canvas.settings.badgeFont)
        self.setText(text)

        self.color = None

    def paint(self, painter, option, widget):
        """Paints the text item"""
        color = self.canvas.settings.cfLineColor
        if self.color:
            color = self.color

        self.setBrush(QBrush(color))
        QGraphicsSimpleTextItem.paint(self, painter, option, widget)

    @staticmethod
    def getSelectTooltip():
        """Provides the tooltip"""
        return 'Text'



class Line(CellElement, QGraphicsLineItem):

    """Implementation of the line item"""

    def __init__(self, canvas, x1, y1, x2, y2):
        CellElement.__init__(self, None, canvas, x=None, y=None)
        QGraphicsLineItem.__init__(self, x1, y1, x2, y2)
        self.kind = CellElement.LINE

        self.penStyle = None
        self.penColor = None
        self.penWidth = None

    def paint(self, painter, option, widget):
        """Paints the text item"""
        color = self.canvas.settings.cfLineColor
        if self.penColor:
            color = self.penColor
        width = self.canvas.settings.cfLineWidth
        if self.penWidth:
            width = self.penWidth

        pen = QPen(color)
        pen.setWidth(width)
        pen.setCapStyle(Qt.FlatCap)
        pen.setJoinStyle(Qt.RoundJoin)
        if self.penStyle:
            pen.setStyle(self.penStyle)
        self.setPen(pen)

        QGraphicsLineItem.paint(self, painter, option, widget)

    @staticmethod
    def getSelectTooltip():
        """Provides the tooltip"""
        return 'Line'



class ConnectorCell(CellElement, QGraphicsPathItem):

    """Represents a single connector cell"""

    NORTH = 0
    SOUTH = 1
    WEST = 2
    EAST = 3
    CENTER = 4

    # Connector type. In case of 'if' and groups it is necessary to calculate
    # properly how wide the connector should be. The subKind tells what kind
    # of correction is required
    GENERIC = 100
    TOP_IF = 101
    BOTTOM_IF = 102

    def __init__(self, connections, canvas, x, y):
        """Connections are supposed to be a list of tuples.

        Eample: [ (NORTH, SOUTH), (EAST, CENTER) ]
        """
        CellElement.__init__(self, None, canvas, x, y)
        QGraphicsPathItem.__init__(self)
        self.kind = CellElement.CONNECTOR
        self.subKind = self.GENERIC
        self.connections = connections

    def __hasVertical(self):
        """True if has a vertical part"""
        for conn in self.connections:
            if self.NORTH in conn or self.SOUTH in conn:
                return True
        return False

    def __hasHorizontal(self):
        """True if has a horizontal part"""
        for conn in self.connections:
            if self.EAST in conn or self.WEST in conn:
                return True
        return False

    def render(self):
        """Renders the cell"""
        settings = self.canvas.settings

        if self.__hasVertical():
            self.minWidth = settings.mainLine + settings.hCellPadding
            self.minWidth += self.hShift * 2 * settings.openGroupHSpacer
        else:
            self.minWidth = 0

        if self.__hasHorizontal():
            self.minHeight = 2 * settings.vCellPadding
        else:
            self.minHeight = 0

        self.height = self.minHeight
        self.width = self.minWidth
        return (self.width, self.height)

    def __getY(self):
        """Provides the Y coordinate"""
        row = self.addr[1]
        column = self.addr[0]
        cells = self.canvas.cells
        for index in range(column - 1, -1, -1):
            cell = cells[row][index]
            if cell.isSpacerItem():
                continue
            if cell.scopedItem():
                break
            if cell.kind != CellElement.CONNECTOR:
                return cell.minHeight / 2
        return self.height / 2

    def __getNorthXY(self, baseX):
        """Provides the north coordinates"""
        settings = self.canvas.settings
        if self.subKind == self.BOTTOM_IF:
            cellAbove = self.canvas.cells[self.addr[1] - 1][self.addr[0]]
            if cellAbove.kind == CellElement.VCANVAS:
                baseX += cellAbove.maxGlobalOpenGroupDepth * 2 * \
                         settings.openGroupHSpacer
        return baseX + settings.mainLine, self.baseY

    def __getSouthXY(self, baseX):
        """Provides the south coordinates"""
        settings = self.canvas.settings
        if self.subKind == self.TOP_IF:
            cellBelow = self.canvas.cells[self.addr[1] + 1][self.addr[0]]
            if cellBelow.kind == CellElement.VCANVAS:
                baseX += cellBelow.maxGlobalOpenGroupDepth * 2 * \
                         settings.openGroupHSpacer
        return baseX + settings.mainLine, self.baseY + self.height

    def __getXY(self, location):
        """Provides the location coordinates"""
        settings = self.canvas.settings
        hShift = self.hShift * 2 * settings.openGroupHSpacer

        baseX = self.baseX
        if self.subKind not in [self.TOP_IF, self.BOTTOM_IF]:
            baseX = self.baseX + hShift

        if location == self.NORTH:
            return self.__getNorthXY(baseX)
        if location == self.SOUTH:
            return self.__getSouthXY(baseX)
        if location == self.WEST:
            return baseX, self.baseY + self.__getY()
        if location == self.EAST:
            return baseX + self.width - hShift, self.baseY + self.__getY()

        # It is CENTER
        if self.subKind == self.TOP_IF:
            cellBelow = self.canvas.cells[self.addr[1] + 1][self.addr[0]]
            if cellBelow.kind == CellElement.VCANVAS:
                baseX += cellBelow.maxGlobalOpenGroupDepth * 2 * \
                         settings.openGroupHSpacer
        elif self.subKind == self.BOTTOM_IF:
            cellAbove = self.canvas.cells[self.addr[1] - 1][self.addr[0]]
            if cellAbove.kind == CellElement.VCANVAS:
                baseX += cellAbove.maxGlobalOpenGroupDepth * 2 * \
                         settings.openGroupHSpacer
        return baseX + settings.mainLine, self.baseY + self.__getY()

    def __angled(self, begin, end):
        """Returns True if the connection is not straight"""
        if begin in [self.NORTH, self.SOUTH] and \
           end in [self.WEST, self.EAST]:
            return True
        return end in [self.NORTH, self.SOUTH] and \
               begin in [self.WEST, self.EAST]

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY

        path = QPainterPath()
        for connection in self.connections:
            startX, startY = self.__getXY(connection[0])
            endX, endY = self.__getXY(connection[1])
            if self.__angled(connection[0], connection[1]):
                centerX, centerY = self.__getXY(self.CENTER)
                path.moveTo(startX, startY)
                path.lineTo(centerX, centerY)
                path.lineTo(endX, endY)
            else:
                path.moveTo(startX, startY)
                path.lineTo(endX, endY)
        # It does not look nice so commented out
        #if len(self.connections) == 1:
        #    if self.connections[0][0] == self.NORTH:
        #        if self.connections[0][1] == self.CENTER:
        #            # That's a half connector used when terminal items are
        #            # suppressed.
        #            radius = self.canvas.settings.vCellPadding / 2.0
        #            path.addEllipse(endX - radius / 2.0,
        #                            endY - radius / 2.0, radius, radius)
        self.setPath(path)
        scene.addItem(self)

    def paint(self, painter, option, widget):
        """Draws the code block"""
        settings = self.canvas.settings

        pen = QPen(settings.cfLineColor)
        pen.setWidth(settings.cfLineWidth)
        pen.setJoinStyle(Qt.RoundJoin)
        self.setPen(pen)
        painter.setPen(pen)
        QGraphicsPathItem.paint(self, painter, option, widget)

