"""
RRT-algorithm built by Atsushi Sakai. Modified by us to incorporate what we need.

author: Atsushi Sakai(@Atsushi_twi)
"""

import math
import random
from shapely.geometry import LineString
from Python.ImageProcessing.mazeRecognizer import mazeRecognizer
import matplotlib.pyplot as plt

show_animation = False
show_final_animation = True


class RRT:
    class Node:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.path_x = []
            self.path_y = []
            self.parent = None

    def __init__(self, start, goal, rand_area_x, rand_area_y, lineList, edge_dist, expand_dis=0.5,
                 path_resolution=0.1, goal_sample_rate=5, max_iter=7000):
        """

        :param start: Start point coordinates
        :param goal: Goal point coordinates
        :param rand_area_x: Area in x-plane which the nodes can be randomly be placed
        :param rand_area_y: Area in y-plane which the nodes can be randomly place
        :param lineList: list of lines for obstacle-lines
        :param edge_dist: distance for rrt to keep from the obstacles
        :param expand_dis: expand distance
        :param path_resolution: not in use
        :param goal_sample_rate: chance for it to try to just go to goal
        :param max_iter: max iterations
        """
        self.start = self.Node(start[0], start[1])
        self.end = self.Node(goal[0], goal[1])
        self.min_rand_x = rand_area_x[0]
        self.max_rand_x = rand_area_x[1]
        self.min_rand_y = rand_area_y[0]
        self.max_rand_y = rand_area_y[1]
        self.expand_dis = expand_dis
        self.path_resolution = path_resolution
        self.goal_sample_rate = goal_sample_rate
        self.max_iter = max_iter
        self.node_list = []
        self.lineList = lineList
        self.edge_dist = edge_dist

    def planning(self, animation=False):
        """
        Finds a path through a maze.
        :param animation: flag for animation on or off
        """
        self.node_list = [self.start]
        for i in range(self.max_iter):
            rnd_node = self.getRandomNode()
            nearest_ind = self.getNearestNodeIndex(self.node_list, rnd_node)
            nearest_node = self.node_list[nearest_ind]

            new_node = self.steer(nearest_node, rnd_node, self.expand_dis)

            if self.checkObstacle(new_node, self.lineList, self.edge_dist):
                self.node_list.append(new_node)

            if animation and i % 5 == 0:
                self.drawGraph(rnd_node)

            if self.calculateDistanceToGoal(self.node_list[-1].x, self.node_list[-1].y) <= self.expand_dis:
                final_node = self.steer(self.node_list[-1], self.end, self.expand_dis)
                if self.checkObstacle(final_node, self.lineList, self.edge_dist):
                    return self.generateFinalCourse(len(self.node_list) - 1)

            if animation and i % 5:
                self.drawGraph(rnd_node)

        return None

    def steer(self, from_node, to_node, extend_length=float("inf")):
        """
        Steers a node to a new node.

        :param from_node: the node to go from
        :param to_node: the node to go to
        :param extend_length: the expand distance
        :return: new node with run coordinates
        """
        new_node = self.Node(from_node.x, from_node.y)
        d, theta = self.calculateDistanceAndAngle(new_node, to_node)

        new_node.path_x = [new_node.x]
        new_node.path_y = [new_node.y]

        if extend_length > d:
            extend_length = d

        new_node.x += extend_length * math.cos(theta)
        new_node.y += extend_length * math.sin(theta)
        new_node.path_x.append(new_node.x)
        new_node.path_y.append(new_node.y)

        new_node.parent = from_node

        return new_node

    def drawGraph(self, rnd=None):
        """
        Plots everything, if there is a node sent in, \n
        it will plot this nodes placement.

        :param rnd: the node to plot
        :return: Nothing
        """
        plt.clf()
        if rnd is not None:
            plt.plot(rnd.x, rnd.y, "^k")
        for node in self.node_list:
            if node.parent:
                plt.plot(node.path_x, node.path_y, "-g")

        for (data) in self.lineList:
            x1 = data[0][0]
            y1 = data[0][1]
            x2 = data[0][2]
            y2 = data[0][3]
            self.plotObstacle(x1, y1, x2, y2)

        plt.plot(self.start.x, self.start.y, "xr")
        plt.plot(self.end.x, self.end.y, "xr")
        plt.axis("equal")
        plt.axis([0, 1920, 0, 1080])
        plt.grid(False)
        plt.pause(0.01)

    def generateFinalCourse(self, goal_ind):
        """
        Generates the final course if the goal is found.

        :param goal_ind: Index for goal node
        :return: the final path from start to goal
        """
        path = [[self.end.x, self.end.y]]
        node = self.node_list[goal_ind]
        while node.parent is not None:
            path.append([node.x, node.y])
            node = node.parent
        path.append([node.x, node.y])

        return path

    def calculateDistanceToGoal(self, x, y):
        """
        Calculates the distance to goal from a set of coordinates

        :param x: coordinate
        :param y: coordinate
        :return: the distance from coordinates to goal
        """
        dx = x - self.end.x
        dy = y - self.end.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def getRandomNode(self):
        """
        Creates a node in a random place

        :return: new randomly placed node
        """
        if random.randint(0, 100) > self.goal_sample_rate:
            rnd = self.Node(random.uniform(self.min_rand_x, self.max_rand_x),
                            random.uniform(self.min_rand_y, self.max_rand_y))
        else:
            rnd = self.Node(self.end.x, self.end.y)
        return rnd

    @staticmethod
    def plotObstacle(x1, y1, x2, y2):
        """
        Plots the lines for the obstacles.

        :param x1: x1 coordinate for obstacle
        :param y1: y1 coordinate for obstacle
        :param x2: x2 coordinate for obstacle
        :param y2: y2 coordinate for obstacle
        :return:
        """
        plt.plot([x1, x2], [y1, y2], color='k', linestyle='-', linewidth=1)

    @staticmethod
    def checkObstacle(node, lineList, edgeDistance):
        """
        Checks if the nodes path collides with obstacle. \n
        Also checks how close to the obstacle the line \n
        will go.

        :param node: Node to check collision for
        :param lineList: List of lines for obstacles
        :param edgeDistance: Distance to keep from the obstacles
        :return: True if no collision, false if collision
        """
        dx_list = [x for x in node.path_x]
        dy_list = [y for y in node.path_y]
        node_line = LineString([(x, y) for (x, y) in zip(dx_list, dy_list)])
        for data in lineList:
            x1 = data[0][0]
            y1 = data[0][1]
            x2 = data[0][2]
            y2 = data[0][3]
            obst = LineString([(x1, y1), (x2, y2)])
            if obst.intersects(node_line):
                return False
            if obst.distance(node_line) < edgeDistance:
                return False
        return True

    @staticmethod
    def getNearestNodeIndex(node_list, rnd_node):
        """
        Gets the index for the nearest node.

        :param node_list: list of all nodes
        :param rnd_node: node to check against
        :return: the index of the nearest node
        """
        dlist = [(node.x - rnd_node.x) ** 2 + (node.y - rnd_node.y)
                 ** 2 for node in node_list]
        minind = dlist.index(min(dlist))

        return minind

    @staticmethod
    def calculateDistanceAndAngle(from_node, to_node):
        """
        Calculates distance and angle between two nodes.

        :param from_node: the node from which to check
        :param to_node: the node to which to check
        :return: the distance and angle
        """
        dx = to_node.x - from_node.x
        dy = to_node.y - from_node.y
        d = math.sqrt(dx ** 2 + dy ** 2)
        theta = math.atan2(dy, dx)
        return d, theta


def main():
    m = mazeRecognizer()
    lines, _ = m.findMaze()
    rrt = RRT(start=[810, 385], goal=[1250, 150], rand_area_x=[250, 1500], rand_area_y=[0, 1100],
              lineList=lines, expand_dis=50.0, path_resolution=25.0, max_iter=1000, goal_sample_rate=20,
              edge_dist=30)

    path = rrt.planning()

    showFinalAnimation = True

    if path is None:
        fig = plt.figure()
        fig.add_subplot(111)
        rrt.drawGraph()
    else:
        print("found path!!")

        # Draw final path
        if showFinalAnimation:
            rrt.drawGraph()
            fig = plt.figure()
            fig.add_subplot(111)
            plt.plot([x for (x, y) in path], [y for (x, y) in path], '-r')
            for (data) in rrt.lineList:
                x1 = data[0][0]
                y1 = data[0][1]
                x2 = data[0][2]
                y2 = data[0][3]
                rrt.plotObstacle(x1, y1, x2, y2)
            plt.grid(True)
            plt.pause(0.01)  # Need for Mac
            plt.show()


if __name__ == '__main__':
    main()
