# Checks before deleting spec details

A procedure for confirming whether the details of behavior written in a spec document may be deleted from the document.
The code holds the description of the details, and the tests independently check it against the public surface. The prose in the document becomes the third copy, so delete it if the conditions are met.
The conditions for triggering follow Done means (spec compression) in change-discipline.
This file holds only the procedure; the criteria for judgment are in change-discipline.

## What can be deleted

Details that satisfy both of the following.

- The code expresses the detail (it exists in the implementation as a validation branch, an output format, or an error message)
- A test pins the detail on the public surface

Examples: enumerations of input/output cases, exact error messages, report/output formats, boundary values and their expected results.

## What cannot be deleted

Neither code nor tests can express the following. Keep them in the document.

- The why, the contract, and non-goals
- Completion conditions (the acceptance level itself)
- The scope that is intentionally not tested
- The conditions for oracle independence (what counts as correct. Example: the frozen sample is the correct answer, and expected values are not created from the implementation's output)

Neither code nor tests can express "what is not written" and "that expected values are independent of the implementation."

## Procedure

1. For each item, check whether the code expresses the detail. If it does not, the item is not a candidate for deletion (treat it as an unimplemented spec or a gap in the implementation)
2. Check whether a test pins it. If not, write or strengthen a test using the document's description as the oracle. Take expected values from the document, not from the implementation's current output
3. Apply the deletion criteria from change-discipline. Do not delete items that fail the criteria. Keep them in the document
4. Delete from the document only the items that meet the conditions. Do not copy the wording into tests or code
5. Run the entire suite
6. In the completion report, attach the items you deleted and the items you kept in the document

## Failure modes

- Writing tests with the implementation's current output as the expected values. The tests become subordinate to the implementation and lose their independence as a spec
- Deleting in bulk without checking item by item. Details that the code does not express, or that tests do not pin, disappear from the document as well
- Copying the wording of details into tests or code comments. Copies multiply, and so do the places where they can drift apart in the future
