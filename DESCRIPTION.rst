.. sectnum::

================================
A(E)3M33UI - Semestral project 3
================================
-------------------------
Markov Decision Processes
-------------------------

Introduction
============

The goal of this task is to make a practical experience with Markov Decision
Processes (MDP) by implementing the *Value Iteration* algorithm.

Technical notes
===============

For the labyrinth environment, implement the *Value Iteration* (VI)
algorithm, for which one can set the discount factor :math:`\gamma`\ , and
the reward :math:`r_0` for any non-terminal state. The implementation
consists of a single python file which must contain a class called ``Solver``
which derives from the class ``SolverBase`` that is defined in the
``mdp_testbed`` package (i.e. the file ``mdp_testbed/__init__.py``\ ).

The class must implement these methods:

* ``solve_mdp(self, environment: Environment)``

  This method is called by the testbed platform. This method should be
  responsible for all the actual computation needed for solving the MDP.

  The ``Environment`` class is located at the ``mdp_testbed`` package (i.e.
  in the file ``mdp_testbed/__init__.py``\ ).

* ``get_action_for_state(self, state: State) -> Action``

  This method is called by the testbed platform. This method is responsible
  for returning the action that should be performed in the given ``state``\ .

  The ``State`` class and the ``Action`` enum are located in the
  ``mdp_testbed.internal`` module (i.e. in the file
  ``mdp_testbed/internal.py``\ ).

* ``get_value_for_state(self, state: State) -> float``

  This method is called by the testbed platform. This method is responsible
  for returning the expected value of the given ``state``\ .

  The ``State`` class is located in the ``mdp_testbed.internal`` module (i.e.
  in the file ``mpd_testbed/internal.py``\ ).

A working dummy solution with all the necessary structure is in the file
``dummy_solution.py``\ . This solution does no computation at all, it always
performs the ``NORTH`` action and it returns the rewards as the values.
However it can serve you as a starting point (from the programming point of
view).

Description of the classes needed for solving this task is in the Section
`Brief Description of the Testbed Framework`_\ .

Restrictions and Constraints
----------------------------

Given Python and its dynamic nature, it is impossible to prevent you from using
some methods and members that are physically available. However, there is a
common convention: methods and members starting with an underscore, e.g.
``_get_coords()``\ , are considered to be **private**\ . Therefore you are
**not allowed** to use any such method or member field of the objects that
are given to you through the three methods introduced in the previous
section, i.e. of the objects of classes ``Environment`` and ``State``\ .

Everything related to your solver needs to be contained in a single python
file. You can import whatever you need to import (libraries, other parts of
the testbed...) but your code must be self-contained in that one file.

Brief Description of the Testbed Framework
==========================================

The ``Action`` enum
-------------------

This enum is defined in the module ``mdp_testbed.internal``\ . It is an
**enum**\ , pretty similar to Java enums, meaning it is a \`\`list'' of
possible values. These values are

* ``WEST`` or ``W`` (the enum has both these aliases that can be used
  interchangeably) - represents the direction to the west, i.e. to the left
  side.
* ``EAST`` or ``E`` - represents the direction to the east, i.e. to the right
  side.
* ``NORTH`` or ``N`` - represents the direction to the north, i.e. in the
  upper direction.
* ``SOUTH`` or ``S`` - represents the direction to the south, i.e. in the
  lower direction.

This enum represents the possible actions in the labyrinth. There are no
actions for turning, you just go in the desired direction.

You can access the enum values by using the class name, dot and the desired
enum value, e.g. ``Acion.WEST``\ . You can also iterate through all the
values like this::

    for action in Action:
        print(action)

The piece of code above would produce::

    Action.WEST
    Action.EAST
    Action.NORTH
    Action.SOUTH

You can get the numerical value of an enum option by using the option's
``value`` member::

    >>> Action.EAST.value
    2

And you can get the enum option from the numerical value by calling the enum
like a constructor with the numerical value::

    >>>print(Action(2))
    Action.EAST

The ``State`` class
-------------------

This class represents a single state. There are no public methods or members
of this class, hence you are not allowed to use any of them. However, the
objects of this class can be tested for equality using the ``==`` operator
and can be used as keys in dictionaries.

The ``Environment`` class
-------------------------

This class represents the API which you can use to interact with the MDP. The
class defines these **public** methods:

* ``set_probability_of_correct_transition(self, p: float)``

  This method sets the probability that a transition from one state to the
  other will be the one desired by an action.

  *Example*\ : the agent chooses the action ``SOUTH``\ . With probability
  :math:`p` she will end up in the cell \`\`below'' the the one she is now and
  with probability :math:`1 - p` whe will not.

* ``get_reward(self, state: State) -> float``

  This method returns the reward for reaching the given ``state``\ .

* ``get_all_states(self) -> list``

  This method returns **all** states that exist in the MDP.

* ``get_transision_probability(self, from_state: State, action: Action, to_state: State) -> float``

  This method returns the probability of a transition from state
  ``from_state`` to state ``to_state`` given an action ``action`` was performed.
