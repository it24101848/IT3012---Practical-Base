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
import math
from collections import deque
import heapq


class GreedyGridAgent:

    def __init__(self):
        self.actions_pool = [
            'Up',
            'Down',
            'Left',
            'Right'
        ]

    def sense_and_act(self, percept):

        if percept.get('smells_food', False):
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

    def __init__(self):
        self.plan = []
        self.active_algo = 'BFS'

    @staticmethod
    def _neighbors(position, walls, grid_size):
        moves = {
            'Up': (0, 1),
            'Down': (0, -1),
            'Left': (-1, 0),
            'Right': (1, 0)
        }

        for action, (dx, dy) in moves.items():
            new_position = (position[0] + dx, position[1] + dy)
            if (
                0 <= new_position[0] < grid_size[0]
                and 0 <= new_position[1] < grid_size[1]
                and new_position not in walls
            ):
                yield new_position, action


    def bfs_search(self, start, goal, walls, grid_size):
        frontier = deque([(start, [])])
        reached = {start}

        while frontier:
            position, path = frontier.popleft()
            if position == goal:
                return path

            for new_position, action in self._neighbors(position, set(walls), grid_size):
                if new_position not in reached:
                    reached.add(new_position)
                    frontier.append((new_position, path + [action]))

        return None

    def dfs_search(self, start, goal, walls, grid_size):
        frontier = [(start, [])]
        reached = {start}

        while frontier:
            position, path = frontier.pop()
            if position == goal:
                return path

            neighbors = list(self._neighbors(position, set(walls), grid_size))
            for new_position, action in reversed(neighbors):
                if new_position not in reached:
                    reached.add(new_position)
                    frontier.append((new_position, path + [action]))

        return None

    def ucs_search(self, start, goal, walls, grid_size):
        frontier = [(0, 0, start, [])]
        reached = {start: 0}
        sequence = 1

        while frontier:
            cost, _, position, path = heapq.heappop(frontier)
            if position == goal:
                return path
            if cost > reached[position]:
                continue

            for new_position, action in self._neighbors(position, set(walls), grid_size):
                new_cost = cost + 1
                if new_cost < reached.get(new_position, float('inf')):
                    reached[new_position] = new_cost
                    heapq.heappush(frontier, (new_cost, sequence, new_position, path + [action]))
                    sequence += 1

        return None

    def manhattan_distance(self, pos, goal):
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def euclidean_distance(self, pos, goal):
        return math.sqrt(
            (pos[0] - goal[0]) ** 2 +
            (pos[1] - goal[1]) ** 2
        )

    def astar_search(
            self,
            start_pos,
            goal_pos,
            walls,
            grid_size,
            heuristic_type='manhattan'
    ):
        heuristics = {
            'manhattan': self.manhattan_distance,
            'euclidean': self.euclidean_distance
        }
        heuristic = heuristics.get(heuristic_type, self.manhattan_distance)
        frontier = [
            (heuristic(start_pos, goal_pos), 0, start_pos, [])
        ]
        reached_states = {start_pos}
        wall_positions = set(walls)

        while frontier:
            f_cost, g_cost, current_pos, path_taken = heapq.heappop(frontier)
            if current_pos == goal_pos:
                return path_taken

            for new_pos, action in self._neighbors(current_pos, wall_positions, grid_size):
                if new_pos not in reached_states:
                    reached_states.add(new_pos)
                    new_g_cost = g_cost + 1
                    new_f_cost = new_g_cost + heuristic(new_pos, goal_pos)
                    heapq.heappush(
                        frontier,
                        (new_f_cost, new_g_cost, new_pos, path_taken + [action])
                    )

        return None

    def sense_and_act(self, percept):
        if not self.plan:
            food_positions = percept.get('all_food', [])
            if food_positions:
                start = tuple(percept['agent_pos'])
                goal = min(
                    food_positions,
                    key=lambda food: abs(food[0] - start[0]) + abs(food[1] - start[1])
                )
                search_methods = {
                    'BFS': self.bfs_search,
                    'DFS': self.dfs_search,
                    'UCS': self.ucs_search,
                    'AStar': self.astar_search
                }
                search = search_methods.get(self.active_algo, self.bfs_search)
                self.plan = search(start, goal, percept['walls'], percept['grid_size']) or []

        return self.plan.pop(0) if self.plan else 'Up'