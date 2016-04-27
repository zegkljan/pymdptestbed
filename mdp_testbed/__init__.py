import sys

from mdp_testbed.internal import Action, Maze, State
from mdp_testbed.utils import prod


class MDPModel(object):
    def __init__(self, maze: Maze):
        self._p_correct = 0.8

        self._maze = maze

        width = maze.get_width()
        height = maze.get_height()

        self._all_states = []
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

    def get_transition_probability(self,
                                   current_state: State,
                                   action: Action,
                                   future_state: State) -> float:
        fromS = current_state
        toS = future_state

        # dummy state
        if fromS == self._dummy_state and toS != self._dummy_state:
            return 0

        if fromS == self._dummy_state and toS == self._dummy_state:
            return 1

        # absorbing state
        if fromS._is_absorbing():
            if future_state != self._dummy_state:
                return 0

            if toS == self._dummy_state:
                return 1

        # teleport state
        if fromS._is_teleport():
            if toS != self._dummy_state:
                return 1.0 / self._normal_states
            return 0

        # non-teleport, non-absorbing, non-dummy
        if toS == self._dummy_state:
            return 0

        fx, fy = fromS._get_coords()

        tx, ty = toS._get_coords()

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

    def get_reward(self, state: State):
        return state._get_reward()


class Environment(object):
    """
    Environment class provides interaction with MDP model.

    It is possible to set probability of correct transition which is set to
    0.8 by default. Students will use this class to obtain all states of MDP
    and they can get reward for each state and transition probability between
    any two states using some action. This object is given to students.
    """
    def __init__(self, maze: Maze):
        self._transition_model = MDPModel(maze)

    def set_probability_of_correct_transition(self, p: float):
        """
        :param p: probability of correct transition between two neighbouring
            states if there are no walls around a state
        """
        self._transition_model.set_p_correct(p)

    def get_reward(self, state: State) -> float:
        """
        :return: reward for the given state in terms of MDP
        """
        return self._transition_model.get_reward(state)

    def get_all_states(self) -> list:
        """
        :return: a list of all states in MDP
        """
        return self._transition_model.get_all_states()

    def get_transition_probability(self,
                                   from_state: State,
                                   action: Action,
                                   to_state: State):
        return self._transition_model.get_transition_probability(from_state,
                                                                 action,
                                                                 to_state)
