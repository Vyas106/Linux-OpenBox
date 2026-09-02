#!/usr/bin/env python3
"""
greeting.py - Dynamic greeting & companion message generator for Conky
Generates time-aware greetings and rotates through 25+ dynamic messages.
Adheres to the minimal modern monochrome black & white aesthetic.
"""

import sys
import time
import textwrap
from datetime import datetime

# ----------------------------------------------------------------------
# Message Database: 25+ dynamic companion messages categorized by time
# and general productivity / workflow prompts.
# ----------------------------------------------------------------------
MORNING_MESSAGES = [
    "Hello Sir, what task today we gone do?",
    "Hello Sir, ready to conquer today's objectives?",
    "Morning clarity is our secret weapon. Let's make it count, Sir.",
    "Fresh start, sharp mindset. What shall we build first today?",
    "All background daemons online. Ready for your command, Sir.",
    "Plan today's top 3 milestones and let's execute flawlessly.",
    "Good morning Sir! A new day to write clean, impactful code.",
]

AFTERNOON_MESSAGES = [
    "Hello Sir, how is your workflow going so far?",
    "Midday checkpoint: Halfway through our mission today.",
    "Stay hydrated and keep the coding momentum rolling, Sir.",
    "Deep focus mode engaged. Crushing tasks one by one.",
    "What's the next major milestone for this afternoon, Sir?",
    "Reviewing progress: Steady, disciplined execution wins.",
    "Afternoon session: Let's turn complex problems into elegant solutions.",
]

EVENING_MESSAGES = [
    "Hello Sir, how was your day?",
    "Wrapping up today's work or pushing the final commit, Sir?",
    "Great effort today, Sir. Solid progress logged across all tasks.",
    "Time to review what we accomplished and plan ahead for tomorrow.",
    "Evening checkpoint: Another productive day in the books, Sir.",
    "Reflecting on today's progress: Every step forward is a victory.",
    "Hello Sir, system is standing by if you have any evening tasks.",
]

NIGHT_MESSAGES = [
    "Late night coding session, Sir? Remember to rest your eyes.",
    "Quiet hours, maximum focus. Distractions are at absolute zero.",
    "Burning the midnight oil, Sir. Stay inspired and focused.",
    "Deep night productivity in progress. Don't forget to sleep soon.",
    "Night shift mastery: Turning visionary ideas into reality, Sir.",
    "Late night focus mode active. Keep hydrated and comfortable, Sir.",
]

GENERAL_MESSAGES = [
    "Discipline equals freedom. Every keystroke brings mastery, Sir.",
    "One clean commit at a time. Quality and simplicity over everything.",
    "Need a quick break, Sir? A short stretch sharpens the mind.",
    "System health optimal: Arch Linux running lean, fast, and quiet.",
    "Small consistent daily habits create extraordinary results, Sir.",
    "Stay relentless in your pursuit of excellence, Sir.",
    "The terminal is ready. What's on your agenda right now, Sir?",
    "Clean code, clean architecture, unstoppable progress.",
    "Focus on the highest leverage task right now, Sir.",
    "Automate the repetitive work, unleash your creative brilliance.",
    "Your desktop environment is distraction-free and primed for focus.",
    "Hello Sir, I'm standing by whenever you need assistance.",
]

def get_time_period(hour):
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 22:
        return "evening"
    else:
        return "night"

def get_header_greeting(hour):
    if 5 <= hour < 12:
        return "GOOD MORNING, SIR", "󰖙"
    elif 12 <= hour < 17:
        return "GOOD AFTERNOON, SIR", "󰖙"
    elif 17 <= hour < 22:
        return "GOOD EVENING, SIR", "󰖔"
    else:
        return "LATE NIGHT, SIR", "󰖔"

def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "--message"
    now = datetime.now()
    hour = now.hour
    period = get_time_period(hour)
    
    if arg == "--header":
        title, icon = get_header_greeting(hour)
        print(f"{icon}  {title}")
        return

    if arg == "--date":
        print(now.strftime("%A, %d %B"))
        return

    # Default: --message
    if period == "morning":
        period_pool = MORNING_MESSAGES
    elif period == "afternoon":
        period_pool = AFTERNOON_MESSAGES
    elif period == "evening":
        period_pool = EVENING_MESSAGES
    else:
        period_pool = NIGHT_MESSAGES
    
    # Combined pool ensuring time-relevant messages rotate frequently with general pool
    combined_pool = period_pool + GENERAL_MESSAGES
    
    # Cycle every 20 seconds smoothly based on epoch timestamp
    epoch_seconds = int(time.time())
    index = (epoch_seconds // 20) % len(combined_pool)
    current_message = combined_pool[index]
    
    # Format message with wrapping (up to 56 chars per line for wider box)
    wrapped_lines = textwrap.wrap(current_message, width=56)
    if not wrapped_lines:
        wrapped_lines = [current_message]
    
    # Pad to 2 lines for visual consistency
    if len(wrapped_lines) == 1:
        wrapped_lines.append("")
    
    for line in wrapped_lines:
        print(f"${{color1}}{line}")

if __name__ == "__main__":
    main()
