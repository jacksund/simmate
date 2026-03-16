# Why use workers?

Up to this point, you've been running workflows directly on your computer. When you use the `run` command (or the `.run()` method in Python), Simmate starts the workflow immediately and waits for it to finish before letting you do anything else.

This is great for testing, but as your research scales, you'll want to submit **hundreds or thousands of jobs** and have them run in the background or on different computers. This is where **Workers** and **Clusters** come in.

---

## The Chef Analogy

A **Worker** is a background process that asks your database: *"Are there any jobs waiting to be run?"* If there are, the worker picks one up, runs it, and saves the result back to the database.

Think of it like a chef in a restaurant:

1. **You (The Waiter)**: You take an order (the workflow) and pin it to the "Order Board" (the database). You don't cook the meal yourself; you just record what needs to be done.
2. **The Database (The Order Board)**: This is the central list of everything that needs to be done. It keeps track of which orders are "Pending," which are "Cooking," and which are "Finished."
3. **The Worker (The Chef)**: The chef watches the board. As soon as an order appears, they pick it up, cook it (run the workflow), and put the finished plate on the counter (save the result to the database).

---

## Why this is powerful

By separating the "submission" from the "execution," you gain several advantages:

### 1. Asynchronous Execution
You can submit 100 jobs in a few seconds and then immediately go back to your research. You don't have to wait for Job 1 to finish before submitting Job 2.

### 2. Scalability
If one chef (worker) isn't fast enough, you can hire more! You can start 10 workers on your computer, or even 1,000 workers across a supercomputer. They all look at the same "Order Board" (database) and work together to clear the queue.

### 3. Resilience
If your computer crashes or you lose your internet connection, the "Order Board" (database) still has the record of what was finished and what still needs to be done. You can just restart your workers and they will pick up right where they left off.

### 4. Firewall Friendly
Most supercomputers (HPC clusters) have strict firewalls that block incoming connections. However, they almost always allow **outbound** connections to a database. Because Simmate workers "pull" work from the database rather than having work "pushed" to them, they can run almost anywhere.

---

## Ready to try it?
In the next section, we'll set up your first worker and submit a job to the queue.
