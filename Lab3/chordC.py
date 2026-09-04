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


def in_interval(value, start, end):
    """
    Comprueba si value está en el intervalo
    circular (start, end).
    """

    if start < end:
        return start < value < end

    return value > start or value < end


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

    # -------------------------
# PARTE C
# Lookup usando Finger Table
# -------------------------

def in_interval(value, start, end):
    """
    Retorna True si 'value' está dentro del
    intervalo circular (start, end).
    """

    if start < end:
        return start < value < end

    # Caso donde el intervalo cruza por 0
    return value > start or value < end


def lookup(start_node, key):

    current = start_node
    hops = 0

    print("\n========================")
    print(f"Lookup key {key}")
    print(f"Starting node: {start_node}")
    print("========================")

    print(current)

    while True:

        # Buscar el sucesor inmediato
        next_node = successor(
            (current + 1) % RING_SIZE
        )

        # ---------------------------------
        # Verificar si la clave pertenece
        # al sucesor inmediato
        # ---------------------------------

        if current < next_node:

            found = (
                current < key <= next_node
            )

        else:

            # Caso circular:
            # ejemplo 28 -> 1
            found = (
                key > current
                or key <= next_node
            )

        if found:

            print("->", next_node)

            hops += 1

            print(
                "Final node:",
                next_node
            )

            print(
                "Total hops:",
                hops
            )

            return next_node

        # ---------------------------------
        # Buscar mejor nodo en Finger Table
        # ---------------------------------

        fingers = finger_table(current)

        chosen = next_node

        # Revisamos desde el finger
        # más grande hacia el más pequeño

        for entry in reversed(fingers):

            i, start, target = entry

            if in_interval(
                target,
                current,
                key
            ):

                chosen = target
                break

        # Avanzar al nodo seleccionado
        current = chosen

        hops += 1

        print("->", current)

        # -------------------------
# PRUEBAS PARTE C
# -------------------------

lookup(1, 26)

lookup(28, 12)