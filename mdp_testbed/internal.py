import numpy as np
import enum
import zipfile
import io

# noinspection PyBroadException
try:
    import zlib
    compression = zipfile.ZIP_DEFLATED
except:
    compression = zipfile.ZIP_STORED


class Action(enum.Enum):
    go_west = 1
    west = 1
    W = 1

    go_east = 2
    east = 2
    E = 2

    go_north = 3
    north = 3
    N = 3

    go_south = 4
    south = 4
    S = 4


class Maze(object):
    _FLOAT_FMT = '%+.4f'
    _BOOL_FMT = '%u'

    def __init__(self,
                 w: int,
                 h: int,
                 default_reward: float):
        self.maze_rewards = np.empty((h, w), dtype='d')
        self.absorbing_goal_states = np.empty((h, w), dtype='?')
        self.teleport_states = np.empty((h, w), dtype='?')
        self.vertical_walls = np.empty((h, w + 1), dtype='?')
        self.horizontal_walls = np.empty((h + 1, w), dtype='?')

        # set default reward
        self.maze_rewards[:] = default_reward

        # reset absorbing goal states
        self.absorbing_goal_states[:] = False

        # reset teleporting states
        self.teleport_states[:] = False

        # reset walls
        self.vertical_walls[:] = False
        self.horizontal_walls[:] = False

        # init boundary walls
        self.horizontal_walls[0, :] = True
        self.horizontal_walls[-1, :] = True
        self.vertical_walls[:, 0] = True
        self.vertical_walls[:, -1] = True

    def get_width(self):
        return self.maze_rewards.shape[1]

    def get_height(self):
        return self.maze_rewards.shape[0]

    def set_vertical_wall(self, x: int, y: int, wall: bool):
        self.vertical_walls[y, x] = wall

    def set_horizontal_wall(self, x: int, y: int, wall: bool):
        self.horizontal_walls[y, x] = wall

    def get_reward(self, x: int, y: int):
        return self.maze_rewards[y, x]

    def set_reward(self, x: int, y: int, reward: float):
        self.maze_rewards[y, x] = reward

    def set_wall(self, x: int, y: int, action: Action, wall: bool):
        if action is Action.W:
            self.set_vertical_wall(x, y, wall)
        elif action is Action.N:
            self.set_horizontal_wall(x, y, wall)
        elif action is Action.S:
            self.set_horizontal_wall(x, y + 1, wall)
        elif action is Action.E:
            self.set_vertical_wall(x + 1, y, wall)

    def is_absorbing_goal(self, x: int, y: int) -> bool:
        return self.absorbing_goal_states[y, x]

    def set_absorbing_goal(self, x: int, y: int, absorbing_goal: bool):
        self.absorbing_goal_states[y, x] = absorbing_goal

    def is_teleport_state(self, x: int, y: int) -> bool:
        return self.teleport_states[y, x]

    def set_teleport_state(self, x: int, y: int, teleport_state: bool):
        self.teleport_states[y, x] = teleport_state

    def is_border(self, x: int, y: int, action: Action):
        if x == 0 and action is Action.W:
            return True

        if x == -1 and action is Action.E:
            return True

        if y == 0 and action is Action.N:
            return True

        if y == -1 and action is Action.S:
            return True

        if x == self.get_width() - 1 and action is Action.E:
            return True

        if x == self.get_width() and action is Action.W:
            return True

        if y == self.get_height() - 1 and action is Action.S:
            return True

        if y == self.get_height() and action is Action.N:
            return True

        return False

    def is_wall(self, x: int, y: int, action: Action) -> bool:
        if action is Action.W:
            return self.vertical_walls[y, x]

        if action is Action.N:
            return self.horizontal_walls[y, x]

        if action is Action.S:
            return self.horizontal_walls[y + 1, x]

        if action is Action.E:
            return self.vertical_walls[y, x + 1]

        raise ValueError('Invalid action value')

    def save_to_file(self, filename: str):
        print('Saving maze to "{}"'.format(filename))
        with zipfile.ZipFile(filename, mode='w') as zf:
            buf = io.BytesIO()
            np.savetxt(buf, self.maze_rewards, fmt=Maze._FLOAT_FMT)
            zf.writestr('rewards.txt', buf.getvalue(),
                        compress_type=compression)

            buf = io.BytesIO()
            np.savetxt(buf, self.absorbing_goal_states, fmt=Maze._BOOL_FMT)
            zf.writestr('goals.txt', buf.getvalue(),
                        compress_type=compression)

            buf = io.BytesIO()
            np.savetxt(buf, self.teleport_states, fmt=Maze._BOOL_FMT)
            zf.writestr('teleports.txt', buf.getvalue(),
                        compress_type=compression)

            buf = io.BytesIO()
            np.savetxt(buf, self.vertical_walls, fmt=Maze._BOOL_FMT)
            zf.writestr('vertical_walls.txt', buf.getvalue(),
                        compress_type=compression)

            buf = io.BytesIO()
            np.savetxt(buf, self.horizontal_walls, fmt=Maze._BOOL_FMT)
            zf.writestr('horizontal_walls.txt', buf.getvalue(),
                        compress_type=compression)
        print('Successfully saved.')

    def load_from_file(self, filename):
        print('Loading maze from "{}"'.format(filename))
        with zipfile.ZipFile(filename, mode='r') as zf:
            with zf.open('rewards.txt', mode='r') as f:
                self.maze_rewards = np.loadtxt(f, dtype='d', ndmin=2)
            with zf.open('goals.txt', mode='r') as f:
                self.absorbing_goal_states = np.loadtxt(f, dtype='?', ndmin=2)
            with zf.open('teleports.txt', mode='r') as f:
                self.teleport_states = np.loadtxt(f, dtype='?', ndmin=2)
            with zf.open('vertical_walls.txt', mode='r') as f:
                self.vertical_walls = np.loadtxt(f, dtype='?', ndmin=2)
            with zf.open('horizontal_walls.txt', mode='r') as f:
                self.horizontal_walls = np.loadtxt(f, dtype='?', ndmin=2)
        print('Successfully loaded.')


class State(object):
    """Class for representing states.

    State can be regular - representing grid cell including position of the
    cell in the grid. Regular states are 'normal state', 'teleport state' and
    'absorbing state'.

    Next state after teleport state is randomly selected regular state
    (including this teleport state) independently on performed action.

    Next state after 'absorbing state' is irregular 'dummy state' independently
    on performed action.

    Next state after 'dummy state' is 'dummy state' independently on performed
    action.

    There is one dummy state. It is impossible to leave the dummy state.

    Each state has a reward. Dummy state has zero reward.
    """
    def __init__(self, x: int, y: int, reward: float, absorbing: bool,
                 teleport: bool):
        self._x = x
        self._y = y
        self._reward = reward
        self._absorbing = absorbing
        self._telport = teleport
        self._dummy = False

    @staticmethod
    def dummy():
        # noinspection PyTypeChecker
        s = State(None, None, None, None, None)
        s._dummy = True
        return s

    def get_x(self) -> int:
        return self._x

    def get_y(self) -> int:
        return self._y

    def is_absorbing(self) -> bool:
        return self._absorbing

    def is_teleport(self) -> bool:
        return self._telport

    def get_reward(self) -> float:
        return self._reward

    def is_dummy(self) -> bool:
        return self._dummy
