import tkinter as tk
import tkinter.filedialog as fd
import tkinter.ttk as ttk
import enum
import itertools

from mdp_testbed.utils import prod
import mdp_testbed.internal as internal


class EditMode(enum.Enum):
    normal = 1
    walls = 2
    absorbing = 3
    teleport = 4
    reward = 5


class Container(object):
    def __init__(self, contents=None):
        self._contents = contents

    @property
    def val(self):
        return self._contents

    @val.setter
    def val(self, contents):
        self._contents = contents


# noinspection PyAttributeOutsideInit
class ResourceMazeEditor(tk.Frame):
    def __init__(self, master=None, **kw):
        cnf = {}
        super().__init__(master, cnf, **kw)

        self.maze_cont = Container()
        self.height_var = tk.IntVar(value=2)
        self.width_var = tk.IntVar(value=2)
        self.zoom_var = tk.IntVar(value=40)
        self.reward_var = tk.DoubleVar()
        self.edit_mode_var = tk.IntVar(value=EditMode.normal.value)

        self.grid(sticky=tk.N + tk.S + tk.E + tk.W)

        top = self.winfo_toplevel()
        top.columnconfigure(0, weight=1)
        top.rowconfigure(0, weight=1)
        top.wm_title('Resoruce Maze Editor')

        self.create_widgets()

    @property
    def maze(self):
        return self.maze_cont.val

    @maze.setter
    def maze(self, m):
        self.maze_cont.val = m

    def create_widgets(self):
        self.menu_panel = tk.Frame(self)
        self.menu_panel.grid(column=0, row=0, sticky=tk.N + tk.S)

        # left menu
        self.width_field = tk.Entry(self.menu_panel,
                                    textvariable=self.width_var)
        self.width_field.grid(column=0, row=0)
        self.height_field = tk.Entry(self.menu_panel,
                                     textvariable=self.height_var)
        self.height_field.grid(column=0, row=1)
        self.size_button = tk.Button(self.menu_panel, text='Width\nx\nHeight',
                                     command=self.set_size)
        self.size_button.grid(column=1, row=0, rowspan=2, sticky=tk.W + tk.E)

        self.reward_field = tk.Entry(self.menu_panel,
                                     textvariable=self.reward_var)
        self.reward_field.grid(column=0, row=2)
        self.reward_field.delete(0, tk.END)
        self.reward_field.insert(0, '50')
        self.reward_button = tk.Button(self.menu_panel, text='Reward',
                                       command=lambda: self.toggle_mode(
                                           EditMode.reward))
        self.reward_button.grid(column=1, row=2, sticky=tk.W + tk.E)

        self.nongoal_reward_button = tk.Button(self.menu_panel,
                                               text='Set non-goal rewards',
                                               command=self.set_reward_global)
        self.nongoal_reward_button.grid(column=0, row=3, columnspan=2,
                                        sticky=tk.W + tk.E)

        self.add_walls_button = tk.Button(
            self.menu_panel, text='Add walls',
            command=lambda: self.toggle_mode(EditMode.walls))
        self.add_walls_button.grid(column=0, row=4, columnspan=2,
                                   sticky=tk.W + tk.E)

        self.add_absorbing_goals_button = tk.Button(
            self.menu_panel, text='Add absorbing goals',
            command=lambda: self.toggle_mode(EditMode.absorbing))
        self.add_absorbing_goals_button.grid(column=0, row=5, columnspan=2,
                                             sticky=tk.W + tk.E)

        self.add_teleport_states = tk.Button(
            self.menu_panel, text='Add teleport states',
            command=lambda: self.toggle_mode(EditMode.teleport))
        self.add_teleport_states.grid(column=0, row=6, columnspan=2,
                                      sticky=tk.W + tk.E)

        self.reset_maze_button = tk.Button(
            self.menu_panel, text='Reset maze', command=self.reset_maze)
        self.reset_maze_button.grid(column=0, row=7, columnspan=2,
                                    sticky=tk.W + tk.E)

        self.save_maze_button = tk.Button(self.menu_panel, text='Save maze',
                                          command=self.save_maze)
        self.save_maze_button.grid(column=0, row=8, columnspan=2,
                                   sticky=tk.W + tk.E)

        self.load_maze_button = tk.Button(self.menu_panel, text='Load maze',
                                          command=self.load_maze)
        self.load_maze_button.grid(column=0, row=9, columnspan=2,
                                   sticky=tk.W + tk.E)

        ttk.Separator(self.menu_panel, orient=tk.HORIZONTAL).grid(
            column=0, row=10, columnspan=2, sticky=tk.N + tk.S + tk.W + tk.E,
            pady=3)

        self.zoom_scale = tk.Scale(self.menu_panel, orient=tk.HORIZONTAL,
                                   label='Cell size (zoom)', command=self.zoom,
                                   from_=20, to=100, variable=self.zoom_var)
        self.zoom_scale.set(50)
        self.zoom_scale.grid(column=0, row=11, columnspan=22,
                             sticky=tk.W + tk.E)

        ttk.Separator(self, orient=tk.VERTICAL).grid(
            column=1, row=0, sticky=tk.N + tk.S + tk.W + tk.E, padx=3)

        # maze view panel
        self.maze_view = MazeView(self, self.maze_cont, self.zoom_var,
                                  self.reward_var, self.edit_mode_var)
        self.maze_view.grid(column=2, row=0, sticky=tk.N + tk.S + tk.W + tk.E)
        self.maze_view.repaint()

        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

    def set_size(self, *args):
        w = int(self.width_var.get())
        h = int(self.height_var.get())
        self.maze = internal.Maze(w, h, 0)
        self.maze_view.repaint()

    # noinspection PyUnboundLocalVariable
    def toggle_mode(self, mode, *args):
        self.reward_button.config(relief='raised')
        self.add_walls_button.config(relief='raised')
        self.add_absorbing_goals_button.config(relief='raised')
        self.add_teleport_states.config(relief='raised')

        if mode is EditMode.walls:
            button = self.add_walls_button
        elif mode is EditMode.absorbing:
            button = self.add_absorbing_goals_button
        elif mode is EditMode.teleport:
            button = self.add_teleport_states
        elif mode is EditMode.reward:
            button = self.reward_button

        curr_mode = EditMode(self.edit_mode_var.get())
        if mode is curr_mode:
            button.config(relief='raised')
            self.edit_mode_var.set(EditMode.normal.value)
        else:
            button.config(relief='sunken')
            self.edit_mode_var.set(mode.value)
        print('Edit mode: {}'.format(EditMode(self.edit_mode_var.get())))

    def set_reward_global(self, *args):
        val = float(self.reward_field.get())
        for x, y in prod(self.maze.get_width(), self.maze.get_height()):
            if not (self.maze.is_absorbing_goal(x, y) or
                    self.maze.is_teleport_state(x, y)):
                self.maze.set_reward(x, y, val)
        self.maze_view.repaint()

    def zoom(self, *args):
        self.maze_view.repaint()

    def reset_maze(self, * args):
        self.maze.__init__(self.maze.get_width(), self.maze.get_height(), 0.0)
        self.maze_view.repaint()

    def save_maze(self, *args):
        fn = fd.asksaveasfilename(defaultextension='.zip',
                                  filetypes=[('ZIP', '*.zip')],
                                  initialdir='./mazes')
        self.maze.save_to_file(fn)

    def load_maze(self, *args):
        fn = fd.askopenfilename(defaultextension='.zip',
                                filetypes=[('ZIP', '*.zip')],
                                initialdir='./mazes')
        self.maze = internal.Maze.load_from_file(fn)
        self.width_field.delete(0)
        self.height_field.delete(0)
        self.width_field.insert(0, str(self.maze.get_width()))
        self.height_field.insert(0, str(self.maze.get_height()))
        self.maze_view.repaint()


class SolutionViewer(tk.Frame):
    def __init__(self, master=None, **kw):
        cnf = {}
        super().__init__(master, cnf, **kw)

        self.maze_cont = Container()
        self.zoom_var = tk.IntVar(value=40)
        self.draw_actions_var = tk.BooleanVar(value=True)
        self.draw_values_var = tk.BooleanVar(value=True)
        self.draw_goals_var = tk.BooleanVar(value=False)
        self.draw_rewards_var = tk.BooleanVar(value=False)
        self.draw_teleports_var = tk.BooleanVar(value=False)
        self.draw_walls_var = tk.BooleanVar(value=True)

        self.grid(sticky=tk.N + tk.S + tk.E + tk.W)

        top = self.winfo_toplevel()
        top.columnconfigure(0, weight=1)
        top.rowconfigure(0, weight=1)
        top.wm_title('MDP Solution Viewer')

        self.create_widgets()

    @property
    def maze(self):
        return self.maze_cont.val

    @maze.setter
    def maze(self, m):
        self.maze_cont.val = m

    # noinspection PyAttributeOutsideInit
    def create_widgets(self):
        self.menu_panel = tk.Frame(self)
        self.menu_panel.grid(column=0, row=0, sticky=tk.N + tk.S)

        # left menu
        self.draw_actions_cb = tk.Checkbutton(self.menu_panel,
                                              text='draw actions',
                                              variable=self.draw_actions_var)
        self.draw_actions_cb.grid(column=0, row=0, sticky=tk.W)

        self.draw_values_cb = tk.Checkbutton(self.menu_panel,
                                             text='draw values',
                                             variable=self.draw_values_var)
        self.draw_values_cb.grid(column=0, row=1, sticky=tk.W)

        self.draw_goals_cb = tk.Checkbutton(self.menu_panel,
                                            text='draw goals',
                                            variable=self.draw_goals_var)
        self.draw_goals_cb.grid(column=0, row=2, sticky=tk.W)

        self.draw_rewards_cb = tk.Checkbutton(self.menu_panel,
                                              text='draw rewards',
                                              variable=self.draw_rewards_var)
        self.draw_rewards_cb.grid(column=0, row=3, sticky=tk.W)

        self.draw_teleports_cb = tk.Checkbutton(
            self.menu_panel, text='draw teleports',
            variable=self.draw_teleports_var)
        self.draw_teleports_cb.grid(column=0, row=4, sticky=tk.W)

        self.draw_walls_cb = tk.Checkbutton(self.menu_panel,
                                            text='draw walls',
                                            variable=self.draw_walls_var)
        self.draw_walls_cb.grid(column=0, row=5, sticky=tk.W)

        ttk.Separator(self.menu_panel, orient=tk.HORIZONTAL).grid(
            column=0, row=6, sticky=tk.N + tk.S + tk.W + tk.E, pady=3)
        self.load_maze_button = tk.Button(self.menu_panel, text='Load maze',
                                          command=self.load_maze)
        self.load_maze_button.grid(column=0, row=7, sticky=tk.W + tk.E)

        self.zoom_scale = tk.Scale(self.menu_panel, orient=tk.HORIZONTAL,
                                   label='Cell size (zoom)', command=self.zoom,
                                   from_=20, to=100, variable=self.zoom_var)
        self.zoom_scale.set(50)
        self.zoom_scale.grid(column=0, row=8, sticky=tk.W + tk.E)

        # maze view panel
        self.maze_view = SolutionView(self, self.maze_cont, self.zoom_var,
                                      self.draw_actions_var,
                                      self.draw_values_var,
                                      self.draw_goals_var,
                                      self.draw_rewards_var,
                                      self.draw_teleports_var,
                                      self.draw_walls_var)
        self.maze_view.grid(column=2, row=0, sticky=tk.N + tk.S + tk.W + tk.E)
        self.maze_view.repaint()

        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

    def zoom(self, *args):
        self.maze_view.repaint()

    def load_maze(self, *args):
        fn = fd.askopenfilename(defaultextension='.zip',
                                filetypes=[('ZIP', '*.zip')],
                                initialdir='./mazes')
        self.maze = internal.Maze.load_from_file(fn)
        self.maze_view.repaint()


class MazeView(tk.Frame):
    def __init__(self, master, maze_cont, zoom_var, reward_var, edit_mode_var, **kw):
        cnf = {}
        super().__init__(master, cnf, **kw)

        self.maze_cont = maze_cont
        self.zoom_var = zoom_var
        self.reward_var = reward_var
        self.edit_mode_var = edit_mode_var
        self.node_length = 70
        self.wall_width = 7
        self.offset = (5, 5)
        self.normal_color = '#ffffff'
        self.goal_color = '#fc8b25'
        self.teleport_color = '#648b25'
        self.label_ids = set()
        self.maze_grid_lines_ids = set()
        self.maze_wall_lines_ids = set()
        self.cell_ids = dict()

        self.canvas = tk.Canvas(self)
        self.canvas.bind('<Button-1>', func=self.handle_click)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

    @property
    def maze(self):
        return self.maze_cont.val

    @maze.setter
    def maze(self, m):
        self.maze_cont.val = m

    def handle_click(self, evt: tk.Event):
        if self.maze is None:
            return
        mx = evt.x
        my = evt.y
        print('Mouse clicked at: {} {}'.format(mx, my))
        edit_mode = EditMode(self.edit_mode_var.get())
        if edit_mode is EditMode.walls:
            ids = self.canvas.find_overlapping(mx - self.node_length / 10,
                                               my - self.node_length / 10,
                                               mx + self.node_length / 10,
                                               my + self.node_length / 10)
            xys = [self.cell_ids[id_] for id_ in ids if id_ in self.cell_ids]
            print('Cells: {}'.format(xys))
            if len(xys) != 2:
                return
            xys.sort()
            x1, y1 = xys[0]
            x2, y2 = xys[1]
            print(x1, y1, x2, y2)
            if x1 + 1 == x2:
                assert y1 == y2
                self.maze.set_vertical_wall(
                    x2, y1, not self.maze.is_wall(x1, y1, internal.Action.E))
            elif y1 + 1 == y2:
                assert x1 == x2
                self.maze.set_horizontal_wall(
                    x1, y2, not self.maze.is_wall(x1, y1, internal.Action.S))
            else:
                raise ValueError('Invalid wall')
            self.repaint()
        else:
            ids = self.canvas.find_overlapping(mx, my, mx, my)
            xys = [self.cell_ids[id_] for id_ in ids if id_ in self.cell_ids]
            print('Cells: {}'.format(xys))
            if len(xys) != 1:
                return
            x, y = xys[0]
            if edit_mode is EditMode.absorbing:
                self.maze.set_absorbing_goal(
                    x, y, not self.maze.is_absorbing_goal(x, y))
                self.repaint()
            elif edit_mode is EditMode.teleport:
                self.maze.set_teleport_state(
                    x, y, not self.maze.is_teleport_state(x, y))
                self.repaint()
            elif edit_mode is EditMode.reward:
                val = float(self.reward_var.get())
                self.maze.set_reward(x, y, val)
                self.repaint()

    def repaint(self):
        self.canvas.delete(tk.ALL)
        if self.maze is None:
            return
        self.node_length = self.zoom_var.get()
        self._draw_values()
        self._draw_maze()
        self._draw_goals()
        self._draw_teleports()
        self._draw_walls()
        self._draw_rewards()
        self._draw_actions()

        self.canvas.move(tk.ALL, *self.offset)

    def _draw_text(self, x: int, y: int, c, text: str):
        id_ = self.canvas.create_text(
            x * self.node_length + self.wall_width / 2 + 2,
            (y + 1) * self.node_length - self.wall_width / 2 - 2,
            text=text,
            fill=c,
            anchor=tk.SW
        )
        self.label_ids.add(id_)

    def _draw_rewards(self):
        for x, y in prod(self.maze.get_width(), self.maze.get_height()):
            self._draw_text(x, y, 'black', str(self.maze.get_reward(x, y)))

    def _draw_maze(self):
        self.cell_ids.clear()
        for ix, iy in prod(self.maze.get_width(), self.maze.get_height()):
            id_ = self._draw_cell(ix, iy, self.normal_color)
            self.cell_ids[id_] = (ix, iy)

    def _draw_goals(self):
        for ix, iy in prod(self.maze.get_width(), self.maze.get_height()):
            if self.maze.is_absorbing_goal(ix, iy):
                self._draw_cell(ix, iy, self.goal_color)

    def _draw_teleports(self):
        for ix, iy in prod(self.maze.get_width(), self.maze.get_height()):
            if self.maze.is_teleport_state(ix, iy):
                self._draw_cell(ix, iy, self.teleport_color)

    def _draw_cell(self, ix, iy, f):
        if f is None:
            f = self.normal_color
        x = ix * self.node_length
        y = iy * self.node_length
        id_ = self.canvas.create_rectangle(x, y,
                                           x + self.node_length,
                                           y + self.node_length,
                                           width=1, fill=f)
        return id_

    def _draw_walls(self):
        h = self.maze.get_height()
        w = self.maze.get_width()

        walls = set()
        for x, y in prod(w, h):
            for action in internal.Action:
                if self.maze.is_wall(x, y, action):
                    walls.add((x, y, action))

        for x, y, action in walls:
            ax = x
            bx = x
            ay = y
            by = y
            if action is internal.Action.N:
                bx += 1
            elif action is internal.Action.S:
                bx += 1
                ay += 1
                by += 1
            elif action is internal.Action.W:
                ay += 1
            elif action is internal.Action.E:
                ax += 1
                bx += 1
                by += 1
            else:
                raise ValueError('Invalid action')
            id_ = self.canvas.create_line(ax * self.node_length,
                                          ay * self.node_length,
                                          bx * self.node_length,
                                          by * self.node_length,
                                          width=self.wall_width)
            self.maze_wall_lines_ids.add(id_)

    def _draw_values(self):
        pass

    def _draw_actions(self):
        pass


class SolutionView(MazeView):
    def __init__(self, master, maze_cont, zoom_var, draw_actions_var,
                 draw_values_var, draw_goals_var, draw_rewards_var,
                 draw_teleports_var, draw_walls_var, **kw):
        super().__init__(master, maze_cont, zoom_var, tk.IntVar(),
                         tk.IntVar(value=EditMode.normal.value), **kw)

        self.draw_actions_var = draw_actions_var
        self.draw_actions_var.trace('w',
                                    lambda *a: self.repaint())
        self.draw_values_var = draw_values_var
        self.draw_values_var.trace('w',
                                   lambda *a: self.repaint())
        self.draw_goals_var = draw_goals_var
        self.draw_goals_var.trace('w',
                                  lambda *a: self.repaint())
        self.draw_rewards_var = draw_rewards_var
        self.draw_rewards_var.trace('w',
                                    lambda *a: self.repaint())
        self.draw_teleports_var = draw_teleports_var
        self.draw_teleports_var.trace('w',
                                      lambda *a: self.repaint())
        self.draw_walls_var = draw_walls_var
        self.draw_walls_var.trace('w',
                                  lambda *a: self.repaint())

    def _draw_actions(self):
        if self.draw_actions_var.get():
            super()._draw_actions()

    def _draw_rewards(self):
        if self.draw_rewards_var.get():
            super()._draw_rewards()

    def _draw_values(self):
        if self.draw_values_var.get():
            super()._draw_values()

    def _draw_walls(self):
        if self.draw_walls_var.get():
            return super()._draw_walls()

    def _draw_teleports(self):
        if self.draw_teleports_var.get():
            super()._draw_teleports()

    def _draw_goals(self):
        if self.draw_goals_var.get():
            return super()._draw_goals()
