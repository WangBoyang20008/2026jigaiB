"""Sorting algorithms implemented as step generators.

Each algorithm is a generator that yields a Step after every comparison or
swap, so the UI can replay the process frame by frame and tests can verify
correctness independently of rendering.
"""

from dataclasses import dataclass, field
from typing import Generator


@dataclass
class Step:
    """One visualizable moment of a sorting run."""

    array: list
    comparing: tuple = ()   # indices currently being compared
    swapping: tuple = ()    # indices currently being swapped/written
    sorted_upto: int = -1   # indices >= this are final (bubble/insertion style)
    comparisons: int = 0
    swaps: int = 0


@dataclass
class SortResult:
    name: str
    comparisons: int = 0
    swaps: int = 0


def bubble_sort(data):
    arr = list(data)
    n = len(arr)
    comparisons = swaps = 0
    for end in range(n - 1, 0, -1):
        for i in range(end):
            comparisons += 1
            yield Step(arr, comparing=(i, i + 1), sorted_upto=end + 1,
                       comparisons=comparisons, swaps=swaps)
            if arr[i] > arr[i + 1]:
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                swaps += 1
                yield Step(arr, swapping=(i, i + 1), sorted_upto=end + 1,
                           comparisons=comparisons, swaps=swaps)
    yield Step(arr, sorted_upto=0, comparisons=comparisons, swaps=swaps)


def insertion_sort(data):
    arr = list(data)
    comparisons = swaps = 0
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0:
            comparisons += 1
            yield Step(arr, comparing=(j, j + 1),
                       comparisons=comparisons, swaps=swaps)
            if arr[j] <= key:
                break
            arr[j + 1] = arr[j]
            swaps += 1
            yield Step(arr, swapping=(j, j + 1),
                       comparisons=comparisons, swaps=swaps)
            j -= 1
        arr[j + 1] = key
    yield Step(arr, sorted_upto=0, comparisons=comparisons, swaps=swaps)


def quick_sort(data):
    arr = list(data)
    comparisons = swaps = 0

    def partition(lo, hi):
        nonlocal comparisons, swaps
        pivot = arr[hi]
        i = lo
        for j in range(lo, hi):
            comparisons += 1
            yield Step(arr, comparing=(j, hi),
                       comparisons=comparisons, swaps=swaps)
            if arr[j] < pivot:
                arr[i], arr[j] = arr[j], arr[i]
                swaps += 1
                yield Step(arr, swapping=(i, j),
                           comparisons=comparisons, swaps=swaps)
                i += 1
        arr[i], arr[hi] = arr[hi], arr[i]
        swaps += 1
        yield Step(arr, swapping=(i, hi), comparisons=comparisons, swaps=swaps)
        return i

    def sort(lo, hi):
        if lo >= hi:
            return
        p = yield from partition(lo, hi)
        yield from sort(lo, p - 1)
        yield from sort(p + 1, hi)

    if arr:
        yield from sort(0, len(arr) - 1)
    yield Step(arr, sorted_upto=0, comparisons=comparisons, swaps=swaps)


def merge_sort(data):
    arr = list(data)
    comparisons = swaps = 0

    def merge(lo, mid, hi):
        nonlocal comparisons, swaps
        left, right = arr[lo:mid], arr[mid:hi]
        i = j = 0
        for k in range(lo, hi):
            if i < len(left) and j < len(right):
                comparisons += 1
                yield Step(arr, comparing=(lo + i, mid + j),
                           comparisons=comparisons, swaps=swaps)
            if j >= len(right) or (i < len(left) and left[i] <= right[j]):
                arr[k] = left[i]
                i += 1
            else:
                arr[k] = right[j]
                j += 1
            swaps += 1
            yield Step(arr, swapping=(k,), comparisons=comparisons, swaps=swaps)

    def sort(lo, hi):
        if hi - lo <= 1:
            return
        mid = (lo + hi) // 2
        yield from sort(lo, mid)
        yield from sort(mid, hi)
        yield from merge(lo, mid, hi)

    if arr:
        yield from sort(0, len(arr))
    yield Step(arr, sorted_upto=0, comparisons=comparisons, swaps=swaps)


def heap_sort(data):
    arr = list(data)
    comparisons = swaps = 0

    def sift_down(root, end):
        nonlocal comparisons, swaps
        while True:
            child = 2 * root + 1
            if child > end:
                return
            if child + 1 <= end:
                comparisons += 1
                yield Step(arr, comparing=(child, child + 1), sorted_upto=end + 1,
                           comparisons=comparisons, swaps=swaps)
                if arr[child + 1] > arr[child]:
                    child += 1
            comparisons += 1
            yield Step(arr, comparing=(root, child), sorted_upto=end + 1,
                       comparisons=comparisons, swaps=swaps)
            if arr[root] >= arr[child]:
                return
            arr[root], arr[child] = arr[child], arr[root]
            swaps += 1
            yield Step(arr, swapping=(root, child), sorted_upto=end + 1,
                       comparisons=comparisons, swaps=swaps)
            root = child

    n = len(arr)
    for root in range(n // 2 - 1, -1, -1):
        yield from sift_down(root, n - 1)
    for end in range(n - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]
        swaps += 1
        yield Step(arr, swapping=(0, end), sorted_upto=end,
                   comparisons=comparisons, swaps=swaps)
        yield from sift_down(0, end - 1)
    yield Step(arr, sorted_upto=0, comparisons=comparisons, swaps=swaps)


ALGORITHMS = {
    "bubble": ("冒泡排序 Bubble Sort", bubble_sort),
    "insertion": ("插入排序 Insertion Sort", insertion_sort),
    "quick": ("快速排序 Quick Sort", quick_sort),
    "merge": ("归并排序 Merge Sort", merge_sort),
    "heap": ("堆排序 Heap Sort", heap_sort),
}


def run_to_end(name, data) -> SortResult:
    """Run an algorithm without rendering; used by tests and benchmarks."""
    label, gen_fn = ALGORITHMS[name]
    last = None
    for last in gen_fn(data):
        pass
    result = SortResult(label)
    if last is not None:
        result.comparisons = last.comparisons
        result.swaps = last.swaps
    return result
