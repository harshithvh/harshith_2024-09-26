# StoreMonitoring
Backend service to generate report of uptime and downtimes for all Stores.

## Uptime and Downtime Calculation
- terate through chronologically ordered poll data
- Calculate time deltas between polls and assign to uptime or downtime
- Extrapolate status for gaps between polls and business hours

## Report Generation
- Process data for three time periods: last hour, last day, and last week
- Aggregate calculated uptime and downtime for each time period
- Round values to the nearest integer (ceiling)

## Further improvements
1. Add validation layer to ensure the integrity of input data
2. Implement a caching mechanism using Redis for frequently accessed data to reduce database load.
3. Parallelizing the processing of stores or asynchronous programming.
4. Assumptions to be avoided as much as possible
5. Avoid/Reduce fields with the same meaning - uptime_last_hour/day/week
6. Implement versioning for the API to allow for future changes - v1/v2

## Edge Cases Covered
1. Used Math.ceil for worst cases - uptime and downtime calculations
2. Used delta to fill in the time gaps - status poll
3. Used joinload() for data fetching in a single query - DB load