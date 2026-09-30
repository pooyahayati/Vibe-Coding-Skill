CUSTOMERS: list[dict[str, str]] = []


def create_customer(email: str) -> dict[str, str]:
    customer = {"email": email}
    CUSTOMERS.append(customer)
    return customer
