tree = {
    "ROOT": {
        "AMERICA": {
            "ECUADOR": {
                "IBARRA": {},
                "QUITO": {}
            },
            "USA": {}
        },
        "EUROPE": {}
    }
}


entities = {

    "IBARRA": {
        "server01": "10.0.1.20"
    },

    "QUITO": {
        "server02": "10.0.2.30"
    }
}

parents = {
    "IBARRA": "ECUADOR",
    "QUITO": "ECUADOR",
    "ECUADOR": "AMERICA",
    "USA": "AMERICA",
    "AMERICA": "ROOT",
    "EUROPE": "ROOT",
    "ROOT": None
}

def find_entity_domain(entity):

    for domain, domain_entities in entities.items():

        if entity in domain_entities:
            return domain

    return None

def ancestors(domain):

    path = []

    while domain is not None:

        path.append(domain)

        domain = parents[domain]

    return path

def lookup(entity, starting_domain):

    print(
        f"\nLooking for {entity}"
    )

    target_domain = find_entity_domain(entity)

    # Si no existe
    if target_domain is None:

        current = starting_domain

        while current is not None:

            print(current)

            current = parents[current]

        print(
            "Entity not found"
        )

        return None

    # Si está localmente
    if target_domain == starting_domain:

        print(starting_domain)

        print(
            "->",
            entity
        )

        address = entities[
            target_domain
        ][entity]

        print(
            "Address:",
            address
        )

        return address

    start_path = ancestors(
        starting_domain
    )

    target_path = ancestors(
        target_domain
    )

    # Buscar ancestro común
    common = None

    for domain in start_path:

        if domain in target_path:

            common = domain
            break

    # Subir
    current = starting_domain

    print(current)

    while current != common:

        current = parents[current]

        print(
            "->",
            current
        )

    # Bajar
    down_path = []

    current = target_domain

    while current != common:

        down_path.append(current)

        current = parents[current]

    down_path.reverse()

    for domain in down_path:

        print(
            "->",
            domain
        )

    print(
        "->",
        entity
    )

    address = entities[
        target_domain
    ][entity]

    print(
        "Address:",
        address
    )

    return address

lookup(
    "server01",
    "IBARRA"
)

lookup(
    "server02",
    "IBARRA"
)

lookup(
    "server99",
    "IBARRA"
)

server01_address = entities[
    "IBARRA"
].pop("server01")

entities[
    "QUITO"
]["server01"] = server01_address

lookup(
    "server01",
    "IBARRA"
)