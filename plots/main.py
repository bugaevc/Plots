#!/usr/bin/env python3

import cairo
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio
import numpy as np
import sympy
import sys
import math

class App(Gtk.Application):
    MIN_GRID_SPACING = 15 # in pixels

    def __init__(self):
        Gtk.Application.__init__(self,
                                  application_id="io.github.alexhuntley.plots",
                                  flags=Gio.ApplicationFlags.FLAGS_NONE)
    
    def draw(self, da, ctx):
        w, h = da.get_allocated_width(), da.get_allocated_height()

        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        ctx.translate(w/2, h/2)
        ctx.scale(self.scale, self.scale)
        ctx.translate(self.x_offset, self.y_offset)
        ctx.set_line_width(max(ctx.device_to_user_distance(1, 1)))
        # bounds of the view
        x1, y1 = ctx.device_to_user(0, 0)
        x2, y2 = ctx.device_to_user(w+100, h+100)
        
        # Grid
        ctx.set_source_rgb(.8, .8, .8)
        min_spacing_horizontal = (x2-x1)*App.MIN_GRID_SPACING/w
        #min_spacing_vertical = (y2-y1)*App.MIN_GRID_SPACING/h
        spacing_horizontal = pow(10, math.ceil(math.log10(min_spacing_horizontal)))
        x0 = round(x1, -math.ceil(math.log10(min_spacing_horizontal)))
        for i in range(math.ceil(w/App.MIN_GRID_SPACING)):
            ctx.move_to(x0 + i*spacing_horizontal, y1)
            ctx.line_to(x0 + i*spacing_horizontal, y2)
        ctx.stroke()

        # Axes
        ctx.set_source_rgb(.6, .6, .6)
        ctx.move_to(x1, 0)
        ctx.line_to(x2, 0)
        ctx.stroke()
        ctx.move_to(0, y1)
        ctx.line_to(0, y2)
        ctx.stroke()

        ctx.set_source_rgb(.8, 0, 0)
        xs = np.linspace(-self.x_offset-w/2/self.scale,-self.x_offset+w/2/self.scale,w*4)
        ys = self.expr(xs)
        mask = np.logical_and(-ys > y1, -ys < y2)
        mask[:-1] = np.logical_or(mask[:-1], mask[1:])
        mask[1:] = np.logical_or(mask[1:], mask[:-1])
        mask = np.logical_and(mask, np.isfinite(ys))

        skipped = False
        for x, y, m in zip(xs, ys, mask):
            if m:
                if skipped:
                    ctx.move_to(x, -y)
                ctx.line_to(x, -y)
                skipped = False
            else:
                skipped = True
        ctx.stroke()
    
    def do_activate(self):
        self.scale = 50 # in pixels per unit
        x = sympy.symbols('x')
        self.expr = sympy.lambdify(x, 'sin(tan(x))', 'numpy')
        self.x_offset, self.y_offset = 0, 0
        self.ix, self.iy = 0, 0
        self.win = Gtk.ApplicationWindow()
        self.win.connect('destroy', lambda w: Gtk.main_quit())
        self.win.set_default_size(450, 550)
        self.win.set_title("Plots")

        self.drawingarea = Gtk.DrawingArea()
        self.win.add(self.drawingarea)
        self.drawingarea.connect('draw', self.draw)
        self.drawingarea.add_events(Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.drawingarea.connect('scroll_event', self.scroll_zoom)
        
        self.dc = Gtk.GestureDrag(widget=self.drawingarea)

        self.dc.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self.dc.connect('drag-update', self.drag)
        self.dc.connect('drag-begin', self.drag_begin)
        
        headerbar = Gtk.HeaderBar()
        headerbar.set_show_close_button(True)
        self.win.set_titlebar(headerbar)
        
        self.win.show_all()

    def scroll_zoom(self, widget, event):
        _, dx, dy = event.get_scroll_deltas()
        self.scale *= 1-dy/3
        widget.queue_draw()
        
    def drag(self, gesture, dx, dy):
        self.x_offset, self.y_offset = self.ix + dx/self.scale, self.iy + dy/self.scale
        self.drawingarea.queue_draw()

    def drag_begin(self, gesture, start_x, start_y):
        self.ix, self.iy = self.x_offset, self.y_offset


if __name__ == '__main__':
    app = App()
    app.run(sys.argv)
    Gtk.main()