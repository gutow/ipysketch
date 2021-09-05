from tkinter import *
from tkinter import ttk, colorchooser
import os
import re
import sys

import pickle
from PIL import Image, ImageTk, ImageDraw
from tkinter import Tk, Frame, Button

from tkinter import LEFT, TOP, X, FLAT, RAISED

import pkg_resources
import pathlib

from ipysketch.model import Pen, SketchModel, Circle, Point, Vector, Path

MODE_WRITE = 1
MODE_ERASE = 2
MODE_LASSO = 3


class Toolbar(Frame):

    def __init__(self, master, app):
        super().__init__(master, bd=1, relief=RAISED)
        self.parent = master

        self.app = app
        self.save_button = self.create_button('save-60.png')
        self.pen_button = self.create_button('pen-60.png')
        self.erase_button = self.create_button('eraser-60.png')
        self.undo_button = self.create_button('undo-50.png')
        self.redo_button = self.create_button('redo-50.png')

        self.lasso_button = self.create_button('lasso-80.png')

        self.color_panel = PenColorPanel(self)
        self.color_panel.pack(side=LEFT, padx=2, pady=2)

        self.color_button = self.create_button('colors.png')
        self.color_button.pack(side=LEFT, padx=2, pady=2)

        self.line_width_panel = PenWidthPanel(self)
        self.line_width_panel.pack(side=LEFT, padx=2, pady=2)

        self.line_width_scale = Scale(self, from_=1, to=30, orient=HORIZONTAL)
        self.line_width_scale.set(self.line_width_panel.selected_button.line_width)
        self.line_width_scale.bind('<ButtonRelease-1>', self.line_width_panel.set_width)
        self.line_width_scale.pack(side=LEFT, padx=2, pady=2)

    def create_button(self, file):

        img = pkg_resources.resource_filename('ipysketch', 'assets/' + file)
        img = Image.open(img)
        img = img.resize((30, 30))
        img = ImageTk.PhotoImage(img)

        #style = ttk.Style()
        #style.map(
        #    "Custom.TButton",
        #    image=[
        #        ("disabled", img),
        #        ("!disabled", img),
        #        ("active", img)
        #    ]
        #)

        #button = ttk.Button(self, style=style)
        button = Button(self, image=img, relief=RAISED)
        button.image = img
        button.pack(side=LEFT, padx=2, pady=2)
        return button

    def save(self):
        with open(pathlib.Path.cwd() / (self.app.model.name + '.isk'), 'wb') as f:
            pickle.dump(self.app.model, f)


class PenWidthPanel(Frame):

    def __init__(self, master, *args, **kwargs):
        super(PenWidthPanel, self).__init__(master)
        self.master = master

        self.button_1 = PenWidthButton(self, lw=2)
        self.button_1.bind('<Button-1>', self.handle)
        self.button_1.pack(side=LEFT, padx=2, pady=2)
        self.button_2 = PenWidthButton(self, lw=4)
        self.button_2.bind('<Button-1>', self.handle)
        self.button_2.pack(side=LEFT, padx=2, pady=2)
        self.button_3 = PenWidthButton(self, lw=8)
        self.button_3.bind('<Button-1>', self.handle)
        self.button_3.pack(side=LEFT, padx=2, pady=2)

        self._selected_btn = self.button_1
        self._selected_btn.set_selected(True)

    @property
    def selected_button(self):
        return self._selected_btn

    def handle(self, event):
        if event.widget != self._selected_btn:
            self._selected_btn.set_selected(False)
            self._selected_btn = event.widget
            self._selected_btn.set_selected(True)
            self.master.line_width_scale.set(self._selected_btn.line_width)

    def set_width(self, event):
        lw = event.widget.get()
        self.selected_button.set_width(lw)


class PenWidthButton(Canvas):

    def __init__(self, master, lw):
        super(PenWidthButton, self).__init__(master, width=30, height=30, relief=FLAT, bd=1)
        self.master = master
        self.line_width = lw
        self.is_selected = False
        self.set_selected(False)
        self.draw()

    def set_width(self, lw):
        self.line_width = lw
        self.draw()

    def set_selected(self, yesno):
        self.is_selected = yesno
        self.draw()

    def draw(self):
        self.delete('all')
        if self.is_selected:
            self.create_rectangle((1, 1, 30, 30), width=1)
        self.create_line((0, 15, 30, 15), width=self.line_width)


class PenColorPanel(Frame):

    def __init__(self, master):
        super(PenColorPanel, self).__init__(master)

        self.button_1 = PenColorButton(self, '#000000')
        self.button_1.bind('<Button-1>', self.handle)
        self.button_1.pack(side=LEFT, padx=2, pady=2)

        self.button_2 = PenColorButton(self, '#FF0000')
        self.button_2.bind('<Button-1>', self.handle)
        self.button_2.pack(side=LEFT, padx=2, pady=2)

        self.button_3 = PenColorButton(self, '#0000FF')
        self.button_3.bind('<Button-1>', self.handle)
        self.button_3.pack(side=LEFT, padx=2, pady=2)

        self.button_1.set_selected(True)
        self._selected_button = self.button_1

    @property
    def selected_button(self):
        return self._selected_button

    def handle(self, event):
        self._selected_button.set_selected(False)
        self._selected_button = event.widget
        self._selected_button.set_selected(True)


class PenColorButton(Canvas):

    def __init__(self, master, color):
        super(PenColorButton, self).__init__(master, width=30, height=30)
        self.color = color
        self.set_selected(False)

    def draw(self):
        self.delete('all')
        if self.is_selected:
            self.create_rectangle((1, 1, 30, 30), width=1)
        self.create_oval((8, 8, 22, 22), fill=self.color)

    def set_selected(self, yesno):
        self.is_selected = yesno
        self.draw()

    def set_color(self, color):
        self.color = color
        self.draw()

class Sketchpad(Canvas):

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, background='white', cursor='cross', **kwargs)

        self.app = app
        self.bind('<Button-1>', self.on_button_down)
        self.bind('<ButtonRelease-1>', self.on_button_up)
        self.bind('<B1-Motion>', self.on_move)

        self.current_pen = None
        self.color = (0, 0, 0), '#000000'

        self._lasso_path = None
        self.selected_paths_uuids = []

    def on_button_down(self, event):
        if not self.contains(event):
            return

        self.current_action = {}

        if self.app.mode == MODE_WRITE:
            self.app.trigger_action_begins()
            self.current_action['type'] = 'write'
            self.app.model.start_path(event.x, event.y, self.app.get_current_pen())
        elif self.app.mode == MODE_ERASE:
            self.app.trigger_action_begins()
            self.current_action['type'] = 'erase'
            if self.delete_paths_at(event.x, event.y, radius=10):
                self.draw_all()
        elif self.app.mode == MODE_LASSO:

            if self.selected_paths_uuids:

                for path in self.app.model.filter_by_uuids(self.selected_paths_uuids):
                    circle = Circle((event.x, event.y), 10)
                    if path.overlaps(circle):
                        self.current_action['type'] = 'transform'
                        self.current_action['start_point'] = Point((event.x, event.y))
                if 'type' not in self.current_action:
                    self.current_action['type'] = 'select'
                    self.selected_paths_uuids = []
                    self.draw_all()
            else:
                self.current_action['type'] = 'select'

            if self.current_action['type'] == 'select':
                self._lasso_path = Path()
                self._lasso_path.pen.dash = (3, 5)
                self._lasso_path.add_point(event.x, event.y)
            else:
                self.app.trigger_action_begins()

    def delete_paths_at(self, x, y, radius):
        paths_to_delete = self.app.model.find_paths(x, y, radius=radius)
        for p in paths_to_delete:
            self.app.model.remove(p)
        return len(paths_to_delete) > 0

    def on_button_up(self, event):
        if self.app.mode == MODE_WRITE:
            pass # nothing to do any more
        elif self.app.mode == MODE_LASSO:
            if self.current_action['type'] == 'select':
                paths = []
                for path in self.app.model.paths:
                    for pt in path.points:
                        if self._lasso_path.contains(pt):
                            paths.append(path.uuid)
                            break
                self.selected_paths_uuids = paths

                self._lasso_path = None
                self.draw_all()
            elif self.current_action['type'] == 'transform':
                for path in self.app.model.paths:
                    path.apply_offset()

        self.current_action = None

    def on_move(self, event):

        if not self.contains(event):
            return

        if not self.current_action:
#        if not self.app.mode == MODE_ERASE and not self.app.mode == MODE_LASSO:
            return

        if self.app.mode == MODE_WRITE:
            self.app.model.add_to_path(event.x, event.y)
            self._add_line()

        elif self.app.mode == MODE_ERASE:
            if self.delete_paths_at(event.x, event.y, radius=10):
                self.draw_all()
        elif self.app.mode == MODE_LASSO:
            if self.current_action['type'] == 'select':
                if self._lasso_path is not None:
                    self._lasso_path.add_point(event.x, event.y)
                    self.draw_line(self._lasso_path.points[-2], self._lasso_path.points[-1],
                                   self._lasso_path.pen,
                                   dash=self._lasso_path.pen.dash)
                    return
            elif self.current_action['type'] == 'transform':
                offset = Point((event.x, event.y)) - self.current_action['start_point']
                for path in self.app.model.paths:
                    if path.uuid in self.selected_paths_uuids:
                        path.offset = offset
                self.draw_all()

    def _add_line(self):
        path = self.app.get_current_path()
        p_from, p_to = path.points[-2], path.points[-1]
        self.draw_line((p_from.x, p_from.y), (p_to.x, p_to.y), path.pen)

    def contains(self, event):
        w, h = self.get_size()
        bd = 5
        return bd < event.x < w - bd and bd < event.y < h - bd

    def get_size(self):
        return self.winfo_width(), self.winfo_height()

    def draw_all(self):
        self.delete('all')

        for path in self.app.model.paths:
            if path.uuid in self.selected_paths_uuids:
                for line in path.lines_flat():
                    self.draw_line((line[0], line[1]), (line[2], line[3]), path.pen, color='#00FFFF', width=path.pen.width + 4, dash=(3, 5))

            for line in path.lines_flat():
                self.draw_line((line[0], line[1]), (line[2], line[3]), path.pen)

        if self._lasso_path:
            for line in self._lasso_path.lines_flat():
                self.draw_line((line[0], line[1]), (line[2], line[3]), self._lasso_path.pen)

    def draw_line(self, start, end, pen, **kwargs):

        cfg = {
            'width': kwargs.get('width', pen.width),
            'fill': kwargs.get('color', pen.color),
            'dash': kwargs.get('dash', pen.dash),
            'capstyle': ROUND
        }

        self.create_line((start[0], start[1], end[0], end[1]), cfg)


class SketchApp(object):

    def __init__(self, name):

        self.history = [SketchModel(name)]
        self._model_ptr = 0

        root = Tk()
        root.title('ipysketch: ' + name)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.geometry('1024x768+200+200')

        toolbar = Toolbar(root, self)
        toolbar.grid(column=0, row=0, sticky=(N, W, E, S))

        pad = Sketchpad(root, self)
        pad.grid(column=0, row=1, sticky=(N, W, E, S), padx=(5, 5), pady=(5, 5))

        self.root = root
        self.toolbar = toolbar
        self.pad = pad

        #self.toolbar.save_button.bind('<Button-1>', self.save)
        self.toolbar.save_button.configure(command=self.save)
        #self.toolbar.pen_button.bind('<Button-1>', self.set_write_mode)
        self.toolbar.pen_button.configure(command=self.set_write_mode)
        self.toolbar.erase_button.bind('<Button-1>', self.set_erase_mode)
        self.toolbar.lasso_button.bind('<Button-1>', self.set_lasso_mode)
        self.toolbar.color_button.bind('<Button-1>', self.choose_color)
        self.toolbar.undo_button.bind('<Button-1>', self.undo_action)
        self.toolbar.redo_button.bind('<Button-1>', self.redo_action)

        # Load drawing, if available
        isk_file = pathlib.Path.cwd() / str(name + '.isk')
        if os.path.exists(isk_file):
            with open(isk_file, 'rb') as f:
                self.model = pickle.load(f)
            self.pad.draw_all()

        self.mode = MODE_WRITE
        self.root.attributes('-topmost', True)

    def get_current_line_width(self):
        return self.toolbar.line_width_panel.selected_button.line_width

    def get_current_color(self):
        return self.toolbar.color_panel.selected_button.color

    def get_current_path(self):
        return self.model.paths[-1]

    def get_current_pen(self):
        pen = Pen()
        pen.color = self.toolbar.color_panel.selected_button.color
        pen.width = self.toolbar.line_width_panel.selected_button.line_width
        return pen

    @property
    def model(self):
        return self.history[self._model_ptr]

    @model.setter
    def model(self, value):
        self.history[self._model_ptr] = value

    def run(self):
        self.root.mainloop()

    def save(self):

        with open(pathlib.Path.cwd() / (self.model.name + '.isk'), 'wb') as f:
            pickle.dump(self.model, f)

        self.export_to_png()

    def export_to_png(self):
        ul, lr = self.model.get_bounding_box()

        width = lr.x - ul.x
        height = lr.y - ul.y
        width += 4
        height += 4

        maxw = 0
        for p in self.model.paths:
            if p.pen.width / 2 > maxw:
                maxw = p.pen.width // 2

        width += 2 * maxw
        height += 2 * maxw

        if width < 0 or height < 0:
            return

        offset = ul - Point((maxw+ 2, maxw + 2))
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        for path in self.model.paths:
            color = path.pen.color
            width = path.pen.width
            radius = width // 2 - 1
            for line in path.lines():
                start, end = line
                start = start - offset
                end = end - offset

                if width > 2:
                    circle = Circle(start, radius)
                    cul = circle.upper_left()
                    clr = circle.lower_right()
                    draw.ellipse((cul.x, cul.y, clr.x, clr.y), fill=color)
                    circle = Circle(end, radius)
                    cul = circle.upper_left()
                    clr = circle.lower_right()
                    draw.ellipse((cul.x, cul.y, clr.x, clr.y), fill=color)

                draw.line([int(start.x), int(start.y),
                           int(end.x), int(end.y)], fill=color, width=width)

        img.save(pathlib.Path.cwd() / (self.model.name + '.png'))

    def set_write_mode(self):
        self.end_mode()
        self.mode = MODE_WRITE

    def set_erase_mode(self, event):
        self.end_mode()
        self.mode = MODE_ERASE

    def set_lasso_mode(self, event):
        self.end_mode()
        self.mode = MODE_LASSO

    def end_mode(self):
        if self.mode == MODE_LASSO:
            self.pad.selected_paths_uuids = []
            self.pad.draw_all()

    def choose_color(self, event):
        self.root.attributes('-topmost', False)
        color = colorchooser.askcolor(title='Choose color')
        if color != (None, None):
            self.toolbar.color_panel.selected_button.set_color(color[1])

    def trigger_action_begins(self):
        if self._model_ptr < len(self.history) - 1:
            self.history = self.history[:self._model_ptr+1]
        self.history.append(self.model.clone())
        self._model_ptr += 1

    def undo_action(self, event):
        if self._model_ptr > 0:
            self._model_ptr -= 1
            self.pad.draw_all()

    def redo_action(self, event):
        if self._model_ptr < len(self.history) - 1:
            self._model_ptr += 1
            self.pad.draw_all()


def main(name):
    SketchApp(name).run()
