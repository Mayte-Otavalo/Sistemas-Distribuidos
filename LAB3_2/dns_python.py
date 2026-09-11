import dns.resolver
import dns.reversename
import dns.message
import dns.query


def print_answers(title, answers):
    print("\n============================")
    print(title)
    print("============================")

    for answer in answers:
        print(answer)


# ---------------------------------
# 1. Basic lookup
# ---------------------------------

answers = dns.resolver.resolve(
    "yachaytech.edu.ec",
    "A"
)

print_answers(
    "1. Basic Lookup",
    answers
)


# ---------------------------------
# 2. Reverse lookup
# ---------------------------------

reverse_name = dns.reversename.from_address(
    "8.8.8.8"
)

answers = dns.resolver.resolve(
    reverse_name,
    "PTR"
)

print_answers(
    "2. Reverse Lookup",
    answers
)


# ---------------------------------
# 3. Specific DNS server
# ---------------------------------

cloudflare = dns.resolver.Resolver()

cloudflare.nameservers = [
    "1.1.1.1"
]

answers = cloudflare.resolve(
    "hpc.cedia.edu.ec",
    "A"
)

print_answers(
    "3. Cloudflare DNS",
    answers
)


# ---------------------------------
# 4. MX records
# ---------------------------------

answers = dns.resolver.resolve(
    "yachaytech.edu.ec",
    "MX"
)

print_answers(
    "4. MX Records",
    answers
)


# ---------------------------------
# 5. NS records
# ---------------------------------

answers = dns.resolver.resolve(
    "yachaytech.edu.ec",
    "NS"
)

print_answers(
    "5. NS Records",
    answers
)


# ---------------------------------
# 6. SOA
# ---------------------------------

answers = dns.resolver.resolve(
    "yachaytech.edu.ec",
    "SOA"
)

print_answers(
    "6. SOA Record",
    answers
)


# ---------------------------------
# 7. CNAME
# ---------------------------------

print("\n============================")
print("7. CNAME")
print("============================")

try:

    answers = dns.resolver.resolve(
        "www.microsoft.com",
        "CNAME"
    )

    for answer in answers:
        print(answer)

except dns.resolver.NoAnswer:
    print("No CNAME record returned")


# ---------------------------------
# 8. Debug-like full DNS response
# ---------------------------------

print("\n============================")
print("8. Detailed DNS Response")
print("============================")

query = dns.message.make_query(
    "yachaytech.edu.ec",
    "A"
)

response = dns.query.udp(
    query,
    "1.1.1.1"
)

print(response.to_text())


# ---------------------------------
# 9. Non-existent domain
# ---------------------------------

print("\n============================")
print("9. Non-existent Domain")
print("============================")

try:

    answers = dns.resolver.resolve(
        "nonexistdomain12345.com",
        "A"
    )

    for answer in answers:
        print(answer)

except dns.resolver.NXDOMAIN:

    print("NXDOMAIN: Domain does not exist")