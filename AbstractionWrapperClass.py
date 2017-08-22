# Python imports.
from collections import defaultdict
import copy

# Other imports.
from simple_rl.agents import Agent, RMaxAgent
from state_abs.StateAbstractionClass import StateAbstraction
from action_abs.ActionAbstractionClass import ActionAbstraction

class AbstractionWrapper(Agent):

    def __init__(self,
                    SubAgentClass,
                    actions,
                    state_abstr=None,
                    action_abstr=None,
                    learn=False,
                    name_ext="abstr"):
        '''
        Args:
            SubAgentClass (Class)
            actions (list of str)
            state_abstr (StateAbstraction)
            state_abstr (ActionAbstraction)
            learn (bool)
        '''
        # Setup the abstracted agent.
        self._create_default_abstractions(actions, state_abstr, action_abstr)
        self.agent = SubAgentClass(actions=self.action_abstr.get_actions())
        Agent.__init__(self, name=self.agent.name + "-" + name_ext, actions=self.action_abstr.get_actions())

    def _create_default_abstractions(self, actions, state_abstr, action_abstr):
        '''
        Summary:
            We here create the default abstractions.
        '''
        if action_abstr is None:
            self.action_abstr = ActionAbstraction(options=agent.actions, prim_actions=agent.actions)
        else:
            self.action_abstr = action_abstr

        self.state_abstr = StateAbstraction() if state_abstr is None else state_abstr

    def act(self, ground_state, reward):
        '''
        Args:
            ground_state (State)
            reward (float)

        Return:
            (str)
        '''
        abstr_state = self.state_abstr.phi(ground_state)
        
        ground_action = self.action_abstr.act(self.agent, abstr_state, ground_state, reward)

        return ground_action

    def reset(self):
        self.agent.reset()
        self.action_abstr.reset()

    def new_task(self):
        self._reset_reward()

    def get_num_known_sa(self):
        return self.agent.get_num_known_sa()

    def _reset_reward(self):
        if isinstance(self.agent, RMaxAgent):
            self.agent._reset_reward()

    def end_of_episode(self):
        self.agent.end_of_episode()
        self.action_abstr.end_of_episode()

    def make_abstract_mdp(self, mdp):
        '''
        Args:
            mdp (MDP)

        Returns:
            mdp (MDP): The abstracted MDP induced by self.state_abstr and self.action_abstr.

        Notes:
            Assumes that gamma is 1.0 and the mdp has a finite horizon.
        '''

        prim_actions = mdp.get_actions()
        ground_t, ground_r = mdp.get_transition_func(), mdp.get_reward_func()

        abstr_actions = self.action_abstr.get_actions()
        abstr_init_state = self.state_abstr.phi(mdp.get_init_state())

        def _abstr_reward_func(ground_state, abstr_action):
            # Option still running
            reward_total = 0.0
            while self.action_abstr.is_next_step_continuing_option(ground_state):
                # Terminal check.
                abstr_state = self.state_abstr.phi(ground_state)
                ground_action = self.action_abstr.act(self.agent, abstr_state, ground_state, reward=0)
                reward_total += ground_r(ground_state, ground_action)
                ground_state = ground_t(ground_state, ground_action)

            return reward_total

        def _abstr_trans_func(ground_state, abstr_action):
            # Option still running
            num_steps = 0
            while self.action_abstr.is_next_step_continuing_option(ground_state):
                # Terminal check and figure out step thing.
                abstr_state = self.state_abstr.phi(ground_state)
                ground_action = self.action_abstr.act(self.agent, abstr_state, ground_state, reward=0)
                reward_total += ground_r(ground_state, ground_action)
                ground_state = ground_t(ground_state, ground_action)
                num_steps += 1

            
            return ground_state
                
        abstr_mdp = MDP(actions=abstr_actions,
                        transition_func=abstr_trans_func,
                        reward_func=abstr_reward_func,
                        init_state=abstr_init_state,
                        gamma=1.0)

        return abstr_mdp
