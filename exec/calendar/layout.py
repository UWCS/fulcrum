import itertools

from exec.calendar.config import GRID_SIZES, MAX_GRID_COLS, MAX_GRID_ROWS


def backtrack(groups: list[tuple[int, list[int]]], grid: list[list[int]]) -> list[list[int]] | None:
    """backtracking algorithm to fit items into grid"""

    # base case, just return grid, we good :)
    if not groups:
        return grid

    # get next group of events to place
    group_id, (width, height) = groups[0]
    remaining_groups = groups[1:]
    num_rows, num_cols = len(grid), len(grid[0])

    for row in range(num_rows - height + 1):
        for col in range(num_cols - width + 1):
            # check if space is free
            is_free = all(
                grid[i][j] == -1 for i in range(row, row + height) for j in range(col, col + width)
            )

            # try again if not free
            if not is_free:
                continue

            # place group in grid
            new_grid = [r.copy() for r in grid]
            for i in range(row, row + height):
                for j in range(col, col + width):
                    new_grid[i][j] = group_id

            # recurse for remaining groups
            solution = backtrack(remaining_groups, new_grid)

            # if solution found, return it
            if solution is not None:
                return solution

    # no solution found
    return None


def get_event_groups(
    event_groups: list[int],
) -> tuple[list[list[int]], list[list[int]]]:
    """Pack events into groups and return group dimensions and layout"""

    # allowed shapes for groups (width, height)
    combinations = {
        1: [[1, 1]],
        2: [[2, 1], [1, 2]],
        3: [[3, 1], [2, 2], [1, 3]],
        4: [[2, 2], [4, 1]],
        5: [[3, 2], [2, 3], [4, 2]],
        6: [[3, 2], [2, 3], [4, 2]],
    }

    # get possible sizes of grids
    grid_sizes = GRID_SIZES[int(sum(event_groups) / 2 - 1) :]

    # get all combinations of shapes for the event groups
    try:
        shape_options = [combinations[n] for n in event_groups]
    except KeyError:
        raise ValueError(
            f"Cannot fit more than {MAX_GRID_COLS * MAX_GRID_ROWS} events in a day"
        ) from None
    all_options = list(itertools.product(*shape_options))

    for num_cols, num_rows in grid_sizes:  # try smallest grids first
        for shape in all_options:  # try all shape combinations
            items = list(enumerate(shape))  # [idx, (width, height)]

            base_grid = [[-1] * num_cols for _ in range(num_rows)]

            # try to fit items into grid
            layout = backtrack(items, base_grid)

            # if successful, return shape and layout
            if layout is not None:
                return list(shape), layout
    raise ValueError("Could not fit events into grid")
