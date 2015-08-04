Feature: Name Conversion

Scenario: New Registers are Converted & Added to Names-Search

Given new data is posted to the queue
When the system runs
Then the reformatted data is stored in ElasticSearch
