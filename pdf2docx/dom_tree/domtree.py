from typing import List


class Node:
    def __init__(self, element, is_root=False):
        self.element = element
        self.child = []
        self.is_root = is_root

    def is_child_of(self, node):
        """Check if self is a child of node"""
        if node.is_root:
            return True
        return False

    def add_child(self, node):
        self.child.append(node)


class DomTree:
    def __init__(self, elements):
        self.root = Node(None, is_root=True)
        self.elements = elements

    def parse_tree(self):
        stack_path: List[Node] = [self.root]

        for element in self.elements:
            node = Node(element)
            while True:
                if node.is_child_of(stack_path[-1]):
                    # 增加子节点
                    stack_path[-1].add_child(node)
                    # 压栈
                    stack_path.append(node)
                else:
                    stack_path.pop()
