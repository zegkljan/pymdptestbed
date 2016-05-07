from mdp_testbed import SolverBase, Environment, Action
from mdp_testbed.internal import State


# noinspection PyAttributeOutsideInit,PyMethodMayBeStatic
class Solver(SolverBase):
    def solve_mdp(self, environment: Environment):
        self.environment = environment
        self.environment.set_probability_of_correct_transition(self.p_correct)

    def get_action_for_state(self, state: State) -> Action:
        return Action.N

    def get_value_for_state(self, state: State) -> float:
        return self.environment.get_reward(state)
