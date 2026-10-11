Feature: Delivery decisions distinguish risk from missing evidence
  Scenario Outline: Return an explicit policy result and process exit code
    Given the normalized "<fixture>" policy report
    When the security gate evaluates the report
    Then the gate result is "<result>" with exit code <exit_code>

    Examples:
      | fixture | result | exit_code |
      | pass    | PASS   | 0         |
      | warn    | WARN   | 0         |
      | fail    | FAIL   | 1         |
      | error   | ERROR  | 2         |
