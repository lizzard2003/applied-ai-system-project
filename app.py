import streamlit as st
from pawpal_system import Owner,Task,PetInformation,Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")

# The "vault": a dictionary of owners keyed by name (name -> Owner object).
# Initialize it ONCE so Streamlit's re-runs don't wipe it.
if "owners" not in st.session_state:
    st.session_state.owners = {}

owner_name = st.text_input("Owner name", value="Jordan")

if st.button("Add owner"):
    # THE CHECK: is an owner with this name already in the vault?
    if owner_name in st.session_state.owners:
        st.warning(f"'{owner_name}' already exists — not creating a duplicate.")
    else:
        st.session_state.owners[owner_name] = Owner(owner_name)
        st.success(f"Added owner: {owner_name}")

# Show everyone currently stored in the vault.
if st.session_state.owners:
    st.write("Current owners:")
    st.table({"Owner": list(st.session_state.owners.keys())})
else:
    st.info("No owners yet. Add one above.")

st.divider()

st.markdown("### Add a Pet")
st.caption("Pets belong to an owner. Pick an owner, then create the pet.")

if not st.session_state.owners:
    st.info("Add an owner first before adding pets.")
else:
    # Pick which owner this pet belongs to.
    pet_owner_name = st.selectbox(
        "Owner for this pet", list(st.session_state.owners.keys())
    )

    pcol1, pcol2 = st.columns(2)
    with pcol1:
        pet_name = st.text_input("Pet name", value="Mochi")
        pet_breed = st.text_input("Breed", value="Tabby")
    with pcol2:
        pet_age = st.number_input("Age", min_value=0, max_value=40, value=3)
        pet_color = st.text_input("Color", value="Orange")

    if st.button("Add pet"):
        owner = st.session_state.owners[pet_owner_name]          # get the Owner object
        existing = [p.getPetName() for p in owner.getPets()]
        if pet_name in existing:
            st.warning(f"'{pet_name}' already exists for {pet_owner_name}.")
        else:
            pet = PetInformation(pet_name, int(pet_age), pet_breed, pet_color)
            owner.addPet(pet)                                    # <-- the class method
            st.success(f"Added pet '{pet_name}' to {pet_owner_name}")

    # Show this owner's pets by reading back from the object.
    owner = st.session_state.owners[pet_owner_name]
    if owner.getPets():
        st.write(f"{pet_owner_name}'s pets:")
        st.table(
            [
                {"Name": p.getPetName(), "Age": p.getAge(),
                 "Breed": p.getBreed(), "Color": p.getColor(),
                 "Tasks": p.getTaskCount()}
                for p in owner.getPets()
            ]
        )
    else:
        st.info(f"{pet_owner_name} has no pets yet.")

st.divider()

st.markdown("### Schedule a Task")
st.caption("Tasks belong to a specific pet. Pick the owner and pet, then add the task.")

# Build the list of (owner, pet) pairs that currently exist in the vault.
owner_pet_pairs = []
for o_name, o in st.session_state.owners.items():
    for p in o.getPets():
        owner_pet_pairs.append((o_name, p))

if not owner_pet_pairs:
    st.info("Add an owner and a pet first before scheduling tasks.")
else:
    # Label each pair so the user can pick one; map the label back to the pet.
    labels = {f"{o_name} → {p.getPetName()}": p for o_name, p in owner_pet_pairs}
    chosen_label = st.selectbox("Pet to schedule for", list(labels.keys()))
    target_pet = labels[chosen_label]

    tcol1, tcol2, tcol3, tcol4 = st.columns(4)
    with tcol1:
        task_desc = st.text_input("Description", value="Morning walk")
    with tcol2:
        task_time = st.text_input("Time", value="08:00")
    with tcol3:
        task_freq = st.selectbox("Frequency", ["daily", "weekly", "monthly"], index=0)
    with tcol4:
        task_priority = st.selectbox("Priority", ["high", "medium", "low"], index=1)

    if st.button("Add task"):
        task = Task(task_desc, task_time, task_freq, priority=task_priority)  # construct the Task
        target_pet.addTask(task)                                 # <-- the class method
        st.success(f"Added task '{task_desc}' ({task_priority} priority) to {target_pet.getPetName()}")

    # Show the chosen pet's tasks by reading back from the object.
    if target_pet.getTasks():
        st.write(f"Tasks for {target_pet.getPetName()}:")
        st.table(
            [
                {"Description": t.getDescription(), "Time": t.getTime(),
                 "Frequency": t.getFrequency(), "Priority": t.getPriority(),
                 "Done": t.getCompletionStatus()}
                for t in target_pet.getTasks()
            ]
        )
    else:
        st.info(f"{target_pet.getPetName()} has no tasks yet.")

st.divider()

st.subheader("Build Schedule")
st.caption("Pick an owner and a day; the Scheduler collects and orders their tasks.")

if not st.session_state.owners:
    st.info("Add an owner (and some pet tasks) first to build a schedule.")
else:
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        sched_owner_name = st.selectbox(
            "Owner", list(st.session_state.owners.keys()), key="sched_owner"
        )
    with fcol2:
        day = st.selectbox("Day / frequency", ["today", "daily", "weekly", "monthly"])
    with fcol3:
        status = st.selectbox("Status", ["All", "To do", "Done"])

    owner = st.session_state.owners[sched_owner_name]
    scheduler = Scheduler(owner)                       # <-- your Scheduler class

    # Conflict banner across ALL of this owner's tasks, using the Scheduler's
    # safe check (returns human-readable warnings, never raises).
    warnings = scheduler.conflict_warnings()
    if warnings:
        st.warning(f"⚠️ {len(warnings)} scheduling conflict(s) detected")
        for warning in warnings:
            st.markdown(f"- {warning}")
    else:
        st.success("✅ No scheduling conflicts.")

    # Let the owner choose how the plan is ordered: chronologically, or with the
    # highest-priority tasks first (ties still broken by time).
    order = st.radio(
        "Order by", ["Time", "Priority"], horizontal=True, key="sched_order"
    )

    # Filter + sort using the Scheduler's own methods. 'today' maps to daily
    # tasks; the Status dropdown maps to the completed flag (None = no filter).
    frequency = "daily" if day in ("today", "daily") else day
    completed = {"All": None, "To do": False, "Done": True}[status]
    filtered = scheduler.filter_tasks(frequency=frequency, completed=completed)
    tasks = (
        scheduler.sort_by_priority(filtered)
        if order == "Priority"
        else scheduler.sort_by_time(filtered)
    )

    # Headline metrics for the chosen frequency (before the status filter),
    # so the owner always sees the full done/remaining picture.
    all_for_freq = scheduler.filter_tasks(frequency=frequency)
    total = len(all_for_freq)
    done = sum(1 for t in all_for_freq if t.getCompletionStatus())
    mcol1, mcol2, mcol3 = st.columns(3)
    mcol1.metric("Total", total)
    mcol2.metric("Done", done)
    mcol3.metric("To go", total - done)

    st.markdown(f"#### Schedule for {sched_owner_name} — {day} ({status})")
    if not tasks:
        st.info(f"No '{day}' tasks matching '{status}' for {sched_owner_name}.")
    else:
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        st.table(
            [
                {
                    "Status": "✅ Done" if t.getCompletionStatus() else "🔲 To do",
                    "Time": t.getTime(),
                    "Task": t.getDescription(),
                    "Priority": f"{priority_icon.get(t.getPriority(), '')} {t.getPriority().capitalize()}",
                    "Frequency": t.getFrequency().capitalize(),
                }
                for t in tasks
            ]
        )
        # A simple "explanation" of the plan, matching whichever ordering was chosen.
        if order == "Priority":
            reason = "ordered by priority (highest first), ties broken by date then time"
        else:
            reason = "ordered by date then time of day"
        st.markdown("**Why this plan:**")
        for t in tasks:
            st.markdown(
                f"- **{t.getTime()}** — *{t.getDescription()}* "
                f"[{t.getPriority()} priority] (frequency matches '{day}', {reason})"
            )
