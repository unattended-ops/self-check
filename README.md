# self-check

**[Open the self-check →](https://unattended-ops.github.io/self-check/)**

30 questions across six axes, for teams trying to run something unattended.

One HTML file. No tracking, no storage, no network calls — it runs entirely in your browser and forgets everything when you close the tab.

## What it does

It does not score you against anyone. There is no benchmark here — the sample size is zero, and inventing one would be worse than leaving it blank.

What it does is pick **the one axis that breaks first** in your setup, and give you **one thing to do this week**.

## The six axes

| Axis | The question underneath |
|---|---|
| Memory | Sessions die, the org does not. What does the next one read first? |
| Overwrite | When the same value lives in two places, whichever is read first wins — and you do not control the order. |
| Output | Building and shipping are different columns. A week with nothing shipped is not a week that ran. |
| Stop | Turning things off is harder than turning them on. Automation you cannot stop is a liability, not an asset. |
| Leak | Every other failure can be fixed afterward. This one cannot. |
| Measurement | When it is wrong, what catches it besides a person? |

## Why "don't know" gets its own column

Most self-checks fold "don't know" into "no" and score it zero. That hides the difference between **a gap** and **something you have not measured yet**.

This one counts them separately, and splits the verdict in two:

- **The axis that breaks first** — counted from gaps only
- **The axis to measure first** — counted from unknowns only

An axis with three unknowns and zero gaps does not need fixing. It needs counting. Those are different weeks of work.

## Full marks are not full marks

If all 30 answers are yes, it refuses to name an axis. Instead it asks the only question left: **of those 30, how many are yes because you observed it, and how many because you remember it?**

The tool cannot tell those apart. You can.

## Where this came from

We are building an organization meant to run without a person in the loop. Every question here is a place we actually stopped.
