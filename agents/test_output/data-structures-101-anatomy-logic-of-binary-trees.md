# Data Structures 101: Anatomy & Logic of Binary Trees

## Table of Contents

---

# Data Structures 101: Anatomy & Logic of Binary Trees
### Understanding Hierarchical Data, Recursion, and The Binary Search Property


---


## 1. Introduction to Binary Trees

Unlike arrays or linked lists, which are linear data structures, trees are hierarchical. A  is a specific type of tree where each node has at most two children, typically referred to as the  and the .

To understand trees, we must define their anatomy:

We measure the scale of trees using  (distance from root to a specific node) and  (longest path from the root to a leaf).

> 💡 **TIP**
> 
> 
 Think of your computer's File System. The "Root" directory contains folders (subtrees) and files (leaves). The HTML Document Object Model (DOM) is also a tree structure.


![Diagram showing Root, Leaf, Edge, Height, and Depth of a binary tree](images\img_1.png)

```mermaid
graph TD
    A((Root)) --> B((Child L))
    A --> C((Child R))
    B --> D((Leaf))
    B --> E((Leaf))
    C --> F((Leaf))
    C --> G((Leaf))
    style A fill:#f9f,stroke:#333,stroke-width:4px
    style D fill:#bbf,stroke:#333,stroke-width:2px
    style E fill:#bbf,stroke:#333,stroke-width:2px
    style F fill:#bbf,stroke:#333,stroke-width:2px
    style G fill:#bbf,stroke:#333,stroke-width:2px
```


---


## 2. Implementing the Node Structure

A tree is not a single contiguous block of memory like an array. It is a collection of objects (Nodes) linked together by references (pointers). The fundamental building block is the .

Every node must contain three specific components:

**Python TreeNode Class**
```python

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left    # Reference to left child
        self.right = right  # Reference to right child

# Example Usage:
# Creating the root
root = TreeNode(10)

# Adding children
root.left = TreeNode(5)
root.right = TreeNode(15)

# Structure created:
#      10
#     /  \
#    5    15

```

> ℹ️ **INFO**
> 
> 
In memory, these nodes may be scattered. The  and  attributes act as the address map that holds the structure together.



---


## 3. Tree Traversals (DFS)

Because trees are non-linear, there is no single "correct" way to iterate through them. We use  traversals to visit nodes. The order in which we process the "Root" (current node) relative to its children determines the traversal type.

![Visual comparison of Pre-order, In-order, and Post-order traversal paths](images\img_2.png)

**Recursive In-order Traversal**
```python

def inorder_traversal(node):
    # Base Case: If the node is None, stop recursion
    if node is None:
        return

    # 1. Traverse Left Subtree
    inorder_traversal(node.left)
    
    # 2. Process Current Node (Root)
    print(node.val)
    
    # 3. Traverse Right Subtree
    inorder_traversal(node.right)

```


---


## 4. The Binary Search Tree (BST) Property

A Binary Search Tree (BST) is a special kind of binary tree that enforces a strict logic, known as the :

> ⚠️ **WARNING**
> 
> 
 For any given node, all values in its  must be smaller than the node, and all values in its  must be larger.


This property turns the tree into a powerful search tool. Instead of checking every element (like in an unsorted array), we can eliminate half the tree at every step. If we are looking for the number 50, and the current node is 100, we know with certainty that 50 must be to the left, and we can ignore the entire right side.

![Comparison of a Valid Binary Search Tree vs an Invalid one](images\img_3.png)

```mermaid
graph TD
    subgraph Valid BST
    A((10)) --> B((5))
    A --> C((15))
    C --> D((12))
    C --> E((20))
    end
    
    subgraph Invalid BST
    X((10)) --> Y((5))
    X --> Z((15))
    Z --> Q((9))
    style Q fill:#ff9999,stroke:#f00,stroke-width:2px
    end
```




---


## 5. Algorithmic Complexity Analysis

The efficiency of a Binary Tree depends heavily on its shape (topology).

![Graph comparing O(n) and O(log n) complexity](images\img_4.png)

### Key Takeaways


---
