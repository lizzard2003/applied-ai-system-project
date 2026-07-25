# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
  My initial design is to have 3 different classes :
  Pet information
  Pet tasks
  Time Constraint
- What classes did you include, and what responsibilities did you assign to each?
  Classes : |Attributes :
  Pet information |Pet breed, name, pet age
  Pet tasks | Walks, feedings, pet sitting
  Time Constraints | avaliability , duration of tasks, repetition

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
  After I asked Claude about relationships and bottle necks. It gave me feedback on my skeleton not being connected to one another. A task list attribute was added to pet information to list tasks needed for that specific pet. All 3 classes have been added a **init** constructor and corrections have been made to return data types.
  On the diagram it was updated by adding a relationship where Petinformation manages PetTasks and PetTasks has TimeConstraints.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)? It considers time .
- How did you decide which constraints mattered most? The constraint matter the most because if you have 2 tasks at the same time they will intervine with one another and cause bad customer service.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
  The redundant sort was a trade off. It would sort time over and over on each run. The other problem was that time was constraining it self with one another. This would be because we didnt know if it was 9:00 am pr 9:00 pm. That was fixed by doing a military time change.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)? I used Claude to help brainstorm and debug code.
- What kinds of prompts or questions were most helpful?
  The most helpful question were the onces that I told Clause what I did not want .
  **b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested? When Claude gave me too many classes to start with my diagram. I reworded my promp to tell claude to help and not add as many classes to the diagram.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test? I tested any time conflicts, If there was a time conflict there should be a warning. I also tested for repetition when it came to an owner. You do not want to keep adding owners after they have been added.
- Why were these tests important? The tests are important for efficiancy and to detect bug. Another importance comes after the test because it mught raise other concerns you were not aware of.

**b. Confidence**

- How confident are you that your scheduler works correctly? I am 5 confident that the scheduler will work.
- What edge cases would you test next if you had more time? I would have a clear all button to clear all the information that was input. This would allow user to add a new user, pet or task faster. I would do more schedule filtering.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
  I am satistfied with UI portion of it, it is user friendly and it is helpful after information has been inputted.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
  I would put in a database to expand on the capabity or even add a section where the user can add a picture of their pet.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
  I learned that what you first design is not what you will always end up with in the end. You might want to keep it slim but then you have to count for exceptions and tests to make sure everything works well with each other.

# 6. Smart Scheduling

a. Sorting Behaviors -
sort_by_time() - Orders tasks chronologically earliest first,
sortTaskVyFrequency - Groups tasls by frequency alphabetachally : daily , monthly, weekly
detectConflicts()= Acompound (tuple) sort: conflicts are ordered by due date first then by time within a date.

b. Filtering Behaviors -
GetScheduleForDay()= first filters out frequency then sorts the time.

c. Conflict Detection =
detectConflicts()= Acompound (tuple) sort: conflicts are ordered by due date first then by time within a date.

d. Reoccurance-
Tasks are set to reoccure it is a repetitive task that is daily or weekly.
The app also pushes to next task on the list at Task.next_occurance.
Another trigger is completion. Once a task is marked as complete then it does not keep reoccuring meaning it will prevent outliers.

# 7. Generalized Pet Information

When an owner adds a pet, the app returns care information about that pet. If
the pet's breed is one the app knows, it gives specific info; if not, it gives a
generalized answer instead. This is implemented as `getPetInformation(breed)` in
pawpal_system.py, backed by a `PET_KNOWLEDGE_BASE` dictionary, and it shows up in
both the console demo (main.py) and the Streamlit app (app.py).

**Design note:** My RAG API diagram shows the full intended architecture —
image/text input, a Vision/LLM layer, RAG retrieval from a knowledge base, and an
LLM-generated answer. The current implementation is a simpler stand-in for that:
a plain local dictionary lookup with a generalized fallback, so it needs no API
key or internet and runs with just streamlit and pytest. The lookup-with-fallback
behavior is the same shape as the diagram; swapping the dictionary for a real
LLM/RAG call would be the next iteration.
