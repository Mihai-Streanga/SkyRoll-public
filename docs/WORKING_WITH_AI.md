# Working with an AI coding agent

SkyRoll was built by one payroll specialist, who is not a software engineer, working with
an AI coding agent. The agent wrote most of the code. This page describes the principles
that made that workable for a tool whose numbers end up on people's payslips.

## The division of labour

The agent proposes and writes. Deterministic code computes. The specialist decides.

No number in a SkyRoll workbook comes from a language model: every amount is produced by
code that can be read, tested and rerun. The agent's role is to write that code and to
explain it; the specialist's role is to say whether the result is right, because the
specialist knows the payroll and the agent does not.

## Proof, not reports

An agent can say "all tests pass" whether or not it ran them. So a claim counts only
together with the output of the command that supports it, reproduced as it came. "Nothing
found" is reported as what it is: nothing found by that particular check, with what the
check does not cover said next to it.

## Rules that are enforced, not remembered

A rule written only in instructions is followed most of the time. A rule that matters is
also enforced by something that does not forget: a permission the agent does not have, a
hook that refuses a commit, a test that fails, a checker that runs at the end of a
session. When a rule keeps being broken, the answer is to move it from text into a
mechanism.

## Safety nets stay on

The guard that refuses an incomplete statement and the checks on the written workbook are
never disabled to get a run through. If they block something, the cause is fixed, or the
net itself is changed deliberately, with the reason written down.

## One change at a time

One change, then the specialist tests it, then it is committed. Several changes at once
make it impossible to tell which one broke something, and a specialist who is not a
programmer cannot untangle them afterwards.

## Real data out of reach

The agent cannot read the folder that holds real payroll statements. Tests that need
real statements read them at run time, outside the agent's view; everything the agent
works with directly is code, structure, counts and synthetic data.

## Stop after two failures

When the same approach fails twice, the agent stops, says what does not work and why,
and proposes a different route. A third attempt down the same path is not made. This
keeps a session from sliding into a series of patches over a wrong idea.

## Decisions are written down

Decisions that were taken, and the reasons for them, are recorded where the next session
will find them, together with the decisions that were considered and rejected. The agent
does not remember previous sessions; what is not written down is proposed again.

## Sessions hand over

Every working session ends by writing down the state of the work, the open issues and
the next step, short enough to be read at the start of the next session. A new session
starts from that note, not from a memory it does not have.

## Plain language

The specialist is the authority on the payroll and the final reader of every
explanation. Explanations are given in plain language, with technical terms explained
when they are needed, because a decision the specialist cannot follow is not a decision
the specialist made.
