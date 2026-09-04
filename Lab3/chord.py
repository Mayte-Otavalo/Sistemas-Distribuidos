M = 5

RING_SIZE = 2 ** M

nodes = [
    1, 4, 9, 11, 14,
    18, 20, 21, 28
]


def successor(key):

    for node in nodes:

        if node >= key:
            return node

    return nodes[0]


# -------------------------
# PARTE A
# -------------------------

print("=== SUCCESSOR TEST ===")

for key in [3, 8, 12, 19, 26, 30]:

    print(
        "Key:", key,
        "-> node:",
        successor(key)
    )


# -------------------------
# PARTE B
# Finger Tables
# -------------------------

def finger_table(node):

    table = []

    for i in range(M):

        start = (
            node + 2**i
        ) % RING_SIZE

        target = successor(start)

        table.append(
            (
                i + 1,
                start,
                target
            )
        )

    return table


# -------------------------
# Mostrar tabla del nodo 1
# -------------------------

print("\n=== FINGER TABLE NODE 1 ===")

print("i\tstart\tsuccessor")

for entry in finger_table(1):

    i, start, target = entry

    print(
        f"{i}\t{start}\t{target}"
    )