 AI-powered journaling that creates markdown diary entries with smart prompts,
   automatic backlinks, and background automation.

   -------------------------------------------------------------------------------

   What It Does

   Creates dated diary entries (YYYY-MM-DD.md) in your Obsidian vault with:

     - AI prompts based on your past 3 days
     - Automatic [[backlinks]] between related entries
     - Topic #tags from theme analysis
     - Background auto-linking and weekly reports
     - Todo extraction to planner files

   -------------------------------------------------------------------------------

   Architecture

   Core Library (diary_core/) - Business logic

     - entry_manager.py - Read/write markdown files
     - analysis.py - Extract themes, find related entries (Jaccard similarity >8%)
     - ollama_client.py - Local LLM via HTTP
     - template_generator.py - Generate AI prompts from recent entries
     - config.py - Load .env, validate paths

   CLI (diary_cli/) - Manual commands

     diary create today              # Create entry with AI prompts
     diary link today                # Generate backlinks after writing
     diary analyze 30                # Memory trace report
     diary todos today               # Extract action items
     diary list                      # Show recent entries
     diary themes 7                  # Show recurring themes

   Daemon (diary_daemon/) - Background automation

     diary-daemon start              # Run in background
     diary-daemon stop               # Stop daemon
     diary-daemon status             # Check if running

     - Auto-links entries at 11pm daily
     - Weekly analysis every Sunday
     - Bulk refresh backlinks periodically
     - Runs silently in background

   -------------------------------------------------------------------------------

   Daily Flow

   Morning: Run diary create today to get AI prompts
   Throughout day: Write in Obsidian whenever inspiration strikes
   Evening: Continue writing your full reflection
   11pm (automated): Daemon runs link today, adds [[backlinks]] and #tags
   Sunday (automated): Daemon generates weekly memory trace analysis

   -------------------------------------------------------------------------------

   Entry Structure

     ## Reflection Prompts
     **1. Based on [[2025-01-14]], how did X work out?**

     ---

     ## Brain Dump
     Your writing here...

     ---

     ## Memory Links
     **Temporal:** [[2025-01-14]] • [[2025-01-13]]
     **Topics:** #focus #energy

   -------------------------------------------------------------------------------

   Configuration

   Required in .env:

     DIARY_PATH=/path/to/obsidian/vault
     PLANNER_PATH=/path/to/planner

   Optional:

     OLLAMA_MODEL=llama3.1:latest
     DAEMON_AUTO_LINK_TIME=23:00
     DAEMON_WEEKLY_ANALYSIS=true
     DAEMON_REFRESH_DAYS=30

   -------------------------------------------------------------------------------

   Key Logic

   Calendar-based context: Past 3 calendar days (not last 3 entries)
   Sunday special: 5 weekly prompts instead of 3 daily
   Brain Dump priority: Only links entries with >50 chars actual writing
   Jaccard similarity: Links entries with >8% theme overlap
   Smart prompts: Recent entries weighted more heavily

   -------------------------------------------------------------------------------

   Dependencies

     - Python 3.13+, httpx, python-dotenv
     - Click or Typer (CLI), Rich (output)
     - APScheduler (daemon scheduling)
     - Ollama with llama3.1:latest

   -------------------------------------------------------------------------------

   Implementation Plan

   Phase 1: Extract core logic, build CLI commands, test all features
   Phase 2: Basic daemon with auto-linking at 11pm
   Phase 3: Weekly analysis automation, bulk refresh scheduling
   Phase 4: Polish CLI output, add progress indicators

   -------------------------------------------------------------------------------

   Why This Design

     - Obsidian stays primary interface (graph view, mobile, sync)
     - CLI for quick manual tasks and scripting
     - Daemon handles repetitive tasks in background
     - Local markdown files (portable, private, future-proof)
     - Local AI via Ollama (no cloud, no API costs)
