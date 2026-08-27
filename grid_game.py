# grid_game.py
import random


class GridHuntGame:
    """A small Pacman-style grid environment (4x4) where an agent collects food."""

    def __init__(self, width=4, height=4):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]  # Starting position (x, y)
        self.agent_facing = 'Up'

        # Place a few random food pellets and obstacles (walls)
        self.food_positions = {(1, 2), (2, 3), (3, 0), (2, 1)}
        self.walls = {(1, 1), (2, 2)}

        self.score = 0
        self.steps = 0

    def get_percept(self, agent) -> dict:
        direction_offsets = {
            'Up': (0, 1),
            'Down': (0, -1),
            'Left': (-1, 0),
            'Right': (1, 0)
        }
        dx, dy = direction_offsets[self.agent_facing]
        ahead_x = self.agent_pos[0] + dx
        ahead_y = self.agent_pos[1] + dy
        ahead_pos = (ahead_x, ahead_y)

        return {
            'agent_pos': tuple(self.agent_pos),
            'wall_ahead': ahead_pos in self.walls,
            'food_here': tuple(self.agent_pos) in self.food_positions,
            'score': self.score,
            'remaining_food': len(self.food_positions)
        }

    def execute_action(self, agent, action: str):
        self.steps += 1
        self.agent_facing = action
        new_pos = list(self.agent_pos)

        if action == 'Up':
            new_pos[1] = min(self.height - 1, new_pos[1] + 1)
        elif action == 'Down':
            new_pos[1] = max(0, new_pos[1] - 1)
        elif action == 'Left':
            new_pos[0] = max(0, new_pos[0] - 1)
        elif action == 'Right':
            new_pos[0] = min(self.width - 1, new_pos[0] + 1)

        # Check collision with walls
        if tuple(new_pos) in self.walls:
            self.score -= 5  # Penalty for hitting a wall
        else:
            self.agent_pos = new_pos

        # Check if eating food
        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.food_positions:
            self.food_positions.remove(tuple_pos)
            self.score += 20  # Reward for eating food pellet

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 20