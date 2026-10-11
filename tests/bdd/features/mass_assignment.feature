Feature: A normal update cannot change protected fields
  Background:
    Given the synthetic lab starts from a clean state
    And two customers and a property owned by the first customer

  Scenario Outline: Reject protected fields without partially changing state
    When the owner includes the protected field "<field>" in an otherwise valid update
    Then the API returns HTTP 400
    And the original property remains unchanged

    Examples:
      | field      |
      | ownerId    |
      | role       |
      | isVerified |
