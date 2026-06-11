# **System Architecture & Development Brief: Cat Show Judging System**

## **1\. Project Overview**

This project is a real-time administration and synchronization system for cat shows. The system manages the judging queue, synchronizes state across multiple client types (Admin, Judges, and Public Displays), and is highly resilient to unstable Wi-Fi networks in large exhibition halls.

## **2\. Tech Stack**

- **Frontend & API:** Nuxt 4 (Vue 3, Composition API), server routes (Nitro) for standard HTTP requests.
- **Styling:** Tailwind CSS (designed for responsiveness from iPads to large TV screens).
- **Database:** PostgreSQL.
- **Real-time Engine:** Nuxt 4 with a dedicated FastAPI socket server for real-time updates.

## **3\. Core Database Schema (PostgreSQL)**

The data model revolves around judges, cats, and the dynamic judging queue.

SQL

\-- Judges / Rings

CREATE TABLE judges (

id SERIAL PRIMARY KEY,

name VARCHAR(255) NOT NULL,

ring_number INT UNIQUE NOT NULL,

current_catalog_number INT,

current_class VARCHAR(50),

status VARCHAR(50) DEFAULT 'active' -- active, paused, finished

);

\-- Cats / Entries

CREATE TABLE cats (

id SERIAL PRIMARY KEY,

catalog_number INT UNIQUE NOT NULL,

name VARCHAR(255) NOT NULL,

breed VARCHAR(50) NOT NULL,

color_code VARCHAR(50),

class VARCHAR(50) NOT NULL,

status VARCHAR(50) DEFAULT 'present' -- present, absent, judged

);

\-- Judging Queue (Mapping cats to judges in a specific order)

CREATE TABLE judge_queue (

id SERIAL PRIMARY KEY,

judge_id INT REFERENCES judges(id) ON DELETE CASCADE,

cat_id INT REFERENCES cats(id) ON DELETE CASCADE,

sequence_order INT NOT NULL,

status VARCHAR(50) DEFAULT 'pending', -- pending, ongoing, completed, skipped

UNIQUE(judge_id, sequence_order)

);

## **4\. User Roles and Interfaces**

| **Role / Device**                         | **Core Functionality**                                                                                                                     | **UI / UX Guidelines**                                                                           |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| **Secretariat**<br><br>_(Laptop/Desktop)_ | Master control. Manage entries, mark cats as "absent" (struken), reassign classes, and trigger global events (like "Best in Show" panels). | Information-dense, search-heavy dashboard. Fast toggles for status changes.                      |
| ---                                       | ---                                                                                                                                        | ---                                                                                              |
| **Judge**<br><br>_(iPad / Tablet)_        | Progress the queue. View current cat details (#, breed, class), click "Next Cat", or pause the ring. View the next 3 upcoming cats.        | Extremely minimalist. Huge touch targets. No clutter. Prominent offline/online status indicator. |
| ---                                       | ---                                                                                                                                        | ---                                                                                              |
| **Display**<br><br>_(TV Screen)_          | Read-only public view. Displays all active rings in a grid (Current Cat, Next Cat, Class, Judge Name).                                     | Readable from 10 meters away. Auto-scrolling if there are too many rings to fit on one screen.   |
| ---                                       | ---                                                                                                                                        | ---                                                                                              |

## **5\. Architectural Rules & Network Resilience**

The exhibition hall environment will have flaky Wi-Fi. The agent must implement the following resilience patterns:

- **Optimistic UI Updates (Judges):** When a judge clicks "Next Cat", the UI must update instantly. The API call should happen in the background.
- **Offline Outbox Pattern:** If the judge's iPad loses connection, queue the state changes in localStorage or IndexedDB. When navigator.onLine becomes true or WebSockets reconnect, flush the queue to the server.
- **State Reconciliation:** WebSockets drop packets during micro-disconnects. Whenever a WebSocket connection is (re)established (onopen), the client MUST immediately perform a standard HTTP GET request to fetch the absolute latest state from the database to overwrite any missed WebSocket events.
- **Event-Driven Real-time:** Do not put heavy logic in the WebSocket payload. The WebSocket should simply broadcast lightweight events (e.g., CAT_STATUS_UPDATED, RING_PROGRESSED). The clients hear this, and update their local state accordingly.

## **6\. Initial Implementation Steps for the Agent**

- Initialize the Nuxt 4 project and configure Tailwind CSS.
- Set up the database connection and run the initial schema migrations.
- Create the base layout structure (default.vue for admin, display-layout.vue for TVs).
- Scaffold the basic CRUD API routes for Cats and Judges.
- Build out the three core views (Admin dashboard, Judge iPad view, TV Display grid) using static dummy data first to nail the responsive layouts.

---

## Session Summary (2026-06-10)

### Done
- **Btn.vue** — shared button component with `variant` (primary/secondary/outline), `size` (normal/small), optional `icon` (Lucide component), `disabled`, `href`. Styles: primary = `bg-black text-white rounded-full`, secondary = `bg-gray-700 text-white`, outline = `border-2 border-black`. All sizes: `rounded-full font-mono uppercase font-bold`.
- **Button replacement** — All `<button>` elements across admin pages replaced with `<Btn>`: `ConfirmDialog.vue`, `login.vue`, `admin/judges.vue`, `admin/cats/index.vue`, `admin/shows/index.vue`, `admin/shows/[id]/index.vue`, `admin/shows/[id]/days/[dayId].vue`, `RingCard.vue`, `ShowCatsTable.vue`, `BreedCategoryManager.vue`, `CsvImportModal.vue`, `RingAssigner.vue`. NuxtLinks with button styling also converted to `<Btn :href="...">`.
- **`.small-button` CSS class** — removed from `main.css` (replaced by `<Btn size="small">`).
- **Stat card colors** — still pending (blue/green/indigo/purple icon backgrounds on `admin/index.vue`).
- **Tab dropdown** — still pending (secondary actions collapse on show detail page).

### Pending
- Color consolidation on `admin/index.vue` stat cards (`bg-blue-100` → `bg-gray-100`, etc.)
- Add `...` dropdown for secondary actions on show detail page header