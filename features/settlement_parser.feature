Feature: HKEX Settlement Price Parser
  As a financial analyst
  I want to download and parse HKEX settlement price files
  So that I can analyze stock option contract data

  Background:
    Given the HKEX settlement parser is running
    And the database connections are healthy

  Scenario: Download settlement data for a specific date
    Given I want to download settlement data for "2023-08-22"
    When I download the settlement data
    Then the download should be successful
    And the data should be stored in the database
    And I should receive a success response

  Scenario: Search for HTI symbol in settlement data
    Given settlement data exists for "2023-08-22"
    When I search for symbol "HTI"
    Then I should find HTI records
    And the records should contain settlement prices
    And the records should contain volume and open interest data

  Scenario: Search for non-existent symbol
    Given settlement data exists for "2023-08-22"
    When I search for symbol "INVALID"
    Then I should receive no records
    And the response should indicate no data found

  Scenario: Get list of available trading dates
    Given multiple trading dates have been processed
    When I request the list of trading dates
    Then I should receive a list of dates
    And each date should have record count information
    And the dates should be sorted by most recent first

  Scenario: Get symbols for a specific date
    Given settlement data exists for "2023-08-22"
    When I request symbols for "2023-08-22"
    Then I should receive a list of unique symbols
    And the symbols should include "HTI" and "HSI"

  Scenario: Download data for invalid date
    Given I want to download settlement data for "2023-08-23"
    And the date is not a trading day
    When I download the settlement data
    Then the download should fail
    And I should receive an error message

  Scenario: Parse settlement file with invalid format
    Given a settlement file with invalid format
    When I parse the file
    Then the parsing should handle the error gracefully
    And I should receive an empty result set

  Scenario: Cache functionality for repeated requests
    Given I have previously downloaded data for "2023-08-22"
    When I request the same data again
    Then the response should come from cache
    And the response time should be faster

  Scenario: Health check of all services
    Given all database services are running
    When I check the system health
    Then all services should report as healthy
    And the response should include connection status for each service
