import enum
import tkinter as tk
import tkinter.filedialog as fd
import tkinter.ttk as ttk

import numpy as np

import mdp_testbed
import mdp_testbed.internal as internal
from mdp_testbed.utils import prod

act_vector = {internal.Action.N: np.array([0, -1], dtype='l'),
              internal.Action.S: np.array([0, +1], dtype='l'),
              internal.Action.W: np.array([-1, 0], dtype='l'),
              internal.Action.E: np.array([+1, 0], dtype='l')}


def rgb2color(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def create_colormap(rm, gm, bm, n=256):
    x = np.linspace(0, 1, n)
    rv = np.interp(x, rm[:, 0], rm[:, 1])
    gv = np.interp(x, gm[:, 0], gm[:, 1])
    bv = np.interp(x, bm[:, 0], bm[:, 1])
    cmap = np.column_stack((rv, gv, bv))
    cmap[np.isnan(cmap)] = 0
    cmap[cmap > 1] = 1
    cmap[cmap < 0] = 0
    return cmap


def apply_colormap(cmap, x):
    rgb = cmap[x, :]
    rgb256 = np.interp(rgb, [0, 1], [0, 255])
    rgb256 = rgb256.astype('l')
    return tuple(rgb256)


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
    def __init__(self, solution, master=None, **kw):
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

        self.create_widgets(solution)

    @property
    def maze(self):
        return self.maze_cont.val

    @maze.setter
    def maze(self, m):
        self.maze_cont.val = m

    # noinspection PyAttributeOutsideInit
    def create_widgets(self, solution):
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

        self.draw_rewards_cb = tk.Checkbutton(self.menu_panel,
                                              text='draw rewards',
                                              variable=self.draw_rewards_var)
        self.draw_rewards_cb.grid(column=0, row=2, sticky=tk.W)

        self.draw_goals_cb = tk.Checkbutton(self.menu_panel,
                                            text='draw goals',
                                            variable=self.draw_goals_var)
        self.draw_goals_cb.grid(column=0, row=3, sticky=tk.W)

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
                                      self.draw_walls_var, solution)
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
        self.maze_view.environment = mdp_testbed.Environment(self.maze)
        self.maze_view.repaint()


class MazeView(tk.Frame):
    def __init__(self, master, maze_cont, zoom_var, reward_var, edit_mode_var, **kw):
        cnf = {}
        super().__init__(master, cnf, **kw)

        self.node_length = 70
        self.wall_width = 7
        self.offset = (5, 5)
        self.reward_label_color = (0, 0, 0)
        self.normal_color = (255, 255, 255)
        self.goal_color = (127, 0, 0)
        self.teleport_color = (170, 72, 156)

        self.maze_cont = maze_cont

        self.zoom_var = zoom_var
        self.reward_var = reward_var
        self.edit_mode_var = edit_mode_var

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
        self._draw_maze()
        self._draw_rewards()
        self._draw_value_labels()
        self._draw_actions()
        self._draw_walls()

        self.canvas.move(tk.ALL, *self.offset)

    def _draw_text(self, x: int, y: int, c, text: str, place):
        if place == tk.SW:
            anchor = tk.SW
            dx = 0
            dy = 1
            ex = self.wall_width / 2 + 2
            ey = -self.wall_width / 2 - 2
        elif place == tk.NE:
            anchor = tk.NE
            dx = 1
            dy = 0
            ex = -self.wall_width / 2 - 2
            ey = self.wall_width / 2 + 2
        elif place == tk.NW:
            anchor = tk.NW
            dx = 0
            dy = 0
            ex = self.wall_width / 2 + 2
            ey = self.wall_width / 2 + 2
        id_ = self.canvas.create_text(
            (x + dx) * self.node_length + ex,
            (y + dy) * self.node_length + ey,
            text=text,
            fill=c,
            anchor=anchor
        )
        self.label_ids.add(id_)

    def _draw_rewards(self):
        for x, y in prod(self.maze.get_width(), self.maze.get_height()):
            self._draw_text(x, y, rgb2color(*self.reward_label_color),
                            str(self.maze.get_reward(x, y)), tk.SW)

    def _draw_maze(self):
        self.cell_ids.clear()
        for x, y in prod(self.maze.get_width(), self.maze.get_height()):
            id_ = self._draw_cell(x, y)
            self.cell_ids[id_] = (x, y)

    def _draw_cell(self, ix, iy):
        x = ix * self.node_length
        y = iy * self.node_length
        f = self.normal_color
        if self.maze.is_absorbing_goal(ix, iy):
            f = self.goal_color
        elif self.maze.is_teleport_state(ix, iy):
            f = self.teleport_color
        id_ = self.canvas.create_rectangle(x, y,
                                           x + self.node_length,
                                           y + self.node_length,
                                           width=1,
                                           fill=rgb2color(*f))
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
                                          width=self.wall_width,
                                          capstyle=tk.ROUND)
            self.maze_wall_lines_ids.add(id_)

    def _draw_value_labels(self):
        pass

    def _draw_actions(self):
        pass


class SolutionView(MazeView):
    def __init__(self, master, maze_cont, zoom_var, draw_actions_var,
                 draw_values_var, draw_goals_var, draw_rewards_var,
                 draw_teleports_var, draw_walls_var, solution, **kw):
        super().__init__(master, maze_cont, zoom_var, tk.IntVar(),
                         tk.IntVar(value=EditMode.normal.value), **kw)

        self.reward_label_color = (0, 0, 0)
        self.value_label_color = (255, 255, 255)

        self.arrow_length_frac = 0.7
        self.arrow_start_offset = 0.5
        self.arrow_feather_length_frac = 0.7
        self.arrow_feather_angle = 25
        self.arrow_color = '#ff0000'
        self.arrow_width = 3

        self.value_cmap = create_colormap(np.array([[0.0,  80 / 255],
                                                    [1.0,  80 / 255]]),
                                          np.array([[0.0,  75 / 255],
                                                    [1.0, 230 / 255]]),
                                          np.array([[0.0,   0 / 255],
                                                    [1.0, 230 / 255]])
                                          )

        cs = np.cos(np.deg2rad(self.arrow_feather_angle))
        sn = np.sin(np.deg2rad(self.arrow_feather_angle))
        self.feather_rot_mat1 = np.array([[cs, -sn],
                                          [sn, cs]])
        self.feather_rot_mat2 = np.array([[cs, sn],
                                          [-sn, cs]])

        self._environment = None
        self._solution = solution
        self._states_values_actions = None
        self._min_v = 0
        self._max_v = 0

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

    @property
    def environment(self) -> mdp_testbed.Environment:
        return self._environment

    @environment.setter
    def environment(self, environment: mdp_testbed.Environment):
        self._environment = environment
        self._solution.solve_mdp(self._environment)
        self._states_values_actions = {
            s._get_coords(): (s,
                              self._solution.get_value_for_state(s),
                              self._solution.get_action_for_state(s))
            for s in self.environment.get_all_states()
            if not s._is_dummy()
        }
        vals = [v for s, v, _ in self._states_values_actions.values()
                if not s._is_dummy()]
        self._min_v = min(vals)
        self._max_v = max(vals)

    def _draw_actions(self):
        if not self.draw_actions_var.get():
            return
        for (x, y), (_, _, a) in self._states_values_actions.items():
            self._draw_arrow(x, y, a)

    def _draw_rewards(self):
        if self.draw_rewards_var.get():
            super()._draw_rewards()

    def _draw_value_labels(self):
        if not self.draw_values_var.get():
            return
        for (x, y), (s, v, _) in self._states_values_actions.items():
            self._draw_text(x, y, rgb2color(*self.value_label_color),
                            '{:.3f}'.format(v), tk.NW)

    def _draw_cell(self, ix, iy):
        is_teleport = self.maze.is_teleport_state(ix, iy)
        is_goal = self.maze.is_absorbing_goal(ix, iy)
        f = self.normal_color
        if self.draw_values_var.get():
            _, value, _ = self._states_values_actions[(ix, iy)]
            norm_val = int(np.interp(value,
                                     [self._min_v, self._max_v],
                                     [0, 255]))
            value_color = apply_colormap(self.value_cmap, norm_val)
            f = value_color
        if is_goal and self.draw_goals_var.get():
            f = self.goal_color
        elif is_teleport and self.draw_teleports_var.get():
            f = self.teleport_color
        x = ix * self.node_length
        y = iy * self.node_length
        id_ = self.canvas.create_rectangle(x, y,
                                           x + self.node_length,
                                           y + self.node_length,
                                           width=1, fill=rgb2color(*f))
        return id_

    def _draw_walls(self):
        if self.draw_walls_var.get():
            return super()._draw_walls()

    def _draw_arrow(self, x, y, action):
        l = self.arrow_length_frac * self.node_length / 2
        c = np.array([x, y])
        c = self.node_length * (c + .5)
        v = act_vector[action]
        start = c - v * l * self.arrow_start_offset
        end = start + v * l

        self.canvas.create_line(start[0], start[1], end[0], end[1],
                                width=self.arrow_width,
                                fill=self.arrow_color,
                                capstyle=tk.ROUND)
        f_v1 = self.feather_rot_mat1.dot(-v)
        f_v2 = self.feather_rot_mat2.dot(-v)
        f_e1 = end + f_v1 * self.arrow_feather_length_frac * l
        f_e2 = end + f_v2 * self.arrow_feather_length_frac * l
        self.canvas.create_line(f_e1[0], f_e1[1],
                                end[0], end[1],
                                f_e2[0], f_e2[1],
                                width=self.arrow_width,
                                fill=self.arrow_color,
                                capstyle=tk.ROUND,
                                joinstyle=tk.MITER)

