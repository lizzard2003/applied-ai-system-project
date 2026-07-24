# #mport classes from pawpal_system
from pawpal_system import Owner, Scheduler, PetInformation, Task

owner = Owner("John Doe")

pet1 = PetInformation("Toby", 3, "Australian Shepherd", "black and white")
pet2 = PetInformation("Mittens", 2, "Tortoiseshell", "multicolor")

owner.addPet(pet1)
owner.addPet(pet2)

# Add tasks OUT OF ORDER (dinner before breakfast) to prove sorting works.
dinner_task = Task("Feed Toby dinner", "18:00", "daily")
breakfast_task = Task("Feed Toby breakfast", "09:00", "daily")
walk_task = Task("Walk Mittens", "12:30", "daily")
vet_task = Task("Vet checkup for Toby", "09:00", "monthly")

mittens_breakfast = Task("Feed Mittens breakfast", "09:00", "daily")

pet1.addTask(dinner_task)      # 18:00
pet1.addTask(breakfast_task)   # 09:00 — added after dinner on purpose
pet2.addTask(walk_task)        # 12:30
pet1.addTask(vet_task)         # 09:00, monthly (same-pet clash with breakfast)
pet2.addTask(mittens_breakfast)  # 09:00 — cross-pet clash (Toby vs Mittens)

scheduler = Scheduler(owner)


def show(title, tasks):
    """Print a titled list of tasks in a consistent format."""
    print(f"\n{title}")
    if not tasks:
        print("  (none)")
    for task in tasks:
        status = "done" if task.getCompletionStatus() else "todo"
        print(f"  - {task.getDueDate()} {task.time} | {task.description} "
              f"({task.frequency}) [{status}]")


# Mark one task done so the status filters have something to show. Completing a
# daily task auto-creates its next occurrence, due one day later.
scheduler.markTaskComplete(breakfast_task)

# 1. Sorting: tasks were added out of order; sort_by_time puts them right.
show("All tasks, sorted by time:", scheduler.sort_by_time())

# 2. Filtering by pet name (case-insensitive).
show("Toby's tasks:", scheduler.filter_tasks(pet_name="toby"))

# 3. Filtering by completion status.
show("Completed tasks:", scheduler.filter_tasks(completed=True))
show("Outstanding tasks:", scheduler.filter_tasks(completed=False))

# 4. Combined filter + sort: Toby's outstanding tasks in time order.
toby_todo = scheduler.filter_tasks(pet_name="Toby", completed=False)
show("Toby's outstanding tasks, sorted:", scheduler.sort_by_time(toby_todo))

# 5. Today's daily schedule (already sorted by getScheduleForDay).
show("Today's daily schedule:", scheduler.getScheduleForDay("today"))

# 6. Conflict detection: 'Feed Toby breakfast' and 'Vet checkup for Toby' are
#    BOTH scheduled at 09:00, so the Scheduler should warn about the clash.
print("\nSchedule conflicts:")
warnings = scheduler.conflict_warnings()
if not warnings:
    print("  No conflicts — schedule looks clear.")
for warning in warnings:
    print(f"  {warning}")

# Verify the two 09:00 tasks were correctly identified as a conflict.
print("\nVerification:")
if scheduler.has_conflicts() and any("09:00" in w for w in warnings):
    print("  PASS - Scheduler detected the two tasks scheduled at 09:00.")
else:
    print("  FAIL - conflict at 09:00 was not detected.")

# 7. Recurrence: completing the daily walk creates the next day's instance,
#    while a monthly task does not auto-recur.
print("\nRecurrence after completing tasks:")
new_walk = scheduler.markTaskComplete(walk_task)
print(f"  Walk was due {walk_task.getDueDate()}; "
      f"next instance due {new_walk.getDueDate()}")
new_vet = scheduler.markTaskComplete(vet_task)
print(f"  Vet checkup (monthly) auto-recurred? {new_vet is not None}")
