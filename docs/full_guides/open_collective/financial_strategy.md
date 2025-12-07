# Financial Strategy

## Summary

Simmate's open collective generates revenue from several sources:

- [x] Users pay for workflow runs
- [x] Grants fund specific projects and app development
- [x] Interest earned on internal funds
- [x] Instituitions & Labs pay for private server managment

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

------------------------------------------------------------

## Revenue Distribution

###  Simmate Treasury


The treasury is used to cover cloud costs as well as fund Simmate development and research. 
For example, Simmate’s database and archive of workflow results are constantly growing, so funding 
is needed to grow resources required to support them. Portions of the fund are also used for promotions
and incentives where needed (such as attracting more users, workers, validators, or developers).

- 5% from each workflow run
- 25% of accrued interest revenue


### Workers

- 85% from each workflow run
- 75% of interest accrued


### Validator Pool

Payment for a single calculation goes to the validator pool rather than directly to a single validator. 
This is because validators are only repeating 5% of all calculations, and there is no clear mechanism to 
pair a validator to each of the remaining 95% jobs. Instead, validator earnings are pooled in the “Community 
Validator Escrow” and then shared with individual validators proportionally to their provided compute power.

Note that validators make ~2x the $/CPU earnings vs workers because they receive 10% 
of the earnings but only did 5% cpu time (Exact calc: total funds / total compute → 10/(5/105) vs 85/(100/105) → 2.35x). 
And on top of this, validators receive funds from any penalized worker collateral (though this is so rare that it leads 
to negligible earnings for validators). This discrepancy is in place to incentivize workers to eventually become validators 
– as being a validator requires a higher standard and more work to set up. Since Simmate is in its early stages, 100% of 
validators are controlled by the Simmate team and close collaborators, but over time, we hope to allow community members to 
become validators through a "worker reputation" system. For example, workers that have a long track record of successful workflow 
runs can automatically become validators and access improved earnings. Until this system is ready, only those that reach out and 
collaborate directly with the Simmate team can become validators.
