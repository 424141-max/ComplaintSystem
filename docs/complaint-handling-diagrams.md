# Complaint Handling Process

## 4.3 Activity Diagram: Complaint Handling Process

Figure 4.2 - Activity Diagram of the Complaint Handling Process

```mermaid
flowchart TD
    start((Start)) --> citizen[Citizen submits complaint]
    citizen --> validate{System validates complaint}
    validate -->|Invalid| fix[Citizen corrects complaint]
    fix --> citizen
    validate -->|Valid| store[System stores complaint]
    store --> review[Administrator reviews complaint]
    review --> priority[Administrator assigns priority level]
    priority --> available{Crew available?}
    available -->|No| recommend[Create or recommend crew]
    recommend --> available
    available -->|Yes| assign[Crew assigned to complaint]
    assign --> navigate[Crew navigates to location]
    navigate --> resolve[Cleaner resolves complaint]
    resolve --> proof[Crew leader uploads completion proof]
    proof --> verify[Administrator verifies work]
    verify --> accepted{Work verified?}
    accepted -->|No| navigate
    accepted -->|Yes| close[Administrator closes complaint]
    close --> finish((End))
```

## 4.4 Sequence Diagram: Complaint Submission and Crew Assignment

```mermaid
sequenceDiagram
    actor Citizen
    participant System as SWMS System
    participant DB as Complaint Database
    actor Administrator
    actor CrewLeader as Crew Leader

    Citizen->>System: Submit complaint and location
    System->>System: Validate required fields
    alt Complaint is invalid
        System-->>Citizen: Return validation errors
    else Complaint is valid
        System->>DB: Store complaint with Submitted status
        DB-->>System: Return complaint reference
        System-->>Citizen: Confirm submission and reference
        System-->>Administrator: Add complaint to review queue
        Administrator->>System: Review complaint and set priority
        System->>DB: Save priority and review status
        System->>DB: Check available crews
        alt A crew is available
            DB-->>System: Return available crew
            Administrator->>System: Assign crew
            System->>DB: Save crew assignment
            System-->>CrewLeader: Send assignment and location
            CrewLeader->>System: Start work at complaint location
            System->>DB: Mark complaint In Progress
            CrewLeader->>System: Upload completion proof
            System->>DB: Save proof and mark Resolved
            System-->>Administrator: Request verification
            Administrator->>System: Verify proof and close complaint
            System->>DB: Save Closed status
            System-->>Citizen: Notify complaint is closed
        else No crew is available
            System-->>Administrator: Recommend creating or scheduling a crew
        end
    end
```