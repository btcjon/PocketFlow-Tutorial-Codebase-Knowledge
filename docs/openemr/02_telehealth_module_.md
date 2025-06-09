# Chapter 2: Telehealth Module

Welcome back! In [Chapter 1: Patient Portal](01_patient_portal_.md), we saw how OpenEMR helps patients connect with their health information online. Now, let's explore an even more direct way for patients and doctors to connect: the **Telehealth Module**.

Imagine you need to talk to your doctor, but you can't easily get to the clinic – maybe you're at work, or feeling too unwell to travel. That's where telehealth comes in! The Telehealth Module in OpenEMR is like a **secure video call system built right into the medical software**. It allows doctors and patients to have virtual appointments, just like they would in person, but from anywhere with an internet connection.

Think of it as a virtual consultation room. It handles everything needed for a smooth video call, from scheduling to managing who's in the call, and even updating patient records afterward.

## A Real-World Use Case: A Virtual Doctor's Visit

Let's imagine our patient, Jane Doe, has a follow-up appointment with her doctor. Instead of going to the clinic, she's having a virtual visit.

**Use Case: Jane has a scheduled telehealth appointment with her doctor.**

1.  **Scheduling:** The clinic schedules a telehealth appointment for Jane in OpenEMR.
2.  **Invitation:** Jane receives a secure email or portal message with a link to join her virtual appointment.
3.  **Joining the Call:** At the time of the appointment, both Jane and her doctor click their respective links in OpenEMR.
4.  **Virtual Consultation:** They meet in the secure video conferencing room. The doctor can even view Jane's chart during the call.
5.  **Updating Records:** After the call, the appointment status in OpenEMR is automatically updated, and the doctor can easily add notes to Jane's patient file.

This seems simple, but there's a lot happening behind the scenes to make it work!

## Key Concepts of the Telehealth Module

The Telehealth Module isn't just a simple video call. It's designed specifically for healthcare, meaning it's secure, integrated, and smart.

1.  **Secure Video Conferencing:** This is the core. It's a "virtual room" protected to keep patient information private.
2.  **Scheduling Integration:** It works directly with OpenEMR's calendar, so appointments scheduled as telehealth automatically have a video call link.
3.  **Participant Management:** It knows who should be in the call (doctor and patient) and can even add others like a specialist or family member.
4.  **Automatic Status Updates:** When a call starts or ends, OpenEMR automatically updates the appointment's status (e.g., "pending" to "in session").
5.  **"Comlink Telehealth":** This is the technical behind-the-scenes part that handles the secure communication. OpenEMR *uses* Comlink Telehealth to power its virtual calls.

## How it Works: Behind the Virtual Curtain

Let's simplify how a telehealth session is launched and conducted.

```mermaid
sequenceDiagram
    participant D as Doctor (OpenEMR)
    participant P as Patient (Patient Portal)
    participant TM as Telehealth Module
    participant C as Comlink Telehealth Service

    D->>TM: 1. Launches telehealth appointment for Jane
    TM->>C: 2. Requests secure video room setup
    C-->>TM: 3. Provides video room link/details
    TM-->>D: 4. Displays "Join Call" button

    P->>P: 5. Patient logs into Patient Portal
    P->>TM: 6. Clicks "Join Call" for appointment
    TM->>C: 7. Connects patient to video room
    C-->>P: 8. Patient joins video call

    D->>C: 9. Doctor joins video call
    C->>C: 10. Handles video/audio stream for D & P
    D<-->>P: 11. Secure Video Consultation

    D->>TM: 12. Doctor ends call
    TM->>C: 13. Notifies call ended
    C-->>TM: 14. Confirms call ended
    TM->>TM: 15. Updates appointment status (e.g., "completed")
```

**Step-by-step Explanation:**

1.  **Doctor Initiates:** The doctor, from within their OpenEMR interface, sees a scheduled telehealth appointment for Jane and clicks a "Launch" button.
2.  **Module Requests Room:** The Telehealth Module tells the Comlink Telehealth Service, "Hey, I need a secure video room for this appointment!"
3.  **Room Ready:** Comlink sets up the secure room and gives the Telehealth Module the details (like a unique ID for the room).
4.  **Doctor Sees Button:** The Telehealth Module then displays a "Join Call" button for the doctor, which will take them into that specific room.
5.  **Patient Logs In:** Jane logs into her [Patient Portal](01_patient_portal_.md).
6.  **Patient Joins:** She sees her upcoming appointment and clicks a similar "Join Call" button.
7.  **Patient Connects:** The Telehealth Module connects Jane's web browser directly to the Comlink Telehealth Service's video room.
8.  **Patient in Call:** Jane is now in the virtual room.
9.  **Doctor Joins:** The doctor clicks their button and also joins the same virtual room.
10. **Comlink Handles Communication:** The Comlink service manages all the video and audio streams between them, ensuring it's secure.
11. **Consultation:** The virtual appointment happens!
12. **Doctor Ends Call:** When the doctor ends the call in OpenEMR.
13. **Module Notifies Service:** The Telehealth Module tells Comlink the call is over.
14. **Service Confirms:** Comlink confirms.
15. **Status Update:** OpenEMR, through the Telehealth Module, automatically updates Jane's appointment status, making it easy for the clinic to track virtual visits.

## A Glimpse at the Code: Launching a Telehealth Session

The Telehealth Module mainly lives in `interface/modules/custom_modules/oe-module-comlink-telehealth/`. Let's look at `public/assets/js/telehealth-calendar.js`, which handles the "Launch" button on the calendar.

#### `telehealth-calendar.js`: The Calendar's Launch Logic

This file contains the logic that allows you to start a telehealth session directly from the OpenEMR calendar. It checks if the appointment is ready and then kicks off the video call.

```javascript
// From interface/modules/custom_modules/oe-module-comlink-telehealth/public/assets/js/telehealth-calendar.js (simplified)

// This function is called when a provider clicks the 'launch' button on the calendar.
function sendToEncounter(evt) {
    // Get the appointment ID from the button's data
    let pc_eid = evt.target.dataset['eid'];

    // Call a function to set the current patient encounter in OpenEMR
    return setCurrentEncounterForAppointment(pid, pc_eid)
        .then(encounterData => {
            // Once the encounter is set, launch the video message for the provider
            loadEncounterFromEncounterData(encounterData, pid, pc_eid);
        })
        .catch(error => {
            // If something goes wrong, show an error message
            alert(translations.SESSION_LAUNCH_FAILED);
            console.error(error);
        });
}

// This function (further simplified) would tell OpenEMR to get ready for the encounter
function setCurrentEncounterForAppointment(pid, appointmentId) {
    // This makes a network request to OpenEMR's backend to prepare for the appointment
    return window.fetch(moduleLocation + 'public/index.php?action=set_current_appt_encounter&pc_eid=' + encodeURIComponent(appointmentId));
    // ... handles response ...
}

// This function (further simplified) actually launches the video call for the provider
function loadEncounterFromEncounterData(encounterData, pid, pc_eid) {
    // It updates the OpenEMR top frame to show the patient's chart
    window.top.RTop.location = '../../patient_file/encounter/encounter_top.php?set_pid=' + encodeURIComponent(pid)
        + '&set_encounter=' + encodeURIComponent(encounterData.selectedEncounter.id) + '&launch_telehealth=1';

    // It then tries to launch the provider's video message through the main 'comlink' object
    if (window.top.comlink && window.top.comlink.telehealth && window.top.comlink.telehealth.launchProviderVideoMessage) {
        window.top.comlink.telehealth.launchProviderVideoMessage({
            pc_eid: pc_eid
        });
    } else {
        console.error("launchProviderVideoMessage was not found in top window object");
        alert(translations.SESSION_LAUNCH_FAILED);
    }
}

// ... Initialization code that finds the launch buttons and attaches 'sendToEncounter' ...
```
**Explanation:** The `sendToEncounter` function is triggered when a doctor clicks the "Launch" button on a calendar appointment. It first calls `setCurrentEncounterForAppointment` to tell OpenEMR which patient's chart needs to be active. After that's done, `loadEncounterFromEncounterData` is called. This function navigates the doctor's OpenEMR view to the correct patient chart and, importantly, calls `window.top.comlink.telehealth.launchProviderVideoMessage`. This is the direct command that tells the main Telehealth (Comlink) application to start the video call for the doctor.

#### `telehealth.js`: The Core Launch Function

Now, let's peek into `public/assets/js/src/telehealth.js`, which is the main "engine" for the telehealth module. This file contains the `launchProviderVideoMessage` function that `telehealth-calendar.js` calls.

```javascript
// From interface/modules/custom_modules/oe-module-comlink-telehealth/public/assets/js/src/telehealth.js (simplified)

// This function launches the video call for providers.
function launchProviderVideoMessage(data) {
    // 'conferenceRoom' is a variable that holds the current video call instance.
    // If a call is already active, it warns the user.
    if (conferenceRoom) {
        if (conferenceRoom.inSession) {
            alert(translations.DUPLICATE_SESSION);
            return;
        }
        else {
            // If a previous session exists but isn't active, destroy it first.
            conferenceRoom.destruct();
            conferenceRoom = null;
        }
    }

    // Create a new ConferenceRoom object. This is the main class that manages the video call.
    conferenceRoom = new ConferenceRoom(comlink.settings.apiCSRFToken, comlink.settings.features,
        translations, getTeleHealthScriptLocation(false)); // 'false' indicates this is for a provider.

    // Initialize the conference room with the appointment data.
    conferenceRoom.init(data);
}

// This function is also part of the main Comlink object and handles patient side.
function showPatientPortalDialog(appointmentEventId) {
    let telehealthSessionData = { pc_eid: appointmentEventId };
    let csrfToken = comlink.settings.apiCSRFToken;

    // Creates a PatientConferenceRoom, which is specialized for patients.
    conferenceRoom = new PatientConferenceRoom(csrfToken, comlink.settings.features,
        translations, getTeleHealthScriptLocation(true)); // 'true' indicates this is for a patient.

    conferenceRoom.init(telehealthSessionData);
}

// The main 'comlink' object where these functions are exposed.
comlink.telehealth = {
    showPatientPortalDialog: showPatientPortalDialog,
    launchProviderVideoMessage: launchProviderVideoMessage,
    // ... other telehealth related functions ...
};
```
**Explanation:** The `launchProviderVideoMessage` function is the central point for providers to start a video call. It first checks if a call is already ongoing to prevent conflicts. Then, it creates a new `ConferenceRoom` object. This `ConferenceRoom` object encapsulates all the complex logic of managing the video call itself (connecting to the Comlink service, handling video/audio, etc.). It's initialized with data about the appointment, and then the video session begins! The `showPatientPortalDialog` is a similar entry point, but it creates a `PatientConferenceRoom` adapted for the patient's simpler interface.

## Conclusion

The Telehealth Module is a powerful addition to OpenEMR, enabling secure and integrated virtual consultations. By leveraging the underlying Comlink Telehealth service, it seamlessly integrates video conferencing into the existing patient management and scheduling workflows. This allows both patients and providers to connect efficiently, anytime, anywhere.

In the next chapter, we'll dive into the world of **RESTful APIs (OpenEMR and FHIR)**, which are the fundamental communication methods that allow different parts of OpenEMR (like the Patient Portal and Telehealth Module) to talk to each other, and also for OpenEMR to talk to other systems.

[Next Chapter: RESTful APIs (OpenEMR and FHIR)](03_restful_apis__openemr_and_fhir__.md)

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)