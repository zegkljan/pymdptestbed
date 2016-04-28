import enum
import io
import sys
import zipfile

import numpy as np

from mdp_testbed.utils import prod

# noinspection PyBroadException
try:
    import zlib
    compression = zipfile.ZIP_DEFLATED
except:
    compression = zipfile.ZIP_STORED


class Action(enum.Enum):
    WEST = 1
    W = 1

    EAST = 2
    E = 2

    NORTH = 3
    N = 3

    SOUTH = 4
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

    @staticmethod
    def load_from_file(filename):
        print('Loading maze from "{}"'.format(filename))
        m = Maze(0, 0, 0)
        with zipfile.ZipFile(filename, mode='r') as zf:
            with zf.open('rewards.txt', mode='r') as f:
                m.maze_rewards = np.loadtxt(f, dtype='d', ndmin=2)
            with zf.open('goals.txt', mode='r') as f:
                m.absorbing_goal_states = np.loadtxt(f, dtype='?', ndmin=2)
            with zf.open('teleports.txt', mode='r') as f:
                m.teleport_states = np.loadtxt(f, dtype='?', ndmin=2)
            with zf.open('vertical_walls.txt', mode='r') as f:
                m.vertical_walls = np.loadtxt(f, dtype='?', ndmin=2)
            with zf.open('horizontal_walls.txt', mode='r') as f:
                m.horizontal_walls = np.loadtxt(f, dtype='?', ndmin=2)
        print('Successfully loaded.')
        return m


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
    def _dummy():
        # noinspection PyTypeChecker
        s = State(None, None, 0, None, None)
        s._dummy = True
        return s

    def _get_coords(self) -> tuple:
        return self._x, self._y

    def _is_absorbing(self) -> bool:
        return self._absorbing

    def _is_teleport(self) -> bool:
        return self._telport

    def _get_reward(self) -> float:
        return self._reward

    def _is_dummy(self) -> bool:
        return self._dummy

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        return super().__eq__(other)


class MDPModel(object):
    def __init__(self, maze: Maze):
        self._p_correct = 0.8

        self._maze = maze

        width = maze.get_width()
        height = maze.get_height()

        self._all_states = []
        # noinspection PyProtectedMember
        self._dummy_state = State._dummy()

        for x, y in prod(width, height):
            absorbing = maze.is_absorbing_goal(x, y)
            teleport = maze.is_teleport_state(x, y)

            if absorbing and teleport:
                raise ValueError('State cannot be teleport and absorbing '
                                 'simultaneously')

            reward = maze.get_reward(x, y)

            s = State(x, y, reward, absorbing, teleport)
            self._all_states.append(s)

        self._normal_states = len(self._all_states)
        self._all_states.append(self._dummy_state)

    def set_p_correct(self, p_correct: float):
        self._p_correct = p_correct

    def get_all_states(self):
        return self._all_states

    # noinspection PyProtectedMember
    def get_transition_probability(self,
                                   current_state: State,
                                   action: Action,
                                   future_state: State) -> float:
        from_s = current_state
        to_s = future_state

        # dummy state
        if from_s == self._dummy_state and to_s != self._dummy_state:
            return 0

        if from_s == self._dummy_state and to_s == self._dummy_state:
            return 1

        # absorbing state
        if from_s._is_absorbing():
            if future_state != self._dummy_state:
                return 0

            if to_s == self._dummy_state:
                return 1

        # teleport state
        if from_s._is_teleport():
            if to_s != self._dummy_state:
                return 1.0 / self._normal_states
            return 0

        # non-teleport, non-absorbing, non-dummy
        if to_s == self._dummy_state:
            return 0

        fx, fy = from_s._get_coords()

        tx, ty = to_s._get_coords()

        dx = fx - tx
        dy = fy - ty
        delta = abs(dx) + abs(dy)

        # are states neighbors?
        if delta > 1:
            return 0

        wall_w = self._maze.is_wall(fx, fy, Action.W)
        wall_e = self._maze.is_wall(fx, fy, Action.E)
        wall_n = self._maze.is_wall(fx, fy, Action.N)
        wall_s = self._maze.is_wall(fx, fy, Action.S)

        other_p = (1 - self._p_correct) / 2

        p_w = other_p
        p_e = other_p
        p_n = other_p
        p_s = other_p
        p_stay = 0.0

        if action is Action.W:
            p_w = self._p_correct
            p_e = 0.0
        elif action is Action.E:
            p_e = self._p_correct
            p_w = 0.0
        elif action is Action.N:
            p_n = self._p_correct
            p_s = 0.0
        elif action is Action.S:
            p_s = self._p_correct
            p_n = 0.0
        else:
            raise ValueError('Invalid action')

        if wall_w:
            p_stay += p_w
            p_w = 0
        if wall_e:
            p_stay += p_e
            p_e = 0
        if wall_n:
            p_stay += p_n
            p_n = 0
        if wall_s:
            p_stay += p_s
            p_s = 0

        if fx == tx:
            if fy > ty:
                return p_n
            elif fy < ty:
                return p_s
        elif fy == ty:
            if fx > tx:
                return p_w
            elif fx < tx:
                return p_e

        if fx == tx and fy == ty:
            return p_stay

        print('Bad direction', file=sys.stderr)
        return 0

    @staticmethod
    def get_reward(state: State):
        # noinspection PyProtectedMember
        return state._get_reward()
