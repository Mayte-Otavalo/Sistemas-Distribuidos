locations = {
    "A": "B",
    "B": "C",
    "C": "D",
    "D": "192.168.1.50:5000"
}


def resolve(location):

    hops = 0

    while location in locations:

        print(
            "Following:",
            location,
            "->",
            locations[location]
        )

        location = locations[location]

        hops += 1

    return location, hops


# ----------------------------
# 1. Resolución original
# ----------------------------

print("=== BEFORE OPTIMIZATION ===")

address, hops = resolve("A")

print("Final address:", address)
print("Number of hops:", hops)


# ----------------------------
# 2. Crear shortcut
# ----------------------------

locations["A"] = address


# ----------------------------
# 3. Resolver nuevamente
# ----------------------------

print("\n=== AFTER OPTIMIZATION ===")

address2, hops2 = resolve("A")

print("Final address:", address2)
print("Number of hops:", hops2)


# ----------------------------
# 4. Comparación
# ----------------------------

print("\n=== COMPARISON ===")

print("Before optimization:", hops, "hops")
print("After optimization:", hops2, "hops")