# The Simmate Open Collective


### Summary


we must first ensure community workers are being honest and their calculations are accurate .

To make sure the worker doesn't provide falsified results, two checks are in place before any payout: 

1. First, Simmate uses certified, trusted members called "validators" who re-run ~5% of all jobs to verify the results are correct
2. Second, workers must put up a cash deposit ("collateral") that they lose if they are found to be dishonest. 

### Details


There are scenarios where workers can cheat the calculation for personal gain, and we want to prevent this from happening. For example, because Simmate workers can be started by anyone on any device, a malicious worker might change Simmate's source code to fabricate the results or even use a ML model to rapidly calculate what should have been done with DFT (and thus being dishonest on the workflow that was ran or the CPU time). We only want to move payment out of the Escrow Wallet once we trust the worker’s results.

So how do we ensure community workers are being honest? Intrusive software (i.e., the equivalent of anticheat software for gaming) is one option, but we want to keep our code 100% open-source and community friendly. We therefore opted to (1) repeat a % of calculations in order to validate them and (2) have workers provide collateral to deter misuse.

For (1), Simmate will randomly re-run ~5% of all calculations using a set of certified and well-trusted workers that we call "validators". Validators will select jobs that have already completed (or even failed!) and see if they get the same results within expected margins of error. Inconsistent results could lead to an investigation of the workers and/or their user. In many cases, issues could be an irregularity or unexpected bug, in which case the user who submitted the original workflow will be notified of the issue, refunded, and (if the issue was fixed) provided corrected results at no charge.

For (2), workers must send USD($) into a locked “worker-collatoral wallet” which they can later withdraw in full amount when the workers are taken offline. The required collateral amount is proportional to worker compute power and potential total earnings (e.g., $10 per CPU-core provided, though this value varies based on compute demand). In rare cases where an investigation from (1) concludes that a worker is misbehaving, the worker will lose their collateral permanently – and the funds are shared among validators.

So to summarize, funds can only be moved out of the escrow once validators confirm a portion of a worker's results. With this system in place, we can ensure results are accurate before finally paying workers for the compute time that they provided. Funds out of the escrow are then split in the following manner: 85% to the individual worker, 10% to the validator pool, and 5% to the Simmate Treasury wallet (more on this later).

    * note payment for a single calculation goes to the validator pool rather than directly to a single validator. This is because validators are only repeating 5% of all calculations, and there is no clear mechanism to pair a validator to each of the remaining 95% jobs. Instead, validator earnings are pooled in the “Community Validator Escrow” and then shared with individual validators proportionally to their provided compute power.
    
    Also note that validators make ~2x the $/CPU earnings vs workers because they receive 10% of the earnings but only did 5% cpu time (Exact calc: total funds / total compute → 10/(5/105) vs 85/(100/105) → 2.35x). And on top of this, validators receive funds from any penalized worker collateral (though this is so rare that it leads to negligible earnings for validators). This discrepancy is in place to incentivize workers to eventually become validators – as being a validator requires a higher standard and more work to set up. Since Simmate is in its early stages, 100% of validators are controlled by the Simmate team and close collaborators, but over time, we hope to allow community members to become validators through a "worker reputation" system. For example, workers that have a long track record of successful workflow runs can automatically become validators and access improved earnings. Until this system is ready, only those that reach out and collaborate directly with the Simmate team can become validators.
