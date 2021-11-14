import gamelib
import random
import math
import warnings
from sys import maxsize
import json

from gamelib.game_state import GameState
from gamelib.navigation import ShortestPathFinder


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write("Random seed: {}".format(seed))

        self.turn = 0
        self.scored_turns = [0]

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write("Configuring your custom algo strategy...")
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write(
            "Performing turn {} of your custom algo strategy".format(
                game_state.turn_number
            )
        )
        # Comment or remove this line to enable warnings.
        game_state.suppress_warnings(True)

        self.hello_world(game_state)

        game_state.submit_turn()

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        self.turn = state["turnInfo"][1]
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self and self.scored_turns[0] != self.turn:
                gamelib.debug_write("Scored in turn {turn}")
                self.scored_turns = [self.turn] + self.scored_turns

    def hello_world(self, game_state: GameState):
        turret_pos = [(3, 12), (24, 12), (9, 10), (18, 10), (13, 7)]
        wall_pos_1 = [
            [0, 13],
            [1, 13],
            [2, 13],
            [3, 13],
            [4, 13],
            [5, 13],
            [22, 13],
            [23, 13],
            [24, 13],
            [25, 13],
            [26, 13],
            [27, 13],
        ]

        wall_pos_2 = [
            [8, 11],
            [9, 11],
            [10, 11],
            [11, 11],
            [12, 11],
            [15, 11],
            [16, 11],
            [17, 11],
            [18, 11],
            [19, 11],
        ]

        # Redeploy stage
        for pos in turret_pos:
            if game_state.can_spawn(TURRET, pos):
                gamelib.debug_write("deploying turret at {}".format(pos))
                game_state.attempt_spawn(TURRET, pos)
        for pos in wall_pos_1:
            if game_state.can_spawn(WALL, pos):
                game_state.attempt_spawn(WALL, pos)
        for pos in wall_pos_2:
            if game_state.can_spawn(WALL, pos):
                game_state.attempt_spawn(WALL, pos)

        # Repair stage
        for pos in turret_pos:
            game_state.attempt_upgrade(pos)
        for pos in wall_pos_1:
            game_state.attempt_upgrade(pos)
        for pos in wall_pos_2:
            game_state.attempt_upgrade(pos)

        # Attack stage
        self.attack_edge(game_state)

    def calc_left_resistance(self, game_state: GameState):
        left_edges = [
            [0, 13],
            [1, 12],
            [2, 11],
            [3, 10],
            [4, 9],
            [5, 8],
            [6, 7],
            [7, 6],
            [8, 5],
            [9, 4],
            [10, 3],
            [11, 2],
            [12, 1],
            [13, 0],
        ]
        left_destinations = [
            [14, 27],
            [15, 26],
            [16, 25],
            [17, 24],
            [18, 23],
            [19, 22],
            [20, 21],
            [21, 20],
            [22, 19],
            [23, 18],
            [24, 17],
            [25, 16],
            [26, 15],
            [27, 14],
        ]

        edge_resistance = {}
        pathfinder = ShortestPathFinder()
        for pos in left_edges:
            # Typecast to tuple to become tuple
            pos = tuple(pos)
            path_edges = pathfinder.navigate_multiple_endpoints(
                pos, left_destinations, game_state
            )
            if path_edges is None:
                continue
            for path in path_edges:
                # Still on my territory
                if path[1] < 11:
                    continue
                # Add number of attackers
                edge_resistance[pos] = edge_resistance.get(pos, 0) + len(
                    game_state.get_attackers(path, 0)
                )
        return edge_resistance

    def calc_left_damages(self, game_state: GameState):
        left_edges = [
            [0, 13],
            [1, 12],
            [2, 11],
            [3, 10],
            [4, 9],
            [5, 8],
            [6, 7],
            [7, 6],
            [8, 5],
            [9, 4],
            [10, 3],
            [11, 2],
            [12, 1],
            [13, 0],
        ]
        left_destinations = [
            [14, 27],
            [15, 26],
            [16, 25],
            [17, 24],
            [18, 23],
            [19, 22],
            [20, 21],
            [21, 20],
            [22, 19],
            [23, 18],
            [24, 17],
            [25, 16],
            [26, 15],
            [27, 14],
        ]

        edge_damages = {}
        pathfinder = ShortestPathFinder()
        for pos in left_edges:
            # Typecast to tuple to become tuple
            pos = tuple(pos)
            path_edges = pathfinder.navigate_multiple_endpoints(
                pos, left_destinations, game_state
            )

            attackable_targets = set()
            attackable_turns = 0

            if path_edges is None:
                continue
            for path_coord in path_edges:
                # Still on my territory
                if path_coord[1] < 10:
                    continue
                # Add number of stationary structures it will encounter. Break if we encounter a turret as it will die

                # we want to send attackable targets/ turns to a max of 3 demolishers

                targets = self.find_nearby_targets(game_state, path_coord)
                if len(targets) > 0:
                    attackable_turns += 1
                    attackable_targets |= targets

                if len(game_state.get_attackers(path_coord, 0)) > 0:
                    break

            edge_damages[pos] = (attackable_targets, attackable_turns)

        gamelib.debug_write(f"Left damages: {edge_damages}")

        return edge_damages

    def calc_right_damages(self, game_state: GameState):
        right_edges = [
            [27, 13],
            [26, 12],
            [25, 11],
            [24, 10],
            [23, 9],
            [22, 8],
            [21, 7],
            [20, 6],
            [19, 5],
            [18, 4],
            [17, 3],
            [16, 2],
            [15, 1],
            [14, 0],
        ]
        right_destinations = [
            [13, 27],
            [12, 26],
            [11, 25],
            [10, 24],
            [9, 23],
            [8, 22],
            [7, 21],
            [6, 20],
            [5, 19],
            [4, 18],
            [3, 17],
            [2, 16],
            [1, 15],
            [0, 14],
        ]

        edge_damages = {}
        pathfinder = ShortestPathFinder()
        for pos in right_edges:
            # Typecast to tuple to become tuple
            pos = tuple(pos)
            path_edges = pathfinder.navigate_multiple_endpoints(
                pos, right_destinations, game_state
            )

            attackable_targets = set()
            attackable_turns = 0

            if path_edges is None:
                continue
            for path_coord in path_edges:
                # Still on my territory
                if path_coord[1] < 10:
                    continue
                # Add number of stationary structures it will encounter. Break if we encounter a turret as it will die
                if len(game_state.get_attackers(path_coord, 0)) > 0:
                    break

                # we want to send attackable targets/ turns to a max of 3 demolishers
                targets = self.find_nearby_targets(game_state, path_coord)
                if len(targets) > 0:
                    attackable_turns += 1
                    attackable_targets |= targets

            edge_damages[pos] = (attackable_targets, attackable_turns)

        gamelib.debug_write(f"Right damages: {edge_damages}")

        return edge_damages

    def find_nearby_targets(self, game_state: GameState, pos):

        targets = set()
        search_coords = game_state.game_map.get_locations_in_range(
            location=pos, radius=4.5
        )

        for coord in search_coords:
            if game_state.contains_stationary_unit(coord):
                for unit in game_state.game_map[coord]:
                    if unit.player_index == 1:
                        targets.add(tuple(coord))

        # gamelib.debug_write(f"Found stationary targets {targets} around {pos}\n")

        return targets

    def count_enemy_structures(self, game_state: GameState):
        total_structures = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1:
                        total_structures += 1

        return total_structures

    def calc_right_resistance(self, game_state: GameState):
        right_edges = [
            [27, 13],
            [26, 12],
            [25, 11],
            [24, 10],
            [23, 9],
            [22, 8],
            [21, 7],
            [20, 6],
            [19, 5],
            [18, 4],
            [17, 3],
            [16, 2],
            [15, 1],
            [14, 0],
        ]
        right_destinations = [
            [13, 27],
            [12, 26],
            [11, 25],
            [10, 24],
            [9, 23],
            [8, 22],
            [7, 21],
            [6, 20],
            [5, 19],
            [4, 18],
            [3, 17],
            [2, 16],
            [1, 15],
            [0, 14],
        ]

        edge_resistance = {}
        pathfinder = ShortestPathFinder()
        for pos in right_edges:
            # Typecast to tuple to become tuple
            pos = tuple(pos)
            path_edges = pathfinder.navigate_multiple_endpoints(
                pos, right_destinations, game_state
            )
            if path_edges is None:
                continue
            for path in path_edges:
                # Still on my territory
                if path[1] < 11:
                    continue
                # Add number of attackers and register edge
                edge_resistance[pos] = edge_resistance.get(pos, 0) + len(
                    game_state.get_attackers(path, 0)
                )
        return edge_resistance

    def attack_edge(self, game_state: GameState):
        if game_state.get_resource(1) < self.calculate_attack_resource_limit():
            gamelib.debug_write(
                f"Insufficient units to attack: {game_state.get_resource(1)}"
            )
            return

        # Determine resistance on left
        left_resistance = self.calc_left_resistance(game_state)
        left_damages = self.calc_left_damages(game_state)
        lowest_left_resistance = min(left_resistance.values())
        # filtered_left_resistance = [
        #     (k, v) for k, v in left_resistance.items() if v == lowest_left_resistance
        # ]
        max_left_damage = max([v[1] for k, v in left_damages.items()])
        # formatted_left_damage = sorted([
        #     (k, v) for k, v in left_damages.items() if v[1] == max_left_damage
        # ], key=lambda x: len(x[1][0]), reverse=True)

        # Determine resistance on right
        right_resistance = self.calc_right_resistance(game_state)
        right_damages = self.calc_right_damages(game_state)
        lowest_right_resistance = min(right_resistance.values())
        # filtered_right_resistance = [
        #     (k, v) for k, v in right_resistance.items() if v == lowest_right_resistance
        # ]
        max_right_damage = max([v[1] for k, v in right_damages.items()])
        # formatted_right_damage = sorted([
        #     (k, v) for k, v in right_damages.items() if v[1] == max_right_damage
        # ], key=lambda x: len(x[1][0]), reverse=True)

        lowest_resistance = min(lowest_left_resistance, lowest_right_resistance)
        filtered_low_resistance = list(
            filter(
                lambda x: x[1] == lowest_resistance,
                list(left_resistance.items()) + list(right_resistance.items()),
            )
        )

        max_damage = max(max_left_damage, max_right_damage)
        filtered_max_damage = sorted(
            list(
                filter(
                    lambda x: x[1][1] == max_damage,
                    list(left_damages.items()) + list(right_damages.items()),
                )
            ),
            key=lambda x: len(x[1][0]),
            reverse=True,
        )

        def attack():

            total_structures = self.count_enemy_structures(game_state)

            can_spawn_anything = False

            num_demolishers = 0
            num_scouts = int(game_state.get_resource(1))

            if total_structures > 20:
                for spawn, data in filtered_max_damage:
                    spawn = list(spawn)
                    if game_state.can_spawn(DEMOLISHER, spawn):
                        can_spawn_anything = True

                        num_demolishers = int(
                            max(min(3, len(data[0]) / (data[1] + 1)), 0)
                        )
                        num_scouts = int(
                            game_state.get_resource(1) - 3 * num_demolishers
                        )

                        gamelib.debug_write(
                            f"Demolisher can attack {len(data[0])} units across {data[1]} turns"
                        )

                        gamelib.debug_write(
                            f"Demolish Attacking on {spawn} with {num_demolishers} demolishers"
                        )
                        game_state.attempt_spawn(DEMOLISHER, spawn, num=num_demolishers)

            for spawn, data in filtered_low_resistance:
                spawn = list(spawn)
                if game_state.can_spawn(SCOUT, spawn):
                    can_spawn_anything = True

                    gamelib.debug_write(f"Scout Attacking on {spawn} with {num_scouts}")
                    game_state.attempt_spawn(SCOUT, spawn, num=num_scouts)

            return can_spawn_anything

        attack()

    def calculate_attack_resource_limit(self):
        turns_since_last_breach = self.turn - self.scored_turns[0]
        return 11 + min(turns_since_last_breach / 6, 9)


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
