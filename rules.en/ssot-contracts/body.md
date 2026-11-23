# SSOT and Contracts

Do not bury volatile values and the agreements between stages deep inside the code. Keep one single truth for what is actually running.

## Do

- Put **volatile numbers, ordering, wait times, and the meaning of flags** in data (profile / config), and keep the code limited to predicates and executors
- Do not treat explanatory documents as the runtime source of truth. If the data is the source of truth, documents should contain only intent and rationale
- **Make contracts between stages explicit** (what is passed, how many of the latest items, what failure or no output means, who holds state)
- Before adding queues or buffering, first decide "latest one only / backpressure / no duplicate execution"
- **Keep one source of truth for operations**. Do not make copies outside the repo, shadow `/tmp` production setups, or reliance on manual syncing the norm. If duplicates exist, make the boundary and the switchover procedure explicit

## Don't

- Manage the same constant in triplicate across code, notes, and separate scripts
- Make a temporary one-line text or shared file permanent without discussing the contract
- Modify things while "what is running now" and "what is being edited" remain separate and you cannot say which one is authoritative
- Introduce hot reloading or a general-purpose rule language before the SSOT

## Decision test

When in doubt: **Where is the source of truth for this value / contract? Have you created a second one?**
