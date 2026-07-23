# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature           | Method(s) | Notes                             |
| ----------------- | --------- | --------------------------------- |
| Task sorting      |           | e.g., by priority, duration       |
| Filtering         |           | e.g., skip tasks if time runs out |
| Conflict handling |           | e.g., overlapping time slots      |
| Recurring tasks   |           | e.g., daily vs. weekly            |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. The apps first asks the user for the owners name. This is to help the pets have a relationship with a specific owner.
2. After owner is added then we add the pet. The fields at that are required are pet name, age, color, and breed. After fields are field out then you add the pet to the owner. It will only add the pet if the pet is not in the system. The user then sees that the pet has been added to a table that shows the pets under that person.
3. The third step is to add the tasks associated with that pet. The owner adds the task, time of task and frequency. After the task has been added then a table will list the pet name with the task and time.
4. The next step the user gets to pick the owners name and then pick the pets name and it display the task time and frequency. If there is any time contrainst the display will show warning of this.
5. The final display on the app is the schedule itself. It shows the status of the task and all the information needed to see where the task stands.
   **Screenshot or video** _(optional)_: <!-- Insert a screenshot or link to a demo video here -->

**Sample Output**

````Today's schedule:
- 09:00 | Feed Toby breakfast (daily)
- 18:00 | Feed Toby dinner (daily)
- 12:30 | Walk Mittens (daily)```
````

**Testing PawPal+**
run python3 -m pytest

TestTimeToMinutes — the time parser (13 tests)
Converts "HH:MM" to minutes-since-midnight. Checks midnight/typical/end-of-day values, that single-digit 9:00 equals 09:00, and that garbage input raises ValueError (wrong shape like "0800", out-of-range like "24:00"/"08:60", non-numeric like "ab:cd").

TestTask — a single task (19 tests)
Defaults (starts incomplete, due today), frequency lowercased, time/frequency validated at construction. Big focus on recurrence (next_occurrence): daily/weekly advance by a fixed interval; monthly advances a calendar month — keeping day-of-month (15th→15th), clamping short months (Jan 31→Feb 28), leap day (Jan 31 2024→Feb 29), and year rollover (Dec→Jan). Also confirms the follow-up is a fresh, incomplete copy and advances from the task's own due date, not today.

TestPetInformation / TestOwner — the data model (6 tests)
Getters, add/remove pets and tasks, counts, and that an owner aggregates tasks across all its pets.

TestSchedulerFiltering — querying tasks (9 tests)
Filter by pet (object or case-insensitive name, unknown name → empty), by frequency (case-insensitive), completed vs. incomplete, combined filters, and lookup by clock time.

TestSchedulerSorting — ordering (10 tests)
The chronological guarantees: output is non-decreasing, 9:00 sorts before 10:00 (not as text), ties are stable, the input list isn't mutated, and ordering is date-then-time (a task due sooner comes first even if its clock time is later). Plus getScheduleForDay mapping today→daily.

TestSchedulerConflicts — collision detection (8 tests)
No conflict when times differ; flags same-pet and cross-pet clashes; a 3-way collision reports all tasks but distinct pets; same time on different dates is not a conflict; conflicts come back chronologically; human-readable warnings; and conflict_warnings never raises even if detection blows up.

=================================================================== test session starts ====================================================================
platform darwin -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/liz/pawpalProject/ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 75 items

tests/test_pawpal.py ........................................................................... [100%]

==================================================================== 75 passed in 0.25s ====================================================================

**Confidence Level**
I am really confident that the test passed all test edge cases for a working app. 5 star confindence.

**Features**
Chronological sorting — sort_by_time() orders tasks by (due_date, minutes-since-midnight). Times are compared numerically via timeToMinutes(), so 9:00 correctly precedes 10:00 (not sorted as text), and multi-day lists stay in true calendar order. The input list is never mutated.

Multi-criteria filtering — filter_tasks() filters by any combination of pet (object or case-insensitive name), completion status, and frequency. Each criterion is optional; unknown pet names return an empty list. Convenience wrappers: getTasksByFrequency, getTasksByTime, getCompletedTasks, getIncompleteTasks.

Conflict detection — detectConflicts() buckets tasks by (date, time) slot and flags any slot with 2+ tasks. Distinguishes same-pet overlaps from cross-pet clashes (same_pet flag), reports all colliding tasks and the distinct pets involved, and returns results chronologically. Two daily tasks at 09:00 on different days are not flagged.

Human-readable conflict warnings — conflict_warnings() turns conflicts into UI-ready messages and is crash-safe: any unexpected error is caught and returned as a warning string rather than raising. has_conflicts() gives a safe boolean.

Recurrence / next occurrence — next_occurrence() generates a fresh incomplete copy advanced by one interval:

Daily / weekly advance by a fixed timedelta.
Monthly advances by one calendar month via add_one_month(), keeping the day-of-month (15th → 15th), clamping short months (Jan 31 → Feb 28, or Feb 29 in a leap year), and rolling over the year (Dec → Jan).
Advances from the task's own due date, not today, so completing late still lands the next task on the correct slot.
Auto-rescheduling on completion — markTaskComplete() marks a task done and auto-attaches its next occurrence to the same pet. Guards against duplicates (won't re-complete an already-done task) and against orphaned follow-ups (returns None if the task belongs to no owned pet).

Daily-plan generation — getScheduleForDay() maps today/daily to daily tasks (and weekly/monthly to their recurrences), then returns them time-sorted so the plan reads in do-order.

Task aggregation across pets — Owner.getAllTasks() collects tasks from every pet so the Scheduler operates over the owner's whole roster.

Input validation — timeToMinutes() enforces HH:MM (accepting single-digit hours), and Task.**init** validates time and normalizes frequency to lowercase against VALID_FREQUENCIES, raising ValueError on bad input.
