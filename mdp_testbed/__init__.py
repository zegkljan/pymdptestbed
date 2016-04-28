from mdp_testbed.internal import Maze, State, Action, MDPModel
from mdp_testbed.utils import prod


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


# noinspection PyAttributeOutsideInit
class SolverBase(object):
    def solve_mdp(self, environment: Environment):
        self.environment = environment
        raise NotImplementedError()

    def get_action_for_state(self, state: State) -> Action:
        raise NotImplementedError()

    def get_value_for_state(self, state: State) -> float:
        raise NotImplementedError()
