# app/utils/contract_templates.py

# Basic templates - these would likely be expanded or loaded from files
# In a real app, these might be more structured prompts or actual templates.

def get_nda_template() -> str:
    """Returns a basic prompt template for generating an NDA."""
    return """
    Generate a simple Non-Disclosure Agreement (NDA) between two parties.
    Please include standard clauses for:
    1. Definition of Confidential Information.
    2. Obligations of the Receiving Party.
    3. Exclusions from Confidential Information.
    4. Term and Termination.
    5. Governing Law.

    Use placeholders like [Party 1 Name], [Party 2 Name], [Effective Date], [Term Length], [Jurisdiction].
    Make the language clear and concise.
    """

def get_rental_agreement_template() -> str:
    """Returns a basic prompt template for generating a Rental Agreement."""
    return """
    Generate a basic Residential Rental Agreement.
    Please include standard clauses for:
    1. Identification of Landlord and Tenant.
    2. Property Description.
    3. Lease Term (Start and End Dates).
    4. Rent Amount and Due Date.
    5. Security Deposit.
    6. Use of Premises.
    7. Maintenance and Repairs.
    8. Governing Law.

    Use placeholders like [Landlord Name], [Tenant Name], [Property Address], [Start Date], [End Date], [Rent Amount], [Security Deposit Amount], [Jurisdiction].
    Keep the language straightforward for residential use.
    """

CONTRACT_PROMPTS = {
    "nda": get_nda_template,
    "rental_agreement": get_rental_agreement_template,
    # Add more contract types here
}

def get_contract_prompt(contract_type: str) -> str | None:
    """Retrieves the prompt template for a given contract type."""
    generator_func = CONTRACT_PROMPTS.get(contract_type.lower())
    if generator_func:
        return generator_func()
    return None
