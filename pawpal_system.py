import calendar
from datetime import date, timedelta

VALID_FREQUENCIES = ("daily", "weekly", "monthly")
# Fixed-length steps between occurrences, for frequencies that map cleanly onto
# a timedelta. 'monthly' is NOT here: a calendar month is not a fixed number of
# days, so it advances via add_one_month() instead.
RECURRENCE_DELTAS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
}

# Named priority levels mapped to numeric weights. A higher weight means the
# task is more important and should bubble to the top of a prioritized plan.
# Keeping the levels named (not raw numbers) keeps tasks readable while still
# giving the scheduler a number to sort on. 'medium' is the default.
PRIORITY_WEIGHTS = {
    "low": 1,
    "medium": 2,
    "high": 3,
}
DEFAULT_PRIORITY = "medium"

# Local "knowledge base" of breed care notes. In the RAG diagram this is the
# Knowledge Base box; here it's a plain dict so the lookup needs no API or
# network. Keys are lowercased breeds so lookups are case-insensitive.
PET_KNOWLEDGE_BASE = {
    "australian shepherd": "Energetic, highly intelligent herding dog. Needs "
        "1-2 hours of vigorous exercise plus mental stimulation every day.",
    "tortoiseshell": "Spirited, often independent cat ('tortitude'). Enjoys "
        "daily play; keep fresh water out and groom regularly.",
    "tabby": "Friendly, adaptable, and social cat. Thrives on daily play and "
        "a steady feeding routine.",
    "labrador retriever": "Outgoing, food-motivated family dog. Needs plenty of "
        "exercise and watch its weight, as the breed gains easily.",
    "siamese": "Vocal, affectionate, people-oriented cat. Wants lots of "
        "interaction and can get lonely if left alone too long.",
}


def getPetInformation(breed: str) -> str:
    """Return care info for a breed.

    Gives the specific note when the breed is in the knowledge base, and a
    generalized answer otherwise, matching the RAG diagram's fallback behavior.
    """
    if breed:
        specific = PET_KNOWLEDGE_BASE.get(breed.strip().lower())
        if specific:
            return specific
    return ("No specific notes for this breed yet. In general: provide fresh "
            "water and daily feeding, regular exercise or play, routine vet "
            "checkups, and grooming suited to the coat.")


def add_one_month(day: date) -> date:
    """Return the date one calendar month after `day`, keeping the day-of-month.

    Advances to the same day in the next month rather than by a fixed number of
    days, so a monthly routine stays anchored to its date (the 15th stays the
    15th). When the target month is shorter, the day is clamped to that month's
    last valid day, so Jan 31 -> Feb 28 (or Feb 29 in a leap year) instead of
    overflowing into March.
    """
    month = day.month + 1
    year = day.year
    if month > 12:
        month = 1
        year += 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))


def timeToMinutes(time: str) -> int:
    """Convert an 'HH:MM' (24-hour) time string into minutes since midnight.

    Accepts single-digit hours too, so '9:00' and '09:00' are treated the same.
    Raises ValueError if the string is not a valid time.
    """
    parts = time.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time '{time}': expected 'HH:MM'.")
    hours, minutes = int(parts[0]), int(parts[1])
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError(f"Invalid time '{time}': hours 0-23 and minutes 0-59.")
    return hours * 60 + minutes


class Owner:
    name: str
    pets: list  # List of PetInformation objects

    def __init__(self, name: str):
        """Initialize owner with a name and empty pet list."""
        self.name = name
        self.pets = []

    def getOwnerName(self) -> str:
        """Return the owner's name."""
        return self.name

    def addPet(self, pet: 'PetInformation') -> None:
        """Add a pet to the owner's collection."""
        self.pets.append(pet)

    def removePet(self, pet: 'PetInformation') -> None:
        """Remove a pet from the owner's collection."""
        self.pets.remove(pet)

    def getPets(self) -> list:
        """Return the list of pets owned by this owner."""
        return self.pets

    def getPetCount(self) -> int:
        """Return the number of pets the owner has."""
        return len(self.pets)

    def getAllTasks(self) -> list:
        """Collect and return all tasks from every pet."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.getTasks())
        return tasks

    def getTotalTaskCount(self) -> int:
        """Return the total number of tasks across all pets."""
        return len(self.getAllTasks())


class Scheduler:
    owner: 'Owner'

    def __init__(self, owner: 'Owner'):
        """Initialize the scheduler with an owner."""
        self.owner = owner

    def getAllTasks(self) -> list:
        """Return all tasks belonging to the owner."""
        return self.owner.getAllTasks()

    def filter_tasks(self, pet: 'PetInformation' = None, pet_name: str = None,
                     completed: bool = None, frequency: str = None,
                     priority: str = None) -> list:
        """Return tasks filtered by any combination of the given criteria.

        Every argument is optional; passing None means "don't filter on this".
        - pet:        only tasks belonging to this pet object
        - pet_name:   only tasks belonging to the pet with this name (case-insensitive)
        - completed:  True for done tasks, False for outstanding ones
        - frequency:  only tasks with this frequency (case-insensitive)
        - priority:   only tasks at this priority level (case-insensitive)

        Pass either `pet` or `pet_name` to filter by pet, not both. Filtering by a
        `pet_name` that no pet matches returns an empty list.
        """
        if pet is not None:
            tasks = pet.getTasks()
        elif pet_name is not None:
            name = pet_name.lower()
            tasks = []
            for owned_pet in self.owner.getPets():
                if owned_pet.getPetName().lower() == name:
                    tasks.extend(owned_pet.getTasks())
        else:
            tasks = self.getAllTasks()

        if completed is not None:
            tasks = [t for t in tasks if t.completion_status == completed]
        if frequency is not None:
            freq = frequency.lower()
            tasks = [t for t in tasks if t.frequency == freq]
        if priority is not None:
            prio = priority.lower()
            tasks = [t for t in tasks if t.priority == prio]
        return tasks

    def getTasksByFrequency(self, frequency: str) -> list:
        """Return tasks matching a specific frequency."""
        return self.filter_tasks(frequency=frequency)

    def getTasksByTime(self, time: str) -> list:
        """Return tasks scheduled at a given time (matched by clock minute)."""
        target = timeToMinutes(time)
        return [t for t in self.getAllTasks() if timeToMinutes(t.time) == target]

    def getTasksByPet(self, pet: 'PetInformation') -> list:
        """Return all tasks for a single pet."""
        return self.filter_tasks(pet=pet)

    def getTasksByPriority(self, priority: str) -> list:
        """Return tasks at a given priority level (case-insensitive)."""
        return self.filter_tasks(priority=priority)

    def getCompletedTasks(self) -> list:
        """Return tasks that have been completed."""
        return self.filter_tasks(completed=True)

    def getIncompleteTasks(self) -> list:
        """Return tasks that are not yet complete."""
        return self.filter_tasks(completed=False)

    def sort_by_time(self, tasks: list = None) -> list:
        """Return tasks ordered chronologically, earliest first.

        Sorts the given task list, or all of the owner's tasks when none is passed.
        Ordering is by (due date, minutes-since-midnight): tasks due sooner come
        first, and within the same date the earlier clock time wins — so '9:00'
        correctly precedes '10:00' instead of sorting as plain text. Sorting on the
        date as well as the time keeps a multi-day list in true calendar order.
        """
        if tasks is None:
            tasks = self.getAllTasks()
        return sorted(tasks, key=lambda task: (task.due_date, timeToMinutes(task.time)))

    def sort_by_priority(self, tasks: list = None) -> list:
        """Return tasks ordered by priority weight, most important first.

        Sorts the given task list, or all of the owner's tasks when none is
        passed. The primary key is the numeric priority weight in DESCENDING
        order (high > medium > low), so the tasks that matter most surface at the
        top of the plan. Ties are broken chronologically — by (due date,
        minutes-since-midnight) — so within one priority level the schedule still
        reads in the order the owner will actually do it. The input list is not
        mutated.
        """
        if tasks is None:
            tasks = self.getAllTasks()
        return sorted(
            tasks,
            key=lambda task: (
                -task.getPriorityWeight(),
                task.due_date,
                timeToMinutes(task.time),
            ),
        )

    def getPrioritizedSchedule(self, day: str) -> list:
        """Return a given day's plan ordered by priority, then by time.

        Combines the recurrence mapping of getScheduleForDay() with the priority
        ordering of sort_by_priority(): 'today'/'daily' select the daily tasks,
        'weekly'/'monthly' select those recurrences, and the result is ranked so
        the highest-priority tasks come first (ties broken chronologically).
        """
        frequency = "daily" if day.lower() in ("today", "daily") else day.lower()
        return self.sort_by_priority(self.filter_tasks(frequency=frequency))

    def detectConflicts(self) -> list:
        """Find tasks that collide on the same date and clock time.

        Two tasks conflict when they fall on the same due date AND the same time,
        whether they belong to the same pet or different pets. Grouping on the date
        as well as the time means two daily tasks at 09:00 on different days are
        NOT flagged.

        Returns a list of conflict dicts, ordered chronologically, each with:
        - date:     the shared due date
        - time:     the shared 'HH:MM' time
        - tasks:    the list of colliding Task objects (two or more)
        - pets:     the distinct pet names involved, in first-seen order
        - same_pet: True if every colliding task belongs to one pet, else False
                    (False means a cross-pet clash the owner must be two places for)

        An empty list means no conflicts.
        """
        slots: dict = {}
        for pet in self.owner.getPets():
            for task in pet.getTasks():
                key = (task.due_date, timeToMinutes(task.time))
                slots.setdefault(key, []).append((pet, task))

        conflicts = []
        for (due_date, minutes), pairs in slots.items():
            if len(pairs) < 2:
                continue
            pet_names = []
            for pet, _ in pairs:
                if pet.getPetName() not in pet_names:
                    pet_names.append(pet.getPetName())
            conflicts.append({
                "date": due_date,
                "time": pairs[0][1].time,
                "tasks": [task for _, task in pairs],
                "pets": pet_names,
                "same_pet": len(pet_names) == 1,
            })

        conflicts.sort(key=lambda c: (c["date"], timeToMinutes(c["time"])))
        return conflicts

    def conflict_warnings(self) -> list:
        """Lightweight conflict check: return human-readable warnings, never raise.

        Turns each conflict from detectConflicts() into a short message a UI or the
        terminal can show. This is the "safe" entry point: any unexpected error
        (e.g. a malformed task) is caught and reported as a single warning string
        instead of crashing the program. An empty list means no conflicts found.
        """
        try:
            conflicts = self.detectConflicts()
        except Exception as error:  # stay lightweight: warn, don't crash
            return [f"Could not check for conflicts: {error}"]

        warnings = []
        for conflict in conflicts:
            descriptions = ", ".join(t.description for t in conflict["tasks"])
            if conflict["same_pet"]:
                scope = f"{conflict['pets'][0]} has overlapping tasks"
            else:
                scope = f"{' & '.join(conflict['pets'])} need you at the same time"
            warnings.append(
                f"⚠️ Conflict on {conflict['date']} at {conflict['time']}: "
                f"{scope} ({descriptions})."
            )
        return warnings

    def has_conflicts(self) -> bool:
        """Return True if any scheduling conflict exists (safe, never raises)."""
        return len(self.conflict_warnings()) > 0

    def sortTasksByFrequency(self) -> list:
        """Return tasks sorted by frequency."""
        return sorted(self.getAllTasks(), key=lambda task: task.frequency)

    def _find_owning_pet(self, task: 'Task') -> 'PetInformation':
        """Return the pet whose task list contains this task, or None."""
        for pet in self.owner.getPets():
            if task in pet.getTasks():
                return pet
        return None

    def markTaskComplete(self, task: 'Task') -> 'Task':
        """Mark a task complete and auto-schedule its next occurrence.

        For recurring daily/weekly/monthly tasks, a fresh incomplete copy is added
        to the same pet so the routine keeps going. Returns the newly created
        follow-up Task, or None when nothing is scheduled: the task's frequency
        does not recur, the task was already complete (so completing twice won't
        create duplicates), or the task belongs to none of this owner's pets. In
        that last case the task is left untouched rather than silently completed,
        since a follow-up would have no pet to attach to.
        """
        if task.completion_status:
            return None
        pet = self._find_owning_pet(task)
        if pet is None:
            return None
        task.markComplete()
        follow_up = task.next_occurrence()
        if follow_up is not None:
            pet.addTask(follow_up)
        return follow_up

    def resetAllTasks(self) -> None:
        """Reset completion status for all tasks."""
        for task in self.getAllTasks():
            task.resetTask()

    def getScheduleForDay(self, day: str) -> list:
        """Return the chronologically ordered schedule for a given frequency.

        'today' and 'daily' both map to the recurring daily tasks; 'weekly' and
        'monthly' return tasks with that recurrence. Results are sorted by time so
        the plan reads in the order the owner will actually do it.
        """
        frequency = "daily" if day.lower() in ("today", "daily") else day.lower()
        return self.sort_by_time(self.filter_tasks(frequency=frequency))


class Task:
    description: str
    time: str
    frequency: str
    completion_status: bool
    due_date: date
    priority: str

    def __init__(self, description: str, time: str, frequency: str,
                 due_date: date = None, priority: str = DEFAULT_PRIORITY):
        """Initialize task details and set completion status false.

        Validates the time format and normalizes frequency to lowercase so that
        sorting, filtering, and recurrence checks stay consistent. `due_date`
        defaults to today when not given, so existing three-argument calls keep
        working. `priority` is a named level ('low'/'medium'/'high', case-
        insensitive) backed by a numeric weight; it defaults to 'medium' so
        older calls that omit it keep working.
        """
        timeToMinutes(time)  # raises ValueError on a malformed time
        frequency = frequency.lower()
        if frequency not in VALID_FREQUENCIES:
            raise ValueError(
                f"Invalid frequency '{frequency}': expected one of {VALID_FREQUENCIES}."
            )
        priority = priority.lower()
        if priority not in PRIORITY_WEIGHTS:
            raise ValueError(
                f"Invalid priority '{priority}': expected one of "
                f"{tuple(PRIORITY_WEIGHTS)}."
            )
        self.description = description
        self.time = time
        self.frequency = frequency
        self.completion_status = False
        self.due_date = due_date if due_date is not None else date.today()
        self.priority = priority

    def getTimeInMinutes(self) -> int:
        """Return the task's time as minutes since midnight (handy for sorting)."""
        return timeToMinutes(self.time)

    def getDueDate(self) -> date:
        """Return the date this task is due."""
        return self.due_date

    def next_occurrence(self) -> 'Task':
        """Return a fresh, incomplete Task for this task's next occurrence.

        Daily, weekly, and monthly tasks recur, so a new copy is returned with its
        due date advanced by one interval. Daily/weekly advance by a fixed
        timedelta; monthly advances by one calendar month (same day-of-month,
        clamped for short months) via add_one_month(). The date advances from this
        task's own due date, not from today, so completing a task late still lands
        the next one on the right slot. The follow-up keeps the same priority. A
        frequency that does not recur returns None.
        """
        if self.frequency == "monthly":
            next_due = add_one_month(self.due_date)
        else:
            delta = RECURRENCE_DELTAS.get(self.frequency)
            if delta is None:
                return None
            next_due = self.due_date + delta
        return Task(self.description, self.time, self.frequency,
                    due_date=next_due, priority=self.priority)

    def getDescription(self) -> str:
        """Return the task description."""
        return self.description

    def getTime(self) -> str:
        """Return the task time."""
        return self.time

    def getFrequency(self) -> str:
        """Return the task frequency."""
        return self.frequency

    def getPriority(self) -> str:
        """Return the task's named priority level ('low'/'medium'/'high')."""
        return self.priority

    def getPriorityWeight(self) -> int:
        """Return the task's numeric priority weight (higher = more important)."""
        return PRIORITY_WEIGHTS[self.priority]

    def getCompletionStatus(self) -> bool:
        """Return whether the task is completed."""
        return self.completion_status

    def markComplete(self) -> None:
        """Mark the task as completed."""
        self.completion_status = True

    def mark_complete(self) -> None:
        """Alias to mark the task as complete."""
        self.markComplete()

    def resetTask(self) -> None:
        """Reset the task to incomplete."""
        self.completion_status = False


class PetInformation:
    name: str
    age: int
    breed: str
    color: str
    tasks: list  # List of Task objects

    def __init__(self, name: str, age: int, breed: str, color: str):
        """Initialize pet details and empty task list."""
        self.name = name
        self.age = age
        self.breed = breed
        self.color = color
        self.tasks = []

    def getPetName(self) -> str:
        """Return the pet's name."""
        return self.name

    def getAge(self) -> int:
        """Return the pet's age."""
        return self.age

    def getBreed(self) -> str:
        """Return the pet's breed."""
        return self.breed

    def getColor(self) -> str:
        """Return the pet's color."""
        return self.color

    def getGeneralInfo(self) -> str:
        """Return care info for this pet's breed (specific or generalized)."""
        return getPetInformation(self.breed)

    def addTask(self, task: 'Task') -> None:
        """Add a task to the pet."""
        self.tasks.append(task)

    def removeTask(self, task: 'Task') -> None:
        """Remove a task from the pet."""
        self.tasks.remove(task)

    def getTasks(self) -> list:
        """Return the pet's task list."""
        return self.tasks

    def getTaskCount(self) -> int:
        """Return how many tasks the pet has."""
        return len(self.tasks)


class PetTasks:
    timeConstraint: 'TimeConstraint'

    def __init__(self, timeConstraint: 'TimeConstraint'):
        ...

    def feedPet(self) -> str:
        ...

    def walkPet(self) -> str:
        ...

    def petSit(self) -> str:
        ...


class TimeConstraint:
    taskDuration: int
    availability: int
    repetition: str

    def __init__(self, taskDuration: int, availability: int, repetition: str):
        ...

    def getTaskDuration(self) -> int:
        ...

    def getAvailability(self) -> int:
        ...

    def getRepetition(self) -> str:
        ...
