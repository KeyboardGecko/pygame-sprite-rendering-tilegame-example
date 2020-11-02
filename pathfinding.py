from warnings import warn
import heapq

class Node:
    """
    A node class for A* Pathfinding
    """

    def __init__(self, parent=None, tile=None):
        self.parent = parent
        self.tile = tile

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, target):
        return self.tile == target.tile

    def __repr__(self):
      return f"{self.tile} - g: {self.g} h: {self.h} f: {self.f}"

    # defining less than for purposes of heap queue
    def __lt__(self, target):
      return self.f < target.f

    # defining greater than for purposes of heap queue
    def __gt__(self, target):
      return self.f > target.f

def return_path(current_node):
    path = []
    current = current_node
    while current is not None:
        path.append(current.tile)
        current = current.parent
    return path[::-1]  # Return reversed path


def astar(map, start, end):
    # Create start and end node
    start_node = Node(None, start)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, end)
    end_node.g = end_node.h = end_node.f = 0

    # Initialize both open and closed list
    open_list = []
    closed_list = []

    # Heapify the open_list and Add the start node
    heapq.heapify(open_list)
    heapq.heappush(open_list, start_node)

    # Adding a stop condition
    outer_iterations = 0
    max_iterations = 70

    # what squares do we search
    adjacent_squares = [[0, 1], [0, -1], [-1, 0], [1, 0]]

    # Loop until you find the end
    while len(open_list) > 0:
        outer_iterations += 1

        if outer_iterations > max_iterations:
          # if we hit this point return the path such as it is
          # it will not contain the destination
          warn("giving up on pathfinding too many iterations")

          return return_path(current_node)

        # Get the current node
        current_node = heapq.heappop(open_list)
        closed_list.append(current_node)

        # Found the goal
        if current_node.tile == end_node.tile:
            return return_path(current_node)

        # Generate children
        children = []

        for tile in adjacent_squares: # Adjacent squares
            # Get node position
            node_tile = [current_node.tile[0] + tile[0], current_node.tile[1] + tile[1]]
            # Make sure within range
            if node_tile[0] > map.size * 32 or node_tile[0] < 0 or node_tile[1] > map.size or node_tile[1] < 0:
                continue

            if (node_tile[0], node_tile[1]) not in map.tiles:
                continue
            if not map.tiles[node_tile[0], node_tile[1]].walkable:
                continue

            new_node = Node(current_node, node_tile)
            children.append(new_node)

        for child in children:
            # Child is on the closed list
            if len([closed_child for closed_child in closed_list if closed_child == child]) > 0:
                continue

            # Create the f, g, and h values
            child.g = current_node.g + 1
            child.h = ((child.tile[0] - end_node.tile[0]) ** 2) + ((child.tile[1] - end_node.tile[1]) ** 2)
            child.f = child.g + child.h

            # Child is already in the open list
            if len([open_node for open_node in open_list if child.tile == open_node.tile and child.g > open_node.g]) > 0:
                continue

            # Add the child to the open list
            heapq.heappush(open_list, child)

    warn("Couldn't get a path to destination")
    return None
