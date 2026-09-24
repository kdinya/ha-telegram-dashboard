# Telegram Dashboard Documentation

## Setup & Configuration

1. **Get Telegram Bot Token:**
   - Message `@BotFather` on Telegram.
   - Run `/newbot` and follow instructions.
   - Copy the HTTP API token into the add-on configuration tab.

2. **Access Control (RBAC):**
   - Open the Telegram Dashboard Ingress panel.
   - Under the **Users** tab, register family members by Telegram User ID.
   - Assign roles:
     - `Admin`: Full access, including system reboot, PC commands, valve control.
     - `Member`: Climate, media, lighting, standard sensors.
     - `Guest`: Read-only view for selected sensors.

3. **Menu Customization:**
   - Use the visual editor to rearrange sections, add items, set alert thresholds, and customize icons.
