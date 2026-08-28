"""
core/heap.py
------------
A genuine, from-scratch array-based binary MIN-HEAP implementation.

This is intentionally NOT a thin wrapper around Python's `heapq` module.
It is written out explicitly (parent/child index math, sift-up, sift-down)
so that the priority-queue mechanics behind Huffman's greedy algorithm are
fully visible and explainable during a viva.

Heap property: for every node i, heap[i] <= heap[left(i)] and
heap[i] <= heap[right(i)]  (using HuffmanNode.__lt__ for comparisons).

Supported operations (classic binary heap complexities):
    push(item)      -> O(log n)
    pop_min()        -> O(log n)
    peek()           -> O(1)
    __len__          -> O(1)
"""


class MinHeap:
    """Array-based binary min-heap over any objects supporting `<`."""

    def __init__(self):
        self._data = []

    def __len__(self):
        return len(self._data)

    def is_empty(self):
        return len(self._data) == 0

    # ---- index helpers -------------------------------------------------
    @staticmethod
    def _parent(i):
        return (i - 1) // 2

    @staticmethod
    def _left(i):
        return 2 * i + 1

    @staticmethod
    def _right(i):
        return 2 * i + 2

    def _swap(self, i, j):
        self._data[i], self._data[j] = self._data[j], self._data[i]

    # ---- core operations -------------------------------------------------
    def push(self, item):
        """Insert `item`, then restore the heap property by sifting up."""
        self._data.append(item)
        self._sift_up(len(self._data) - 1)

    def peek(self):
        """Return (without removing) the minimum element."""
        if self.is_empty():
            raise IndexError("peek from an empty heap")
        return self._data[0]

    def pop_min(self):
        """Remove and return the minimum element, restoring heap property."""
        if self.is_empty():
            raise IndexError("pop_min from an empty heap")

        minimum = self._data[0]
        last = self._data.pop()  # remove the last element from the array
        if self._data:
            self._data[0] = last
            self._sift_down(0)
        return minimum

    # ---- internal restructuring -------------------------------------------
    def _sift_up(self, i):
        while i > 0:
            parent = self._parent(i)
            if self._data[i] < self._data[parent]:
                self._swap(i, parent)
                i = parent
            else:
                break

    def _sift_down(self, i):
        n = len(self._data)
        while True:
            left = self._left(i)
            right = self._right(i)
            smallest = i

            if left < n and self._data[left] < self._data[smallest]:
                smallest = left
            if right < n and self._data[right] < self._data[smallest]:
                smallest = right

            if smallest == i:
                break

            self._swap(i, smallest)
            i = smallest

    def to_sorted_list(self):
        """Non-destructive snapshot of the heap contents, sorted (for display)."""
        return sorted(self._data)
