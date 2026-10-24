"""
The demo's history, day by day: what was done to each project and when,
as the app's own edits (build.py runs them). Each project ends in the
tree the demo shows. Dates are written as if today were
build.WRITTEN_FOR; times are local (Europe/Oslo) and given only where
something else depends on them (a chat reply that names a time).

A path is node labels from the top, joined by "/". An outline is one
node per line, indented two spaces per level.
"""

# Contents
#  1. Actions
#      - create(), paste(), add(), rename(), move(), remove(),
#        save_tree(), chat()
#
#  2. Projects
#      - ACCOUNT
#      - BUILDING_PROJECT
#      - TRAINING
#      - CHARACTER_A
#      - PROJECTS

# ============================================================
# 1. Actions
# ============================================================


def create() -> dict:
    return {"do": "create"}


def paste(under: str | None, outline: str) -> dict:
    return {"do": "paste", "under": under, "outline": outline}


def add(under: str | None, label: str) -> dict:
    return {"do": "add", "under": under, "label": label}


def rename(path: str, label: str) -> dict:
    return {"do": "rename", "path": path, "label": label}


def move(path: str, direction: str, at: str | None = None) -> dict:
    return {"do": "move", "path": path, "direction": direction, "at": at}


def remove(path: str) -> dict:
    return {"do": "remove", "path": path}


def save_tree(path: str) -> dict:
    return {"do": "save_tree", "path": path}


def chat(
    about: str | None,
    message: str,
    reply: str,
    at: str,
    focus_day: str | None = None,
) -> dict:
    """A chat turn, about a node (`about`), one day's changes
    (`focus_day`), or the whole project. `{date:YYYY-MM-DD}` in the
    reply is written as that date after the shift ("14 Oct")."""
    return {
        "do": "chat",
        "about": about,
        "message": message,
        "reply": reply,
        "at": at,
        "focus_day": focus_day,
    }


# ============================================================
# 2. Projects
# ============================================================

ACCOUNT = "John Doe"

CC = "Civic Centre"
ACTORS = f"{CC}/Actors"

BUILDING_PROJECT = (
    "Building Project",
    [
        (
            "2026-08-03",
            [
                create(),
                paste(
                    None,
                    """
Civic Centre
  Development
    Concept
    Design
    Planning
""",
                ),
            ],
        ),
        (
            "2026-08-04",
            [paste(f"{CC}/Development/Concept", "Site\nDesign Principles")],
        ),
        (
            "2026-08-06",
            [
                paste(
                    f"{CC}/Development/Concept/Site",
                    """
Context
  Surroundings
  Access
Constraints
""",
                )
            ],
        ),
        (
            "2026-08-10",
            [
                paste(
                    f"{CC}/Development/Design",
                    """
Architecture
  Floor Plans
  Elevations
Materials
""",
                )
            ],
        ),
        (
            "2026-08-12",
            [
                paste(
                    f"{CC}/Development/Design/Architecture/Floor Plans",
                    """
Ground Floor
  Entrance
  Offices
First Floor
""",
                )
            ],
        ),
        (
            "2026-08-14",
            [
                paste(
                    f"{CC}/Development/Design/Architecture/Floor Plans/Ground Floor/Entrance",
                    """
Lobby
  Reception
Stair
""",
                )
            ],
        ),
        (
            "2026-08-17",
            [
                paste(
                    f"{CC}/Development/Planning",
                    """
Application
  Documentation
  Drawings
  Approval
Authorities
""",
                )
            ],
        ),
        (
            "2026-08-19",
            [
                add(f"{CC}/Development/Planning/Application/Approval", "Conditions"),
                add(
                    f"{CC}/Development/Planning/Application/Approval/Conditions",
                    "Revisions",
                ),
            ],
        ),
        (
            "2026-08-21",
            [
                add(CC, "Documents"),
                paste(
                    f"{CC}/Documents",
                    """
Contracts
  Architect Agreement
  Contractor Agreement
Drawings
Reports
""",
                ),
            ],
        ),
        (
            "2026-08-24",
            [
                paste(
                    f"{CC}/Documents/Contracts/Architect Agreement",
                    """
Scope
  Services
    Design
      Concept
        Delivery
      Documentation
    Coordination
  Responsibilities
Fee
""",
                )
            ],
        ),
        (
            "2026-08-26",
            [rename(f"{CC}/Documents/Contracts/Architect Agreement/Fee", "Fees")],
        ),
        (
            "2026-08-27",
            [
                paste(
                    CC,
                    """
Actors
  Client
  Architect
  Engineers
  Contractor
  Authorities
""",
                )
            ],
        ),
        (
            "2026-08-31",
            [
                paste(
                    f"{ACTORS}/Client",
                    """
Client A
  Organization ID
  Client Representative
  Project Manager
  Responsibilities
""",
                )
            ],
        ),
        (
            "2026-09-01",
            [
                paste(
                    f"{ACTORS}/Architect",
                    """
Architect A
  Organization ID
  Project Architect
  Project Manager
  Responsibilities
""",
                )
            ],
        ),
        ("2026-09-02", [remove(f"{ACTORS}/Architect/Architect A/Responsibilities")]),
        ("2026-09-03", [add(f"{ACTORS}/Architect/Architect A", "Responsibilities")]),
        (
            "2026-09-04",
            [
                paste(
                    f"{ACTORS}/Engineers",
                    """
Engineer A
  Organization ID
  Lead Engineer
  Project Manager
  Responsibilities
""",
                )
            ],
        ),
        (
            "2026-09-07",
            [
                paste(
                    f"{ACTORS}/Engineers",
                    """
Engineer B
  Organization ID
  Lead Engineer
  Project Manager
  Responsibilities
""",
                )
            ],
        ),
        (
            "2026-09-08",
            [
                paste(
                    f"{ACTORS}/Contractor",
                    """
Contractor A
  Organization ID
  Site Manager
  Project Manager
  Responsibilities
""",
                )
            ],
        ),
        (
            "2026-09-10",
            [
                paste(
                    f"{ACTORS}/Authorities",
                    """
Municipality
  Organization ID
  People
    Case Officer
    Planning Officer
  Responsibilities
""",
                )
            ],
        ),
        (
            "2026-09-11",
            [
                paste(
                    f"{ACTORS}/Authorities",
                    """
Labour Inspectorate
  Organization ID
  People
    Officer
    Case Officer
  Responsibilities
""",
                )
            ],
        ),
        (
            "2026-09-14",
            [
                rename(
                    f"{ACTORS}/Authorities/Labour Inspectorate/People/Officer",
                    "Inspector",
                )
            ],
        ),
        (
            "2026-09-15",
            [
                paste(
                    CC,
                    """
Construction
  Building
    Structure
    Envelope
    Interior
  Systems
  Site
""",
                )
            ],
        ),
        (
            "2026-09-17",
            [
                paste(
                    f"{CC}/Construction/Building/Structure",
                    "Foundations\nColumns\nBeams",
                ),
                paste(f"{CC}/Construction/Building/Envelope", "Facade\nWindows\nRoof"),
            ],
        ),
        (
            "2026-09-18",
            [paste(f"{CC}/Construction/Building/Interior", "Walls\nDoors\nFloors")],
        ),
        (
            "2026-09-21",
            [
                paste(
                    f"{CC}/Construction/Systems",
                    "HVAC\nElectrical\nPlumbing\nFire Safety",
                )
            ],
        ),
        (
            "2026-09-22",
            [paste(f"{CC}/Construction/Site", "Terrain\nRoads\nLandscaping")],
        ),
        (
            "2026-09-24",
            [
                paste(
                    CC,
                    """
Changes
  Change Request #001
    Reason
    Proposal
    Cost Impact
    Schedule Impact
    Review
    Client Decision
    Implementation
""",
                )
            ],
        ),
        (
            "2026-09-28",
            [
                paste(
                    CC,
                    """
Completion
  Inspection
  Punch List
  Handover
  Closeout
""",
                )
            ],
        ),
        (
            "2026-09-30",
            [
                paste(
                    CC,
                    """
Agreements
  Agreement #001
    Parties
      Client A
      Architect A
    Terms
      Scope
      Responsibilities
      Fee
""",
                )
            ],
        ),
        (
            "2026-10-01",
            [
                paste(
                    CC,
                    """
BIM Objects
  Building Elements
  Components
  Systems
  Equipment
""",
                )
            ],
        ),
        ("2026-10-05", [move(f"{CC}/BIM Objects", "up", at="12:03")]),
        (
            "2026-10-06",
            [
                paste(
                    f"{CC}/Development/Concept/Site/Context/Surroundings",
                    """
Buildings
  Existing Conditions
    Documentation
      Survey
      Measurements
        ...
  Infrastructure
Landscape
""",
                )
            ],
        ),
        (
            "2026-10-07",
            [
                paste(
                    f"{CC}/Agreements",
                    """
Agreement #002
  Parties
    Client A
    Contractor B
  Terms
    Scope
    Responsibilities
    Schedule
""",
                )
            ],
        ),
        (
            "2026-10-08",
            [
                move(f"{CC}/BIM Objects", "up", at="10:16"),
                move(f"{CC}/BIM Objects", "up", at="10:32"),
            ],
        ),
        (
            "2026-10-13",
            [
                chat(
                    f"{CC}/Development/Concept",
                    "Whats this?",
                    "Concept is a part under Development that contains the Site, Design Principles, and other foundational elements for the project. It helps define the initial ideas and constraints before moving into detailed design work.",
                    at="15:29:48",
                )
            ],
        ),
        (
            "2026-10-14",
            [
                move(f"{CC}/BIM Objects", "up", at="11:35"),
                chat(
                    f"{CC}/Development/Concept/Site/Context/Surroundings",
                    "Whats this",
                    "Surroundings is a part under Concept that focuses on the external environment of the site, including nearby buildings, infrastructure, and landscape features. It helps understand how the project fits into its existing context before detailed design begins.",
                    at="15:37:48",
                ),
                chat(
                    f"{CC}/Development/Concept/Site/Context/Surroundings",
                    "What does it include",
                    "Surroundings includes Buildings, Infrastructure, and Landscape as its main components. These parts help define the external environment around the site.",
                    at="15:50:48",
                ),
            ],
        ),
        (
            "2026-10-16",
            [
                chat(
                    None,
                    "What's this project about?",
                    "The project is a building construction effort for a Civic Centre that covers everything from initial concept and planning through to construction, changes, and final handover. It organizes information about actors, documents, BIM objects, and specific building systems like structure and HVAC.",
                    at="15:28:48",
                ),
                chat(
                    None,
                    "What happened here?",
                    "On {date:2026-10-14} at 11:35 a part under Civic Centre named BIM Objects was moved to sit above Construction in the project structure.",
                    at="16:05:00",
                    focus_day="2026-10-14",
                ),
            ],
        ),
        ("2026-10-19", [add(f"{CC}/Changes", "Change Request #002")]),
        ("2026-10-21", [add(f"{CC}/Changes", "Design Revision 3")]),
        (
            "2026-10-23",
            [rename(f"{CC}/Changes/Design Revision 3", "Design Revision #03")],
        ),
    ],
)

UPPER_BODY = "Plan/Focus/Strength/Upper Body"

TRAINING = (
    "Training",
    [
        (
            "2026-09-14",
            [
                create(),
                paste(
                    None,
                    """
Plan
  Schedule
    Monday
      18.00-20.00
    Wednesday
      14:30-16.00
    Friday
      14.00-15.00
  Goals
""",
                ),
            ],
        ),
        ("2026-09-15", [move("Plan/Goals", "up"), add("Plan", "Workouts")]),
        (
            "2026-09-16",
            [
                paste(
                    "Plan",
                    """
Focus
  Strength
    Upper Body
      Excercises
        Bench
        Military Press
    Lower Body
      Excercises
        Squat
        Deadlift
  Condition
    Exercises
      Intervalls
      5 km run
""",
                )
            ],
        ),
        ("2026-09-17", [remove("Plan/Workouts")]),
        (
            "2026-09-18",
            [
                paste(
                    None,
                    """
Log
  2026
    September
      Week 1
        Monday
          Upper Body
            Bench Press
            Pull-ups
            Shoulder Press
        Wednesday
          Lower Body
            Squat
            Deadlift
      Week 2
        Monday
          Upper Body
            Bench Press
            Pull-ups
            Biceps Curl
        Wednesday
          Lower Body
            Squat
            Leg Press
        Friday
          Conditioning
            5 km Run
""",
                )
            ],
        ),
        (
            "2026-09-25",
            [
                paste(
                    "Log/2026/September",
                    """
Week 3
  Tuesday
    Upper Body
      Bench Press
      Shoulder Press
      Triceps Extension
  Friday
    Lower Body
      Squat
      Deadlift
""",
                )
            ],
        ),
        (
            "2026-09-28",
            [
                save_tree("Plan/Focus"),
                save_tree("Plan/Focus/Strength"),
                paste(
                    UPPER_BODY,
                    """
Compound
  Bench Press
  Squat
  Pull-ups
Isolation
  Biceps Curl
  Triceps Extension
  Lateral Raise
""",
                ),
                save_tree(f"{UPPER_BODY}/Compound"),
                save_tree(f"{UPPER_BODY}/Isolation"),
                save_tree("Plan/Focus/Condition"),
                remove(f"{UPPER_BODY}/Excercises"),
            ],
        ),
        (
            "2026-10-01",
            [
                paste(
                    "Log/2026/September",
                    """
Week 4
  Monday
    Upper Body
      Bench Press
      Pull-ups
      Lateral Raise
  Wednesday
    Lower Body
      Squat
      Deadlift
      Leg Press
  Friday
    Conditioning
      Intervals
      5 km Run
""",
                )
            ],
        ),
        ("2026-10-02", [rename("Plan/Focus", "Exercises")]),
        (
            "2026-10-13",
            [
                chat(
                    None,
                    "Hello",
                    "Hi there. How can I help you with the Training project today?",
                    at="15:40:48",
                )
            ],
        ),
        (
            "2026-10-16",
            [
                chat(
                    "Plan/Schedule/Monday/18.00-20.00",
                    "What's this?",
                    "This part is a time slot scheduled for Monday at 18:00 to 20:00 under the Plan section of the project. It does not specify what activities are planned for that time yet.",
                    at="15:39:48",
                )
            ],
        ),
        (
            "2026-10-19",
            [paste("Log/2026", "October\n  Week 1\n  Week 2\n  Week 3\n  Week 4")],
        ),
    ],
)

CHARACTER_A = (
    "Character A",
    [
        (
            "2026-10-05",
            [
                create(),
                paste(
                    None,
                    """
STORY
  Genre: Mystery novel
  Role: Protagonist
IDENTITY
  Character ID: C-001
  Age: 26
  Place of Birth: Kyoto, Japan
  Occupation: Investigator
""",
                ),
            ],
        ),
        (
            "2026-10-06",
            [
                paste(
                    None,
                    """
BACKGROUND
  Family Background
    Parent A
    Parent B
  Education
    Investigative Sciences
  Formative Experience
    A sibling disappeared during childhood
""",
                )
            ],
        ),
        (
            "2026-10-07",
            [
                paste(
                    None,
                    """
PERSONALITY
  Strengths
    Observant
    Persistent
  Weaknesses
    Distrustful
    Obsessive
  Motivation
    Discover the truth
  Internal Conflict
    Truth versus personal loyalty
""",
                )
            ],
        ),
        (
            "2026-10-08",
            [
                paste(
                    None,
                    """
RELATIONSHIPS
  Person B
    Relationship: Mentor
    Status: Close
  Person C
    Relationship: Colleague
    Status: Trusted
""",
                )
            ],
        ),
        (
            "2026-10-09",
            [
                paste(
                    None,
                    """
LIFE EVENTS
  Age 10 — Sibling Disappears
    Shapes Character's Motivation
  Age 19 — Leaves Home
    Begins Independent Life
""",
                )
            ],
        ),
        (
            "2026-10-12",
            [
                paste(
                    None,
                    """
CURRENT STATE
  Location: Berlin, Germany
  Main Obstacle: Conflicting Evidence
  Active Goal: Investigate a Missing Person
""",
                ),
                move("CURRENT STATE/Active Goal: Investigate a Missing Person", "up"),
            ],
        ),
        (
            "2026-10-13",
            [
                rename(
                    "RELATIONSHIPS/Person B/Relationship: Mentor",
                    "Relationship: Former Mentor",
                ),
                rename("RELATIONSHIPS/Person B/Status: Close", "Status: Estranged"),
            ],
        ),
        (
            "2026-10-14",
            [
                chat(
                    None,
                    "Who is this?",
                    "This project defines an investigator named Character ID C-001, who is 26 years old and currently based in Berlin. Born in Kyoto, Japan, their primary motivation is to discover the truth despite a deep-seated distrust of institutions. Their background includes a formative experience where a sibling disappeared during childhood, which shapes their persistent but obsessive nature.",
                    at="15:24:48",
                )
            ],
        ),
        (
            "2026-10-15",
            [add("CURRENT STATE", "Current Conflict: Mentor May Be Involved")],
        ),
        (
            "2026-10-16",
            [
                chat(
                    "RELATIONSHIPS",
                    "What's this?",
                    "This part lists two key figures in the investigator's life: Person B, who is a former mentor with an estranged status, and Person C, who is a trusted colleague. It also notes that the current conflict involves the possibility that the former mentor may be involved in the main case.",
                    at="15:41:48",
                )
            ],
        ),
        (
            "2026-10-20",
            [
                paste(
                    "LIFE EVENTS",
                    "Age 24 — Case Goes Unresolved\n  Loses Trust in the Institution",
                )
            ],
        ),
    ],
)

PROJECTS = [BUILDING_PROJECT, TRAINING, CHARACTER_A]
