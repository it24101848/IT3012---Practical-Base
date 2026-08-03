# # agent.py
# class GreedyGridAgent:
#     """A simple agent that tries to move around systematically to clear the grid."""
#
#     def __init__(self):
#         self.actions_pool = ['Up', 'Down', 'Left', 'Right']
#
#     def sense_and_act(self, percept: dict) -> str:
#         # If standing directly on food, or just wander / move towards coordinates
#         pos = percept['agent_pos']
#         # Simple heuristic or fallback random sweep
#         return random.choice(self.actions_pool)
import random
from collections import deque


class GreedyGridAgent:

    def __init__(self):
        self.actions_pool = [
            'Up',
            'Down',
            'Left',
            'Right'
        ]

    def sense_and_act(self, percept):

        if percept['smells_food']:
            return random.choice(self.actions_pool)

        return random.choice(self.actions_pool)



# ---------------------------------
# Practical 1
# Simple Reflex Agent
# ---------------------------------

class SimpleReflexAgent:

    def __init__(self):
        self.actions = [
            'Up',
            'Down',
            'Left',
            'Right'
        ]

    def sense_and_act(self, percept):
        if percept.get('food_here'):
            return 'Up'

        if percept.get('wall_ahead'):
            return 'Left'

        return 'Up'



# ---------------------------------
# Practical 2
# Model Based Agent
# ---------------------------------

class ModelBasedAgent:

    def __init__(self):
        self.memory = {}
        self.last_action = None
        self.last_percept = None
        self.action_order = ['Up', 'Left', 'Right', 'Down']

    def _alternate_action(self):
        if self.last_action is None:
            return 'Left'

        choices = [action for action in self.action_order if action != self.last_action]
        return choices[0]

    def sense_and_act(self, percept):
        percept_key = tuple(sorted(percept.items()))
        seen_before = percept_key in self.memory

        if percept.get('food_here'):
            action = 'Up'
        elif percept.get('wall_ahead'):
            if seen_before:
                action = self._alternate_action()
            else:
                action = 'Left'
        else:
            if seen_before:
                action = self._alternate_action()
            else:
                action = 'Up'

        self.memory[percept_key] = self.memory.get(percept_key, 0) + 1
        self.last_percept = percept
        self.last_action = action

        return action



# ---------------------------------
# Practical 3
# Search Agent BFS
# ---------------------------------

class SearchAgent:


    def bfs_search(
            self,
            start,
            goal,
            walls,
            grid_size
    ):

        queue = deque()

        queue.append(
            (start, [])
        )

        visited=set()

        visited.add(start)


        moves = {

            "Up":(0,1),
            "Down":(0,-1),
            "Left":(-1,0),
            "Right":(1,0)

        }


        while queue:


            position,path = queue.popleft()


            if position == goal:

                return path



            for action,move in moves.items():

                new_x = position[0]+move[0]
                new_y = position[1]+move[1]


                new_position = (
                    new_x,
                    new_y
                )


                if (
                    0 <= new_x < grid_size[0]
                    and
                    0 <= new_y < grid_size[1]
                    and
                    new_position not in walls
                    and
                    new_position not in visited
                ):

                    visited.add(new_position)

                    queue.append(
                        (
                            new_position,
                            path+[action]
                        )
                    )


        return None