# Porting from spec to tests

The procedure for moving test specifications written in the spec document into test code.
The trigger conditions follow change-discipline's Done means (spec compression).
This file contains only the procedure; the criteria for judgment are in change-discipline.

## What to port

The fine details of behavior.

- Enumeration of input/output cases
- Exact error message text
- Report and output formats
- Boundary values and their expected results

## What not to port

The following cannot be expressed in test code. Leave them in the document.

- The why, the contract, and non-goals
- Completion conditions (the acceptance level itself)
- Ranges intentionally not tested
- Conditions for oracle independence (what counts as correct. Example: the frozen sample is the correct answer, and expected values are not derived from the implementation's output)

Test code cannot express "what is not written" or "that expected values are independent of the implementation."

## Procedure

1. Using the document's description as the oracle, write or strengthen the corresponding tests. Take expected values from the document
2. For each item, apply change-discipline's deletion criteria. Do not port items that fail the criteria. Leave them in the document, or strengthen the tests first
3. Delete from the document only the items the tests have pinned down
4. Run the entire suite
5. In the completion report, attach the items ported and the items left in the document

## Failure modes

- Porting the implementation's current output as the expected value. The tests become subordinate to the implementation and lose their independence as a spec
- Deleting in bulk without checking item by item. Details that the tests have not pinned down vanish from both the document and the tests
