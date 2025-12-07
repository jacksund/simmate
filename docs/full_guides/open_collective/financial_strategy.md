# Financial Strategy

## Summary

Simmate's open collective generates revenue from several sources:

- [x] Users pay for workflow runs
- [x] Grants fund specific projects and app development
- [x] Interest earned on internal funds
- [x] Instituitions & Labs pay for private server managment
- [x] Penalized Collatoral (rare and negligible) 

Each source's revenue is distributed differently, but collectively, all revenue
is paid out to the following entities:

- [x] Community Compute Providers (Workers & Validators)
- [x] Simmate Treasury


------------------------------------------------------------

## Revenue Sources

### Workflow Runs

When a user pays for a workflow, 100% of that payment goes into the "Simmate Escrow Wallet", 
which is a staging area for the funds until the workflow completes successfully and is confirmed
for accuracy. A community "worker" will then pick up and run the workflow. 
If the workflow fails, funds are returned to the original user, and if the workflow succeeds, 
the user can immediately see the results. The results will then undergo a review process to ensure workers 
are behaving accuractely and honestly (see our page on [Data Integrity Safegaurds](#)). And after 
passing integrity checks, the money can be released from the escrow holding account and split: 

- 85% goes to the worker
- 10% goes to the validators
- 5% goes to the Simmate Treasury

![Image title](workflow_payments_diagram.jpg){ align=center }

### Grants 

The Simmate team and collaborators apply for grants to help support development and research. 
But not all grants are publically disclosed to Simmate's open collective -- because grants may
be individual funding (e.g., [NSF-GFRP](https://www.nsfgrfp.org/) for 
student research) or compute funding for a specific research topic (which enters Simmate as 
user-submitted workflows).
Meanwhile, grants that directly support Simmate infrastructure are publically disclosed. This includes
grants that support cloud costs and core development (developer salaries). These funds are
added to the Simmate Treasury and appear in the [ledger](#).


### Accrued Interest 

There are many funds that sit within the Simmate ecosystem that must be physically 
backed within a bank account or on the blockchain. The source of these funds 
include:

- user balances
- collateral provided by workers & validators
- worker & validator payouts (before withdrawal)
- Simmate Treasury Balance

While Simmate's ledger of all individual wallets are maintained within [our database](#),
the backed funds all sit in two places:

1. the original [`simmate.eth`](#) Ethereum Wallet as USDC
2. a private Fidelity account as [SPAXX](https://fundresearch.fidelity.com/mutual-funds/summary/31617H102)

Interest rates vary for each but, generally, the rates both follow US government bond rates. Specifically, funds
are primarily backed by short-term U.S. Treasury Bills, so interest rates are typically in the range of **3-5%**.

The accrued 3-5% interest earned is paid out monthy:

- 75% goes to workers and validators to serve as a bonus/incentive
- 25% goes into the Simmate treasury

### Private Servers

On our pricing page, you can see that there is an option to host Simmate privately
and have our team manage it. This is the primary route that we
pay for developer salaries (as opposed to pulling from the Simmate Treasury).

We consider this to be private consulting that is separate from the Simmate collective
and public website. For this reason, all earnings here are kept separate from
the open collective accounts and ledger.

Ideally, this revenue stream is sufficient to cover 100% of developer salaries, 
but if that is not the case, the Simmate Treasury is used to supplement pay (and those
supplementary payments are public accessible).

### Penalized Collatoral

Workers and validators provide collateral to discourage them from providing any 
malicious or dishonest workflow results (see our page on [Data Integrity Safegaurds](#)).
If a worker or validator is found to acting dishonestly, their collatoral is penalized
and transferred to validator pool.

Note, this is a very rare occurance that collatoral is penalized. In fact, we have
never had to issue any penalities to worker and validator collatoral -- all issues 
so far have been honest mistakes or technical errors. We still include this
in our list of "revenue" sources for completeness & for those that wish to
know where funds would move if this were ever to occur.

------------------------------------------------------------

## Revenue Distribution

###  Simmate Treasury

The treasury fund is managed directly by the Simmate team, and because it is central to
the health & longevity of the entire open collective, all treasury transactions are
publically available in the ledger [here](#), and we provide quartly reports [here](#).

In the ledger, you can see that treasury is funded through several sources:

- 5% from each workflow run
- 25% of accrued interest revenue
- grants

And these funds are used to collectively cover...

- cloud infrastructure costs
- insurance (refunds, bug bounties, & emergency funds)
- research (Simmate-sponsered grants)
- promotions & incentives
- developer salaries (when Private Server revenue is insufficient)

The largest expense here is cloud infrastructure. For example, Simmate’s 
database and archive of workflow results are constantly growing, so funding 
is needed to grow resources required to support them. This involves storing and
serving many TB of data as well as maintaining backups. There are also the Simmate
webservers and services that require funds.

We aim to avoid using treasury funds for developement (specifically developer salaries),
and instead, fund development through our support of Private Servers (see above).

And if there is ever a surplus of funds in the treasury, our team explorers ways to
help grow the ecosystem, such as through new developer, funding research, or creating
promotions. For example, we can use small portions of the fund as incentives where needed 
(such as attracting more users, workers, validators, or developers).


### Workers

Workers are the ones that actually run workflows submitted by users. They provide
the CPU/GPU compute required, and they therefore get the majority of the payment
from users. Their full sources of revenue are the following:

- 85% from each workflow run
- 75% of interest accrued

See the "Workflow Runs" section above to understand where the other 15% of funds 
from workflow runs go.

While earnings from all validators are pooled (see below), workers are only paid
for the individual workflows that they actually ran. If you ran the workflow,
you get the results - no need to share with other workers. This is because there
are different types of workfers and resource requirements (not all CPU time is equal 
- some calcs require a more powerful setup with many cores + more RAM).

Because workers are only paid for what they run and anyone can be set up a worker,
there exist times when demand for compute heavily outweighs supply -- i.e., we
have more workers on standby than what is needed by user submissions. For this
reason, worker revenue is highly variable, and workers can get 'unlucky' by not
being selected to execute workflows (i.e., another worker picks up the job before them).
This is an unavoidable consequence, but Simmate aims to keep job distribution
fair by rate-limiting job pickup calls and randomly assigning workloads.

Payouts are made for each workflow as soon as a validator confirms the results.


### Validator Pool

Validators confirm that the results from Workers are accurate and honest by re-running 
5% of all workflows (see our page on [Data Integrity Safegaurds](#)).
Because they are providing compute power just like Workers, Validators earn revenue 
through the same sources (though in different ratios):

- 10% from *all* workflow runs (even though only 5% are actually repeated)
- 75% of interest accrued
- 100% penalized collatoral of other compute

Note that validators make ~2x the $/CPU earnings vs workers because they receive 10% 
of the earnings but only did 5% cpu time (Exact calc: total funds / total compute → 10/(5/105) vs 85/(100/105) → 2.35x). 
And on top of this, validators receive funds from any penalized worker collateral (though this is so rare that it leads 
to negligible earnings for validators). This discrepancy is in place to incentivize workers to eventually become validators 
– as being a validator requires meeting a higher standard and providing more collateral. 

!!! note
    Since Simmate is in its early stages, 100% of validators are controlled by the Simmate team and close collaborators, 
    but over time, we hope to allow community members to 
    become validators through a "worker reputation" system. For example, workers that have a long track record of successful workflow 
    runs can automatically become validators and access improved earnings. Until this system is ready, only those that reach out and 
    collaborate directly with the Simmate team can become validators.

While a worker is paid only for each workflow that they ran themelves, validators
are paid through a pool that is shared. Specifically, the 10% cut of a single calculation 
goes to the validator pool rather than directly to a single validator. We do this
for several reasons: 

- validators only repeat 5% of all calculations, and we need a mechanism on how to distribute revenue from each of the remaining 95% of jobs
- revenue becomes much more predictable when pooled, which is desirable when you're providing compute
- it allows us to evenly distribute penalized collatoral to those that help identify bad actors

Thus, validator earnings are pooled in the "Validator Escrow Pool" and then shared 
with individual validators proportionally to their provided compute power. Payouts
are done on a monthly basis.
