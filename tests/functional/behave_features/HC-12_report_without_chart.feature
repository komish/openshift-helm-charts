Feature: Report only submission
    Partners, redhat and community users can publish their chart by submitting
    error-free report that was generated by chart-verifier.

    Scenario Outline: [HC-12-001] A partner or redhat associate submits an error-free report
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And an error-free report is used in "<report_path>"
        When the user sends a pull request with the report
        Then the user sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
    
        @partners @smoke
        Examples:
            | vendor_type  | vendor    | report_path            |
            | partners     | hashicorp | tests/data/report.yaml |
        
        @redhat
        Examples:
            | vendor_type  | vendor    | report_path            |
            | redhat       | redhat    | tests/data/report.yaml |

    Scenario Outline: [HC-12-002] A community user submits an error-free report
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And an error-free report is used in "<report_path>"
        When the user sends a pull request with the report
        Then the pull request is not merged
        And user gets the "<message>" in the pull request comment

        @community @smoke
        Examples:
            | vendor_type | vendor  | report_path            | message                                                                                     |
            | community   | redhat  | tests/data/report.yaml | Community charts require maintainer review and approval, a review will be conducted shortly |