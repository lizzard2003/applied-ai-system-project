"""Comprehensive tests for the PawPal scheduling system.

Organized by unit: the timeToMinutes helper, then each class
(Task, PetInformation, Owner, Scheduler), then integration-style
scenarios that exercise several pieces together.
"""

from datetime import date, timedelta

import pytest

from pawpal_system import (
    Owner,
    PetInformation,
    Scheduler,
    Task,
    timeToMinutes,
)


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def make_pet_with_tasks(name="Rex", tasks=None):
    """Build a PetInformation with the given Task objects already attached."""
    pet = PetInformation(name, age=3, breed="Lab", color="black")
    for task in tasks or []:
        pet.addTask(task)
    return pet


# --------------------------------------------------------------------------- #
# timeToMinutes                                                                #
# --------------------------------------------------------------------------- #

class TestTimeToMinutes:
    def test_midnight_is_zero(self):
        assert timeToMinutes("00:00") == 0

    def test_typical_time(self):
        assert timeToMinutes("08:30") == 8 * 60 + 30

    def test_end_of_day(self):
        assert timeToMinutes("23:59") == 23 * 60 + 59

    def test_single_digit_hour_matches_padded(self):
        assert timeToMinutes("9:00") == timeToMinutes("09:00")

    @pytest.mark.parametrize("bad", ["", "8", "8:00:00", "0800"])
    def test_wrong_number_of_parts_raises(self, bad):
        with pytest.raises(ValueError):
            timeToMinutes(bad)

    @pytest.mark.parametrize("bad", ["24:00", "08:60", "-1:00", "12:99"])
    def test_out_of_range_raises(self, bad):
        with pytest.raises(ValueError):
            timeToMinutes(bad)

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            timeToMinutes("ab:cd")


# --------------------------------------------------------------------------- #
# Task                                                                         #
# --------------------------------------------------------------------------- #

class TestTask:
    def test_defaults(self):
        task = Task("Feed dog", "08:00", "daily")
        assert task.getDescription() == "Feed dog"
        assert task.getTime() == "08:00"
        assert task.getFrequency() == "daily"
        assert task.getCompletionStatus() is False
        assert task.getDueDate() == date.today()

    def test_frequency_normalized_to_lowercase(self):
        assert Task("x", "08:00", "DAILY").getFrequency() == "daily"
        assert Task("x", "08:00", "Weekly").getFrequency() == "weekly"

    def test_explicit_due_date_is_kept(self):
        due = date(2026, 1, 15)
        assert Task("x", "08:00", "daily", due_date=due).getDueDate() == due

    def test_invalid_time_rejected_at_construction(self):
        with pytest.raises(ValueError):
            Task("x", "99:99", "daily")

    def test_invalid_frequency_rejected(self):
        with pytest.raises(ValueError):
            Task("x", "08:00", "hourly")

    def test_get_time_in_minutes(self):
        assert Task("x", "01:30", "daily").getTimeInMinutes() == 90

    def test_mark_complete_and_reset(self):
        task = Task("x", "08:00", "daily")
        task.markComplete()
        assert task.getCompletionStatus() is True
        task.resetTask()
        assert task.getCompletionStatus() is False

    def test_mark_complete_alias(self):
        task = Task("x", "08:00", "daily")
        task.mark_complete()
        assert task.getCompletionStatus() is True

    @pytest.mark.parametrize(
        "frequency,delta",
        [
            ("daily", timedelta(days=1)),
            ("weekly", timedelta(weeks=1)),
        ],
    )
    def test_next_occurrence_advances_fixed_interval(self, frequency, delta):
        due = date(2026, 1, 1)
        task = Task("x", "08:00", frequency, due_date=due)
        follow_up = task.next_occurrence()
        assert follow_up is not None
        assert follow_up.getDueDate() == due + delta

    def test_next_occurrence_monthly_advances_one_calendar_month(self):
        # A calendar month, not a fixed 30 days: Jan 1 -> Feb 1, keeping the day.
        task = Task("x", "08:00", "monthly", due_date=date(2026, 1, 1))
        assert task.next_occurrence().getDueDate() == date(2026, 2, 1)

    def test_next_occurrence_monthly_keeps_day_of_month(self):
        # The 15th stays the 15th across a month boundary.
        task = Task("x", "08:00", "monthly", due_date=date(2026, 1, 15))
        assert task.next_occurrence().getDueDate() == date(2026, 2, 15)

    def test_next_occurrence_monthly_clamps_short_month(self):
        # Jan 31 -> Feb 28 (2026 is not a leap year), not overflow into March.
        task = Task("x", "08:00", "monthly", due_date=date(2026, 1, 31))
        assert task.next_occurrence().getDueDate() == date(2026, 2, 28)

    def test_next_occurrence_monthly_clamps_to_leap_day(self):
        # Jan 31, 2024 -> Feb 29 (2024 is a leap year).
        task = Task("x", "08:00", "monthly", due_date=date(2024, 1, 31))
        assert task.next_occurrence().getDueDate() == date(2024, 2, 29)

    def test_next_occurrence_monthly_rolls_over_year(self):
        # Dec -> Jan of the next year.
        task = Task("x", "08:00", "monthly", due_date=date(2026, 12, 10))
        assert task.next_occurrence().getDueDate() == date(2027, 1, 10)

    def test_next_occurrence_is_fresh_and_incomplete(self):
        task = Task("x", "08:00", "daily", due_date=date(2026, 1, 1))
        task.markComplete()
        follow_up = task.next_occurrence()
        assert follow_up is not task
        assert follow_up.getCompletionStatus() is False
        assert follow_up.getDescription() == task.getDescription()
        assert follow_up.getTime() == task.getTime()

    def test_next_occurrence_advances_from_own_due_date_not_today(self):
        # Completing late still lands the next task relative to its own due date.
        past = date.today() - timedelta(days=100)
        task = Task("x", "08:00", "daily", due_date=past)
        assert task.next_occurrence().getDueDate() == past + timedelta(days=1)

    def test_next_occurrence_handles_month_rollover(self):
        # timedelta arithmetic, not naive +1 to the day field.
        task = Task("x", "08:00", "daily", due_date=date(2026, 1, 31))
        assert task.next_occurrence().getDueDate() == date(2026, 2, 1)

    def test_next_occurrence_handles_leap_day(self):
        # 2024 is a leap year: Feb 28 -> Feb 29, not straight to Mar 1.
        task = Task("x", "08:00", "daily", due_date=date(2024, 2, 28))
        assert task.next_occurrence().getDueDate() == date(2024, 2, 29)


# --------------------------------------------------------------------------- #
# Task: priority                                                               #
# --------------------------------------------------------------------------- #

class TestTaskPriority:
    def test_default_priority_is_medium(self):
        task = Task("Feed", "08:00", "daily")
        assert task.getPriority() == "medium"
        assert task.getPriorityWeight() == 2

    @pytest.mark.parametrize(
        "level,weight",
        [("low", 1), ("medium", 2), ("high", 3)],
    )
    def test_priority_levels_map_to_weights(self, level, weight):
        task = Task("Feed", "08:00", "daily", priority=level)
        assert task.getPriority() == level
        assert task.getPriorityWeight() == weight

    def test_priority_normalized_to_lowercase(self):
        assert Task("x", "08:00", "daily", priority="HIGH").getPriority() == "high"
        assert Task("x", "08:00", "daily", priority="Low").getPriority() == "low"

    def test_invalid_priority_rejected(self):
        with pytest.raises(ValueError):
            Task("x", "08:00", "daily", priority="urgent")

    def test_higher_priority_has_greater_weight(self):
        high = Task("x", "08:00", "daily", priority="high")
        low = Task("y", "08:00", "daily", priority="low")
        assert high.getPriorityWeight() > low.getPriorityWeight()

    def test_next_occurrence_keeps_priority(self):
        task = Task("Vet", "09:00", "monthly", due_date=date(2026, 1, 1), priority="high")
        follow_up = task.next_occurrence()
        assert follow_up.getPriority() == "high"


# --------------------------------------------------------------------------- #
# PetInformation                                                               #
# --------------------------------------------------------------------------- #

class TestPetInformation:
    def test_getters(self):
        pet = PetInformation("Milo", 5, "Beagle", "brown")
        assert pet.getPetName() == "Milo"
        assert pet.getAge() == 5
        assert pet.getBreed() == "Beagle"
        assert pet.getColor() == "brown"

    def test_starts_with_no_tasks(self):
        assert PetInformation("Milo", 5, "Beagle", "brown").getTaskCount() == 0

    def test_add_and_remove_task(self):
        pet = PetInformation("Milo", 5, "Beagle", "brown")
        task = Task("Walk", "07:00", "daily")
        pet.addTask(task)
        assert pet.getTasks() == [task]
        assert pet.getTaskCount() == 1
        pet.removeTask(task)
        assert pet.getTaskCount() == 0


# --------------------------------------------------------------------------- #
# Owner                                                                        #
# --------------------------------------------------------------------------- #

class TestOwner:
    def test_starts_empty(self):
        owner = Owner("Liz")
        assert owner.getOwnerName() == "Liz"
        assert owner.getPetCount() == 0
        assert owner.getTotalTaskCount() == 0

    def test_add_and_remove_pet(self):
        owner = Owner("Liz")
        pet = make_pet_with_tasks("Rex")
        owner.addPet(pet)
        assert owner.getPets() == [pet]
        assert owner.getPetCount() == 1
        owner.removePet(pet)
        assert owner.getPetCount() == 0

    def test_get_all_tasks_spans_every_pet(self):
        owner = Owner("Liz")
        t1 = Task("Feed", "08:00", "daily")
        t2 = Task("Walk", "09:00", "daily")
        t3 = Task("Groom", "10:00", "weekly")
        owner.addPet(make_pet_with_tasks("Rex", [t1, t2]))
        owner.addPet(make_pet_with_tasks("Milo", [t3]))
        assert owner.getTotalTaskCount() == 3
        assert set(owner.getAllTasks()) == {t1, t2, t3}


# --------------------------------------------------------------------------- #
# Scheduler fixtures                                                           #
# --------------------------------------------------------------------------- #

@pytest.fixture
def scenario():
    """A two-pet owner with a mix of frequencies, times, and dates.

    Returns (scheduler, dict-of-named-tasks) so tests can assert on
    specific tasks by name.
    """
    d1 = date(2026, 3, 1)
    d2 = date(2026, 3, 2)
    tasks = {
        "feed_rex": Task("Feed Rex", "08:00", "daily", due_date=d1),
        "walk_rex": Task("Walk Rex", "18:00", "daily", due_date=d1),
        "groom_rex": Task("Groom Rex", "10:00", "weekly", due_date=d2),
        "feed_milo": Task("Feed Milo", "08:00", "daily", due_date=d1),
        "vet_milo": Task("Vet Milo", "09:00", "monthly", due_date=d2),
    }
    owner = Owner("Liz")
    owner.addPet(make_pet_with_tasks("Rex", [tasks["feed_rex"], tasks["walk_rex"], tasks["groom_rex"]]))
    owner.addPet(make_pet_with_tasks("Milo", [tasks["feed_milo"], tasks["vet_milo"]]))
    return Scheduler(owner), tasks


# --------------------------------------------------------------------------- #
# Scheduler: filtering                                                         #
# --------------------------------------------------------------------------- #

class TestSchedulerFiltering:
    def test_get_all_tasks(self, scenario):
        scheduler, tasks = scenario
        assert set(scheduler.getAllTasks()) == set(tasks.values())

    def test_filter_by_pet_object(self, scenario):
        scheduler, tasks = scenario
        rex = scheduler.owner.getPets()[0]
        result = scheduler.getTasksByPet(rex)
        assert set(result) == {tasks["feed_rex"], tasks["walk_rex"], tasks["groom_rex"]}

    def test_filter_by_pet_name_case_insensitive(self, scenario):
        scheduler, tasks = scenario
        result = scheduler.filter_tasks(pet_name="MILO")
        assert set(result) == {tasks["feed_milo"], tasks["vet_milo"]}

    def test_filter_by_unknown_pet_name_is_empty(self, scenario):
        scheduler, _ = scenario
        assert scheduler.filter_tasks(pet_name="Nope") == []

    def test_filter_by_frequency(self, scenario):
        scheduler, tasks = scenario
        result = scheduler.getTasksByFrequency("daily")
        assert set(result) == {tasks["feed_rex"], tasks["walk_rex"], tasks["feed_milo"]}

    def test_filter_by_frequency_case_insensitive(self, scenario):
        scheduler, _ = scenario
        assert len(scheduler.filter_tasks(frequency="WEEKLY")) == 1

    def test_completed_and_incomplete_split(self, scenario):
        scheduler, tasks = scenario
        tasks["feed_rex"].markComplete()
        completed = scheduler.getCompletedTasks()
        incomplete = scheduler.getIncompleteTasks()
        assert completed == [tasks["feed_rex"]]
        assert tasks["feed_rex"] not in incomplete
        assert len(incomplete) == 4

    def test_combined_filters(self, scenario):
        scheduler, tasks = scenario
        tasks["walk_rex"].markComplete()
        rex = scheduler.owner.getPets()[0]
        # Rex's completed daily tasks -> just the walk.
        result = scheduler.filter_tasks(pet=rex, completed=True, frequency="daily")
        assert result == [tasks["walk_rex"]]

    def test_get_tasks_by_time_matches_by_clock_minute(self, scenario):
        scheduler, tasks = scenario
        result = scheduler.getTasksByTime("8:00")  # single-digit, still matches 08:00
        assert set(result) == {tasks["feed_rex"], tasks["feed_milo"]}


# --------------------------------------------------------------------------- #
# Scheduler: sorting                                                           #
# --------------------------------------------------------------------------- #

class TestSchedulerSorting:
    def test_sort_by_time_is_chronological(self):
        owner = Owner("Liz")
        late = Task("late", "10:00", "daily")
        early = Task("early", "9:00", "daily")  # would mis-sort as text
        owner.addPet(make_pet_with_tasks("Rex", [late, early]))
        scheduler = Scheduler(owner)
        assert scheduler.sort_by_time() == [early, late]

    def test_sort_by_time_accepts_explicit_list(self, scenario):
        scheduler, tasks = scenario
        subset = [tasks["walk_rex"], tasks["feed_rex"]]  # 18:00, 08:00
        assert scheduler.sort_by_time(subset) == [tasks["feed_rex"], tasks["walk_rex"]]

    def test_sort_by_time_output_is_non_decreasing(self):
        # The core correctness property: whatever the input order, every task's
        # time is >= the one before it. Includes day boundaries and a
        # single-digit hour that must not sort as plain text.
        scheduler = Scheduler(Owner("Liz"))
        shuffled = [
            Task("noon", "12:00", "daily"),
            Task("midnight", "00:00", "daily"),
            Task("nine", "9:00", "daily"),
            Task("end of day", "23:59", "daily"),
            Task("ten", "10:00", "daily"),
            Task("half seven", "07:30", "daily"),
        ]
        ordered = scheduler.sort_by_time(shuffled)
        minutes = [t.getTimeInMinutes() for t in ordered]
        assert minutes == sorted(minutes)
        assert [t.getDescription() for t in ordered] == [
            "midnight", "half seven", "nine", "ten", "noon", "end of day",
        ]

    def test_sort_by_time_is_stable_for_equal_times(self):
        # Tasks sharing a time keep their original relative order, so a stable
        # secondary ordering (e.g. insertion order) is predictable.
        scheduler = Scheduler(Owner("Liz"))
        first = Task("first", "08:00", "daily")
        second = Task("second", "08:00", "daily")
        third = Task("third", "08:00", "daily")
        assert scheduler.sort_by_time([first, second, third]) == [first, second, third]

    def test_sort_by_time_does_not_mutate_input(self):
        # sort_by_time returns a new ordered list; the caller's list is untouched.
        scheduler = Scheduler(Owner("Liz"))
        late = Task("late", "18:00", "daily")
        early = Task("early", "06:00", "daily")
        original = [late, early]
        result = scheduler.sort_by_time(original)
        assert result == [early, late]
        assert original == [late, early]  # unchanged

    def test_sort_by_time_is_chronological_across_days(self):
        # A task due SOONER comes first even if its clock time is later: the
        # sort orders by (due_date, time), not clock time alone.
        scheduler = Scheduler(Owner("Liz"))
        today_late = Task("dinner today", "18:00", "daily", due_date=date(2026, 3, 1))
        tomorrow_early = Task("breakfast tomorrow", "08:00", "daily", due_date=date(2026, 3, 2))
        result = scheduler.sort_by_time([tomorrow_early, today_late])
        assert result == [today_late, tomorrow_early]  # by date first, then time

    def test_sort_by_time_orders_by_time_within_same_day(self):
        # Within one date, the earlier clock time still wins.
        scheduler = Scheduler(Owner("Liz"))
        d = date(2026, 3, 1)
        evening = Task("evening", "18:00", "daily", due_date=d)
        morning = Task("morning", "08:00", "daily", due_date=d)
        assert scheduler.sort_by_time([evening, morning]) == [morning, evening]

    def test_sort_by_frequency(self, scenario):
        scheduler, _ = scenario
        freqs = [t.getFrequency() for t in scheduler.sortTasksByFrequency()]
        assert freqs == sorted(freqs)

    def test_get_schedule_for_day_today_maps_to_daily(self, scenario):
        scheduler, tasks = scenario
        result = scheduler.getScheduleForDay("today")
        # Only daily tasks, sorted by time (08:00 feeds before 18:00 walk).
        assert result == [tasks["feed_rex"], tasks["feed_milo"], tasks["walk_rex"]]

    def test_get_schedule_for_day_weekly(self, scenario):
        scheduler, tasks = scenario
        assert scheduler.getScheduleForDay("weekly") == [tasks["groom_rex"]]


# --------------------------------------------------------------------------- #
# Scheduler: priority                                                          #
# --------------------------------------------------------------------------- #

class TestSchedulerPriority:
    def test_sort_by_priority_highest_first(self):
        scheduler = Scheduler(Owner("Liz"))
        d = date(2026, 3, 1)
        low = Task("low", "08:00", "daily", due_date=d, priority="low")
        high = Task("high", "08:00", "daily", due_date=d, priority="high")
        med = Task("med", "08:00", "daily", due_date=d, priority="medium")
        result = scheduler.sort_by_priority([low, high, med])
        assert result == [high, med, low]

    def test_sort_by_priority_breaks_ties_chronologically(self):
        # Same priority: earlier (date, time) wins.
        scheduler = Scheduler(Owner("Liz"))
        d = date(2026, 3, 1)
        evening = Task("evening", "18:00", "daily", due_date=d, priority="high")
        morning = Task("morning", "08:00", "daily", due_date=d, priority="high")
        assert scheduler.sort_by_priority([evening, morning]) == [morning, evening]

    def test_priority_outranks_earlier_time(self):
        # A high-priority evening task still comes before a low-priority morning one.
        scheduler = Scheduler(Owner("Liz"))
        d = date(2026, 3, 1)
        low_morning = Task("low morning", "08:00", "daily", due_date=d, priority="low")
        high_evening = Task("high evening", "18:00", "daily", due_date=d, priority="high")
        result = scheduler.sort_by_priority([low_morning, high_evening])
        assert result == [high_evening, low_morning]

    def test_sort_by_priority_does_not_mutate_input(self):
        scheduler = Scheduler(Owner("Liz"))
        low = Task("low", "08:00", "daily", priority="low")
        high = Task("high", "08:00", "daily", priority="high")
        original = [low, high]
        result = scheduler.sort_by_priority(original)
        assert result == [high, low]
        assert original == [low, high]  # unchanged

    def test_sort_by_priority_defaults_to_all_tasks(self):
        owner = Owner("Liz")
        low = Task("low", "08:00", "daily", priority="low")
        high = Task("high", "09:00", "daily", priority="high")
        owner.addPet(make_pet_with_tasks("Rex", [low, high]))
        assert Scheduler(owner).sort_by_priority() == [high, low]

    def test_filter_by_priority(self):
        owner = Owner("Liz")
        high = Task("high", "08:00", "daily", priority="high")
        low = Task("low", "09:00", "daily", priority="low")
        owner.addPet(make_pet_with_tasks("Rex", [high, low]))
        scheduler = Scheduler(owner)
        assert scheduler.getTasksByPriority("high") == [high]
        assert scheduler.filter_tasks(priority="LOW") == [low]  # case-insensitive

    def test_filter_combines_priority_with_frequency(self):
        owner = Owner("Liz")
        high_daily = Task("hd", "08:00", "daily", priority="high")
        high_weekly = Task("hw", "09:00", "weekly", priority="high")
        low_daily = Task("ld", "10:00", "daily", priority="low")
        owner.addPet(make_pet_with_tasks("Rex", [high_daily, high_weekly, low_daily]))
        result = Scheduler(owner).filter_tasks(frequency="daily", priority="high")
        assert result == [high_daily]

    def test_get_prioritized_schedule_selects_and_ranks(self):
        owner = Owner("Liz")
        d = date(2026, 3, 1)
        low_daily = Task("low daily", "07:00", "daily", due_date=d, priority="low")
        high_daily = Task("high daily", "18:00", "daily", due_date=d, priority="high")
        weekly = Task("weekly", "08:00", "weekly", due_date=d, priority="high")
        owner.addPet(make_pet_with_tasks("Rex", [low_daily, high_daily, weekly]))
        scheduler = Scheduler(owner)
        # 'today' -> daily only, ranked high-before-low despite the later time.
        assert scheduler.getPrioritizedSchedule("today") == [high_daily, low_daily]


# --------------------------------------------------------------------------- #
# Scheduler: conflict detection                                               #
# --------------------------------------------------------------------------- #

class TestSchedulerConflicts:
    def test_no_conflicts_when_times_differ(self):
        owner = Owner("Liz")
        owner.addPet(make_pet_with_tasks("Rex", [
            Task("a", "08:00", "daily", due_date=date(2026, 1, 1)),
            Task("b", "09:00", "daily", due_date=date(2026, 1, 1)),
        ]))
        scheduler = Scheduler(owner)
        assert scheduler.detectConflicts() == []
        assert scheduler.has_conflicts() is False
        assert scheduler.conflict_warnings() == []

    def test_cross_pet_conflict_flagged(self):
        owner = Owner("Liz")
        d = date(2026, 1, 1)
        owner.addPet(make_pet_with_tasks("Rex", [Task("Feed Rex", "08:00", "daily", due_date=d)]))
        owner.addPet(make_pet_with_tasks("Milo", [Task("Feed Milo", "08:00", "daily", due_date=d)]))
        scheduler = Scheduler(owner)
        conflicts = scheduler.detectConflicts()
        assert len(conflicts) == 1
        conflict = conflicts[0]
        assert conflict["date"] == d
        assert conflict["time"] == "08:00"
        assert conflict["same_pet"] is False
        assert set(conflict["pets"]) == {"Rex", "Milo"}
        assert len(conflict["tasks"]) == 2

    def test_same_pet_conflict_flagged(self):
        owner = Owner("Liz")
        d = date(2026, 1, 1)
        owner.addPet(make_pet_with_tasks("Rex", [
            Task("Feed", "08:00", "daily", due_date=d),
            Task("Pill", "08:00", "daily", due_date=d),
        ]))
        scheduler = Scheduler(owner)
        conflicts = scheduler.detectConflicts()
        assert len(conflicts) == 1
        assert conflicts[0]["same_pet"] is True
        assert conflicts[0]["pets"] == ["Rex"]

    def test_three_way_conflict_reports_all_tasks_and_distinct_pets(self):
        # Two Rex tasks + one Milo task all at the same slot: one conflict
        # holding three tasks, but only two distinct pet names.
        owner = Owner("Liz")
        d = date(2026, 1, 1)
        owner.addPet(make_pet_with_tasks("Rex", [
            Task("Feed", "08:00", "daily", due_date=d),
            Task("Pill", "08:00", "daily", due_date=d),
        ]))
        owner.addPet(make_pet_with_tasks("Milo", [
            Task("Feed Milo", "08:00", "daily", due_date=d),
        ]))
        conflicts = Scheduler(owner).detectConflicts()
        assert len(conflicts) == 1
        conflict = conflicts[0]
        assert len(conflict["tasks"]) == 3
        assert conflict["pets"] == ["Rex", "Milo"]  # distinct, first-seen order
        assert conflict["same_pet"] is False

    def test_same_time_different_dates_is_not_a_conflict(self):
        owner = Owner("Liz")
        owner.addPet(make_pet_with_tasks("Rex", [
            Task("a", "08:00", "daily", due_date=date(2026, 1, 1)),
            Task("b", "08:00", "daily", due_date=date(2026, 1, 2)),
        ]))
        assert Scheduler(owner).detectConflicts() == []

    def test_conflicts_sorted_chronologically(self):
        owner = Owner("Liz")
        d_late = date(2026, 1, 2)
        d_early = date(2026, 1, 1)
        pet = make_pet_with_tasks("Rex", [
            Task("late1", "08:00", "daily", due_date=d_late),
            Task("late2", "08:00", "daily", due_date=d_late),
            Task("early1", "08:00", "daily", due_date=d_early),
            Task("early2", "08:00", "daily", due_date=d_early),
        ])
        owner.addPet(pet)
        conflicts = Scheduler(owner).detectConflicts()
        assert [c["date"] for c in conflicts] == [d_early, d_late]

    def test_conflict_warnings_and_has_conflicts(self):
        owner = Owner("Liz")
        d = date(2026, 1, 1)
        owner.addPet(make_pet_with_tasks("Rex", [Task("Feed Rex", "08:00", "daily", due_date=d)]))
        owner.addPet(make_pet_with_tasks("Milo", [Task("Feed Milo", "08:00", "daily", due_date=d)]))
        scheduler = Scheduler(owner)
        assert scheduler.has_conflicts() is True
        warnings = scheduler.conflict_warnings()
        assert len(warnings) == 1
        assert "Conflict on" in warnings[0]
        assert "Rex" in warnings[0] and "Milo" in warnings[0]

    def test_conflict_warnings_never_raises(self, monkeypatch):
        owner = Owner("Liz")
        scheduler = Scheduler(owner)

        def boom():
            raise RuntimeError("malformed task")

        monkeypatch.setattr(scheduler, "detectConflicts", boom)
        warnings = scheduler.conflict_warnings()
        assert len(warnings) == 1
        assert "Could not check for conflicts" in warnings[0]


# --------------------------------------------------------------------------- #
# Scheduler: completion & recurrence                                          #
# --------------------------------------------------------------------------- #

class TestSchedulerCompletion:
    def test_mark_complete_adds_followup_for_recurring(self):
        # Completing a daily task creates a NEW task for the FOLLOWING day.
        owner = Owner("Liz")
        pet = make_pet_with_tasks("Rex", [Task("Feed", "08:00", "daily", due_date=date(2026, 1, 1))])
        owner.addPet(pet)
        scheduler = Scheduler(owner)
        original = pet.getTasks()[0]

        follow_up = scheduler.markTaskComplete(original)

        # The original is now done.
        assert original.getCompletionStatus() is True

        # A distinct, brand-new task was created and attached to the same pet.
        assert follow_up is not None
        assert follow_up is not original
        assert follow_up in pet.getTasks()
        assert pet.getTaskCount() == 2

        # It is due the very next day (Jan 1 -> Jan 2), exactly one day later.
        assert follow_up.getDueDate() == date(2026, 1, 2)
        assert follow_up.getDueDate() == original.getDueDate() + timedelta(days=1)

        # It carries the same details but starts incomplete, ready to be done.
        assert follow_up.getCompletionStatus() is False
        assert follow_up.getDescription() == "Feed"
        assert follow_up.getTime() == "08:00"
        assert follow_up.getFrequency() == "daily"

    def test_monthly_generates_followup_one_calendar_month_later(self):
        owner = Owner("Liz")
        pet = make_pet_with_tasks("Rex", [Task("Vet", "09:00", "monthly", due_date=date(2026, 1, 1))])
        owner.addPet(pet)
        scheduler = Scheduler(owner)

        follow_up = scheduler.markTaskComplete(pet.getTasks()[0])

        assert follow_up is not None
        assert follow_up.getDueDate() == date(2026, 2, 1)
        assert pet.getTaskCount() == 2

    def test_completing_twice_does_not_duplicate(self):
        owner = Owner("Liz")
        task = Task("Feed", "08:00", "daily", due_date=date(2026, 1, 1))
        pet = make_pet_with_tasks("Rex", [task])
        owner.addPet(pet)
        scheduler = Scheduler(owner)

        scheduler.markTaskComplete(task)
        second = scheduler.markTaskComplete(task)  # already complete

        assert second is None
        assert pet.getTaskCount() == 2  # only one follow-up ever added

    def test_reset_all_tasks(self, scenario):
        scheduler, tasks = scenario
        for t in tasks.values():
            t.markComplete()
        scheduler.resetAllTasks()
        assert all(not t.getCompletionStatus() for t in tasks.values())

    def test_find_owning_pet(self):
        owner = Owner("Liz")
        task = Task("Feed", "08:00", "daily")
        pet = make_pet_with_tasks("Rex", [task])
        owner.addPet(pet)
        scheduler = Scheduler(owner)
        assert scheduler._find_owning_pet(task) is pet
        assert scheduler._find_owning_pet(Task("Other", "08:00", "daily")) is None

    def test_completing_unowned_task_is_refused(self):
        # Completing a task that belongs to no pet is a no-op: the scheduler
        # leaves it untouched and returns None, rather than marking it complete
        # and creating a follow-up that has no pet to attach to.
        owner = Owner("Liz")
        pet = make_pet_with_tasks("Rex", [])
        owner.addPet(pet)
        scheduler = Scheduler(owner)

        stray = Task("Feed", "08:00", "daily", due_date=date(2026, 1, 1))
        follow_up = scheduler.markTaskComplete(stray)

        assert follow_up is None                     # nothing scheduled
        assert stray.getCompletionStatus() is False  # left untouched
        assert pet.getTaskCount() == 0

    def test_monthly_recurrence_stays_on_calendar(self):
        # Repeated completions keep the day-of-month and stay on the calendar:
        # Jan 1 -> Feb 1 -> Mar 1, with no 30-day drift skipping February.
        owner = Owner("Liz")
        pet = make_pet_with_tasks("Rex", [Task("Vet", "09:00", "monthly", due_date=date(2026, 1, 1))])
        owner.addPet(pet)
        scheduler = Scheduler(owner)

        first = scheduler.markTaskComplete(pet.getTasks()[0])
        assert first.getDueDate() == date(2026, 2, 1)

        second = scheduler.markTaskComplete(first)
        assert second.getDueDate() == date(2026, 3, 1)


# --------------------------------------------------------------------------- #
# Integration                                                                  #
# --------------------------------------------------------------------------- #

class TestIntegration:
    def test_daily_routine_keeps_going_over_several_completions(self):
        owner = Owner("Liz")
        pet = make_pet_with_tasks("Rex", [Task("Feed", "08:00", "daily", due_date=date(2026, 1, 1))])
        owner.addPet(pet)
        scheduler = Scheduler(owner)

        current = pet.getTasks()[0]
        due = date(2026, 1, 1)
        for _ in range(3):
            follow_up = scheduler.markTaskComplete(current)
            due += timedelta(days=1)
            assert follow_up.getDueDate() == due
            current = follow_up

        # 1 original + 3 generated follow-ups.
        assert pet.getTaskCount() == 4
        # Exactly the three completed ones are done.
        assert len(scheduler.getCompletedTasks()) == 3
        assert len(scheduler.getIncompleteTasks()) == 1


# --------------------------------------------------------------------------- #
# Empty / boundary states                                                      #
# --------------------------------------------------------------------------- #

class TestEmptyStates:
    @pytest.fixture
    def empty_scheduler(self):
        return Scheduler(Owner("Liz"))

    def test_no_tasks_returns_empty_not_error(self, empty_scheduler):
        assert empty_scheduler.getAllTasks() == []
        assert empty_scheduler.sort_by_time() == []
        assert empty_scheduler.detectConflicts() == []
        assert empty_scheduler.conflict_warnings() == []
        assert empty_scheduler.has_conflicts() is False
        assert empty_scheduler.getScheduleForDay("today") == []

    def test_owner_with_pet_but_no_tasks(self):
        owner = Owner("Liz")
        owner.addPet(make_pet_with_tasks("Rex", []))
        scheduler = Scheduler(owner)
        assert scheduler.getAllTasks() == []
        assert scheduler.detectConflicts() == []
