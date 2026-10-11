Feature: Customer data stays inside its ownership boundary
  Background:
    Given the synthetic lab starts from a clean state
    And two customers and a property owned by the first customer

  Scenario Outline: Check ownership before reading or changing a property
    When the "<actor>" customer sends "<method>" for that property
    Then the API returns HTTP <status>
    And the original property remains unchanged

    Examples:
      | actor | method | status |
      | owner | GET    | 200    |
      | other | GET    | 404    |
      | other | PATCH  | 404    |
