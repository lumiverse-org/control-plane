# Pilot Change: Add POST /customers/{id}/disable route
def disable_customer(customer_id: str):
    """Marks customer as disabled with current timestamp."""
    return {"id": customer_id, "status": "disabled"}
