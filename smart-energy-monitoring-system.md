# Smart Energy Monitoring & Power Saving System
### Build Documentation — Hostels, PGs, Colleges & Universities

---

## 1. What You Are Building

A hybrid energy monitoring platform that combines one whole-building energy meter with a few smart plugs on heavy appliances, feeds all that data into a Python backend, stores it in PostgreSQL, and displays it on a live React dashboard. The software is entirely yours. The hardware is prebuilt and off-the-shelf.

The system answers three questions at any given moment:
- How much electricity is the entire building consuming right now?
- How much of that are the known heavy appliances consuming?
- What is everything else consuming (unknown/background loads)?

It then uses that data to detect spikes, estimate electricity bills, flag wastage, and give administrators actionable alerts.

---

## 2. System Architecture Overview

The system has four layers. Each layer has one job and passes its output to the next.

**Sensing Layer** — Physical hardware that measures electricity and sends numbers over WiFi.

**Communication Layer** — APIs or local network calls that carry those numbers from the hardware into your backend.

**Processing Layer** — Your Python backend that polls the hardware, stores readings, runs analysis, and serves data to the frontend.

**Presentation Layer** — Your React dashboard that displays live graphs, alerts, breakdowns, and reports.

---

## 3. Hardware Setup

### 3.1 What to Buy

**One WiFi-enabled DIN Rail Energy Meter with CT Clamp**
- Installed at the main electrical distribution panel of the building
- Measures total voltage, current, active power (kW), and energy consumed (kWh) for the whole building
- Communicates over WiFi
- Must be a Tuya Smart certified device so API access is available
- This is the most important piece of hardware in your system

**Two to Three TP-Link Tapo P110 Smart Plugs**
- Each plugged into one heavy appliance — AC unit, geyser, or industrial heater
- Measures real-time power draw of that specific appliance
- Communicates over local WiFi — no internet dependency for data access
- The Tapo P110 exposes a local LAN API so your backend talks directly to it without going through TP-Link's servers

### 3.2 What Each Hardware Component Gives You

| Hardware | Data It Provides |
|---|---|
| DIN Rail Energy Meter | Total building kW, kWh, voltage, current |
| Tapo P110 (×2 or ×3) | Per-appliance kW, kWh, on/off state |

### 3.3 Installation Notes

The DIN Rail meter requires installation inside the electrical distribution board. An electrician must do this. The CT clamp wraps around the main live wire — no cutting of wires is involved. This takes under an hour.

The smart plugs are plug-and-play. Connect them to the same WiFi network as your backend server.

### 3.4 Network Requirement

All hardware must be on the same local WiFi network as the machine running your backend. This ensures that Tapo local API calls work without depending on the internet. The Tuya meter will still need internet to reach Tuya's cloud unless you configure a local Tuya integration.

---

## 4. Communication Strategy

### 4.1 Tuya Energy Meter — How Data Reaches Your Backend

Tuya devices send data to Tuya's cloud. Your backend communicates with Tuya's IoT Platform using their API. The free tier of Tuya's IoT Platform is sufficient for a pilot deployment at a hostel or college building. You register your device on the Tuya IoT Platform, obtain API credentials, and your backend uses those credentials to fetch real-time device data.

Tuya provides device status including power, current, voltage, and cumulative energy as structured data your backend can parse directly.

### 4.2 Tapo P110 — How Data Reaches Your Backend

The Tapo P110 exposes a local HTTP API on your WiFi network. Your backend sends a request to the plug's local IP address and receives real-time power and energy data in response. No Tapo cloud account is needed for this. No API key is needed. It is entirely local.

This makes Tapo the simpler and more reliable of the two data sources because there is no external dependency.

### 4.3 Polling Frequency

Your backend polls both sources every 5 to 10 seconds. This is frequent enough for live dashboard updates and spike detection without overwhelming the hardware or API rate limits.

---

## 5. Backend — Python + FastAPI

### 5.1 Responsibilities

The backend has four distinct responsibilities:
1. Poll hardware APIs on a fixed schedule and collect raw readings
2. Store every reading in PostgreSQL with a precise timestamp
3. Run analysis on stored data to produce insights, alerts, and summaries
4. Serve processed data to the React frontend via REST endpoints and a live SSE stream

### 5.2 Module Structure

**Poller Module**
Runs on a background schedule using APScheduler. Every 5 to 10 seconds it calls the Tuya API for the main meter reading and calls each Tapo plug's local API for its appliance reading. Packages each reading with a timestamp and device identifier and hands it to the storage module.

**Storage Module**
Receives readings from the poller and writes them into PostgreSQL. Each row in the readings table contains a timestamp, device ID, power in watts, current in amps, voltage in volts, and energy in kWh. This module also handles database connection management and any write errors.

**Analysis Engine**
This is the brain of your backend. It queries PostgreSQL for recent readings and computes the following:

- *Unknown Load* — Total building power minus the sum of all known smart plug readings. This tells you what background loads are consuming.
- *Average Usage* — Rolling average of power consumption over the last hour, day, or week.
- *Spike Detection* — If the current reading exceeds the rolling average by a configurable threshold (for example 50%), a spike is flagged.
- *Bill Estimation* — Cumulative kWh is converted to a rupee amount using India's electricity slab rates. Slabs are configurable per state.
- *Peak Hours* — Analysis of which hours of the day consistently show the highest consumption.
- *Appliance Runtime* — How many hours each plugged appliance has been running in a given day.

**Alert Engine**
Reads the output of the analysis engine and generates alert objects when thresholds are crossed. Alert types include: consumption spike, high overnight usage, appliance left on for too long, and projected bill crossing a set limit. Alerts are stored in a separate alerts table with a timestamp, type, severity, and message.

**API Layer**
FastAPI routes that the React frontend calls. Key endpoints include:
- Current live readings for all devices
- Historical readings for a given device and time range
- Computed daily, weekly, and monthly summaries
- Active and historical alerts
- Bill estimate for the current billing cycle
- Unknown load calculation for the current moment

**SSE Endpoint**
A single Server-Sent Events endpoint that streams the latest readings to the frontend every 5 to 10 seconds. The frontend connects once and receives a continuous stream of updates without polling. This powers the live graph on the dashboard.

### 5.3 Scheduled Jobs

Beyond the hardware poller, the backend runs two additional scheduled jobs:

- *Hourly Summary Job* — Aggregates the last hour's readings into a single summary row. This keeps the readings table from growing too large while preserving historical data.
- *Daily Report Job* — Computes a full day's summary at midnight: total kWh, peak hour, total estimated cost, and any alerts that fired during the day.

### 5.4 Configuration

All configurable values are stored in a single configuration file — not hardcoded into logic. This includes polling frequency, spike detection threshold, electricity slab rates, device IP addresses, Tuya API credentials, and database connection string. When deploying at a new building, only this file needs to change.

---

## 6. Database — PostgreSQL

### 6.1 Core Tables

**readings**
Stores every raw reading from every device. Columns: reading ID, device ID, timestamp, power (watts), current (amps), voltage (volts), energy (kWh). This table grows continuously. Older rows are periodically summarized and compressed.

**devices**
One row per hardware device. Columns: device ID, device name, device type (main meter or smart plug), location label (for example Floor 1, Room 12 AC), IP address or Tuya device ID, active status.

**hourly_summaries**
One row per device per hour. Columns: device ID, hour timestamp, average power, max power, min power, total kWh for that hour. Used for historical graphs and trend analysis.

**daily_summaries**
One row per device per day. Columns: device ID, date, total kWh, peak hour, average power, estimated cost in rupees.

**alerts**
One row per alert event. Columns: alert ID, timestamp, device ID, alert type, severity, message, acknowledged status.

### 6.2 Data Retention Strategy

Raw readings are kept for 7 days. After that, the hourly summaries carry the historical picture. Daily summaries are kept indefinitely. This prevents the database from growing unmanageable over months of operation.

---

## 7. Frontend — React + Recharts + Tailwind CSS

### 7.1 Responsibilities

The frontend has one job: take the data served by the backend and make it immediately understandable to a hostel warden, college facilities manager, or administrator. It does not do any analysis. All numbers it shows are computed by the backend.

### 7.2 Pages and Views

**Live Dashboard (Home Page)**
The primary screen. Shows the current moment's state of the building. Contains:
- Total building power right now in kW (large, prominent number)
- Breakdown: known appliances combined vs unknown/background loads
- Per-appliance current power draw (one card per smart plug)
- A live line graph of the last 30 minutes of total power, updating via SSE every few seconds
- Active alerts displayed as banners at the top of the page
- Current estimated bill for this billing cycle in rupees

**Historical Analysis Page**
Lets the administrator explore past consumption. Contains:
- Date range selector
- Line graph of daily kWh over the selected range
- Bar chart comparing consumption by day of week
- Table of daily summaries with kWh and estimated cost per day
- Ability to filter by individual device

**Appliance Breakdown Page**
Focus on smart plug data. Contains:
- Per-appliance daily kWh for the current week
- Runtime hours per appliance per day
- Comparison of each appliance's share of total known consumption
- Trend line per appliance over the past 30 days

**Alerts Page**
Full log of all alerts. Contains:
- List of all alerts sorted by timestamp newest first
- Filter by alert type and severity
- Mark as acknowledged button
- Unacknowledged alert count shown as a badge in the navigation

**Bill Estimator Page**
Focused on cost. Contains:
- Current month's kWh so far
- Projected kWh by end of month based on current trend
- Estimated bill in rupees using slab calculation
- Month-over-month comparison for the last 6 months
- Configurable slab rates so the admin can update them if the electricity board changes pricing

**Settings Page**
For administrator configuration. Contains:
- Device list with labels and locations
- Polling frequency setting
- Spike detection threshold setting
- Electricity slab rate editor
- Alert notification preferences

### 7.3 Real-Time Behaviour

The dashboard connects to the backend's SSE endpoint on page load and keeps the connection open. Every time the backend sends a new data point, the live graph updates, the current power number updates, and any new alerts appear as banners — all without the user refreshing the page.

### 7.4 Design Principles

The UI is built for administrators, not engineers. Every number is labelled clearly. Graphs have axis labels and units. Alerts use plain language — not error codes. The colour system uses green for normal, amber for moderate, and red for high or critical consumption states. The layout is responsive so it works on both a laptop and a tablet mounted on a wall in a hostel office.

---

## 8. Data Flow — End to End

This is the complete journey of one reading from hardware to screen:

1. APScheduler triggers the poller every 5 seconds
2. Poller calls Tuya API for the main meter and Tapo local API for each plug
3. Raw readings are received and passed to the storage module
4. Storage module writes each reading to the readings table in PostgreSQL with the current timestamp
5. Analysis engine is triggered and computes unknown load, checks for spikes, updates rolling averages
6. If a spike is detected, the alert engine writes a new row to the alerts table
7. The SSE endpoint packages the latest readings and analysis output and pushes it to all connected frontend clients
8. The React frontend receives the SSE update and re-renders the live graph, the current power number, and any new alert banners

---

## 9. Deployment (For Pilot at a Hostel or College)

### 9.1 Where to Run the Backend

Run the backend on a dedicated machine that stays on 24 hours — a Raspberry Pi 4, an old laptop, or a small desktop PC on the hostel's network. This machine must be on the same WiFi network as the hardware. It does not need a public IP address for a local-only pilot.

### 9.2 Where to Run the Frontend

For a pilot, the React frontend can be served by the same machine as the backend. The administrator accesses it through a browser on any device connected to the same local network using the machine's local IP address.

### 9.3 Database

PostgreSQL runs on the same machine as the backend for a pilot. For a production deployment serving multiple buildings, move PostgreSQL to a dedicated server or managed cloud database.

---

## 10. Build Order — What to Build First

Build in this sequence. Each step produces something testable before moving to the next.

**Step 1 — Database Setup**
Create the PostgreSQL database. Define all tables. Verify that you can insert and query rows correctly.

**Step 2 — Device Communication**
Write the poller for the Tapo P110 first (simpler, local). Verify you can fetch a real power reading. Then write the Tuya poller and verify it returns meter data.

**Step 3 — Data Storage**
Connect the poller output to the storage module. Verify readings are appearing in the database with correct timestamps.

**Step 4 — Analysis Engine**
Build unknown load calculation first. Then spike detection. Then bill estimation. Test each calculation against manually verified numbers.

**Step 5 — REST API**
Build the FastAPI endpoints one by one. Test each with a tool like Postman before moving to the next.

**Step 6 — SSE Endpoint**
Build the SSE stream. Verify a simple HTML client can receive updates every 5 seconds.

**Step 7 — React Dashboard**
Build the live dashboard page first. Connect it to the SSE stream. See numbers updating live. Then build remaining pages.

**Step 8 — Alerts**
Add the alert engine and wire alerts into the frontend banners and the alerts page.

**Step 9 — Polish**
Add the bill estimator page, historical graphs, settings page, and responsive layout.

**Step 10 — Pilot Deployment**
Deploy on the hostel or college network. Run for one week. Collect real data. Verify the analysis output matches ground truth (compare kWh with the actual electricity meter reading).

---

## 11. What Success Looks Like

At the end of the build, a hostel warden sitting at a desk should be able to:

- Open a browser and see the building's live power consumption updating every few seconds
- See that the two ACs together are consuming 3.2 kW and everything else is consuming 1.8 kW
- See a red alert banner saying consumption spiked 60% above average at 11 PM last night
- Click through to see the last 30 days of daily kWh and identify that weekends consistently consume 40% more than weekdays
- See that this month's projected bill is ₹8,400 and last month was ₹6,200
- Change the spike detection threshold from 50% to 40% in the settings page without touching any code

That is the complete system.
