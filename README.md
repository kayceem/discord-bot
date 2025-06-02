
## Discord Scheduler Bot – Setup Guide (Windows)

This bot sends scheduled race alerts to a Discord channel by reading a CSV file and running at a specified time daily. You can install it easily using our PowerShell script or set it up manually.

---

## Option 1: Automatic Setup (Recommended)

### Requirements

* Windows 10/11
* Python

---

### Steps to Use the Auto Setup Script

1. **Download the Project Files**

   * Clone the repo or download it as ZIP and extract to a folder, e.g., `C:\DiscordSchedulerBot`

2. **Open PowerShell as Administrator**

   * Right-click the Start menu → **Windows PowerShell (Admin)**

3. **Run the Setup Script**

   ```powershell
   cd "C:\DiscordSchedulerBot"
   .\setup.ps1
   ```

4. **Follow the Prompts**

   * Enter the time to schedule the bot (e.g., `10:00AM`)
   * The script will:

     * Create a virtual environment
     * Install required dependencies
     * Schedule the task to run daily
     * Ensure only one instance runs at a time

5. You're done! The bot will run every day at the time you provided.

---

## Option 2: Manual Setup


### Step 1: Install Python

* Download from [python.org/downloads](https://www.python.org/downloads/)
* During install, **check the box: "Add Python to PATH"**

---

### Step 2: Set Up the Project

1. **Open PowerShell**

2. Navigate to the project folder:

   ```powershell
   cd "C:\DiscordSchedulerBot"
   ```

3. **Create a Virtual Environment**

   ```powershell
   python -m venv venv
   ```

4. **Install Dependencies**

   ```powershell
   .\venv\Scripts\pip install -r requirements.txt
   ```

---

### Step 3: Configure Environment Variables

Create a file named `.env` in the project folder with the following:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=123456789012345678
ALERT_THRESHOLD=10
TIMEZONE=Australia/Sydney
```

---

### Step 4: Test the Bot

```powershell
.\venv\Scripts\python.exe main.py
```

---

### Step 5: Schedule the Task Manually

1. Open **Task Scheduler**

2. Click **"Create Task"**

3. Under **General Tab:**

   * Name: `DiscordSchedulerBot`
   * Run with highest privileges
   * Configure for Windows 10 or later

4. **Trigger Tab:**

   * Add a new Daily trigger at desired time

5. **Action Tab:**

   * Program/script:
     `C:\DiscordSchedulerBot\venv\Scripts\python.exe`
   * Add arguments:
     `"C:\DiscordSchedulerBot\main.py"`
   * Start in:
     `C:\DiscordSchedulerBot`

6. **Settings Tab:**

   * Check “**If the task is already running, stop the existing instance**”

---

## Logs

* Logs are saved in logs folder in  the project folder.
* To reschedule or remove the task, open **Task Scheduler** > **Task Library**.

---
