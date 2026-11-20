# pygdo-poll
Poll module for PyGDO8. Create and broadcast polls over any connectors.


## From Humans To Humans

We feature two kinds of voting:

1) public vote - anyone can vote.
2) a vote/poll of the PyGDO Team . A user has a user_config "effective_poll_power"

## From ALs To ALs

Poll creation accepts a whole-day duration. `poll_credits_per_day` defaults to
zero; when nonzero, creation requires `payment_credits` and atomically debits
duration × daily price in the creation transaction. Polls are scheduled in
order, so a queued poll starts after the previous open poll expires. An old
open poll without an expiry needs to be closed or scheduled before another
poll can be queued. A Dog timer checks every 10 seconds and broadcasts active,
not-yet-announced polls; a failed call is retried on a later tick. If the Dog
is down for an entire poll, that expired poll is not announced. Email
announcements also wait until the start. Restart Dog and migrate the module
schema when deploying the new fields.

HTTP users vote on a specific poll; text users vote on the active poll with
`$poll.vote <choice> [<choice>...]` (or `$pv`). Choices use stable ID order.
Queued and expired polls cannot receive votes. Outcomes render as HTML lists
and as numbered text for connectors.

Open design: public and effective/team polls are not yet distinguished or
weighted. Define who can create each kind and whether vote power is captured
at voting time before implementing that distinction. Existing announcements
are best effort; validate queue recovery and notification behavior on a real
installation before relying on it.
