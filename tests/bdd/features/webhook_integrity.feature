Feature: Integration events must be authentic, fresh and idempotent
  Background:
    Given the synthetic lab starts from a clean state

  Scenario Outline: Invalid notifications cannot pay an invoice
    Given a "<kind>" payment notification for an open synthetic invoice
    When the payment notification is received
    Then the API returns HTTP 401
    And the invoice remains open with no claimed events

    Examples:
      | kind    |
      | missing |
      | forged  |
      | stale   |

  Scenario: A valid duplicate does not apply the payment twice
    Given a "valid" payment notification for an open synthetic invoice
    When the payment notification is received
    Then the API returns HTTP 200
    And the invoice is paid with exactly one claimed event
    When the same payment notification is received again
    Then the API returns HTTP 200
    And the response identifies a duplicate
    And the invoice is paid with exactly one claimed event
