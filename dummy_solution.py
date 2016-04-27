import mdp_testbed
import mdp_testbed.internal


# noinspection PyAttributeOutsideInit
class Solver(object):
    def solve_mdp(self, environment: mdp_testbed.Environment):
        self.environment = environment

    def get_action_for_state(self, state: mdp_testbed.State):
        return mdp_testbed.internal.Action.N

    def get_value_for_state(self, state: mdp_testbed.State):
        return self.environment.get_reward(state)
