# Deep Dip 2 Player Monitor

Monitors the Trackmania player **fajoogaloo** on the Deep Dip 2 map and sends notifications when they reach floor 15 (1938 meters).

## How It Works

- **Monitoring Script**: `monitor_player.py` fetches player data from the Deep Dip 2 API every 10 minutes
- **Target**: Player `fajoogaloo`
- **Alert Threshold**: Floor 15 at 1938 meters
- **Schedule**: Runs automatically via GitHub Actions every 10 minutes

## Setup

### Prerequisites

- Python 3.11+
- GitHub repository with Actions enabled

### Local Testing

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the monitoring script:
   ```bash
   python monitor_player.py
   ```

### GitHub Actions

The workflow is configured in `.github/workflows/monitor.yml` and runs automatically every 10 minutes.

You can also trigger it manually:
1. Go to the "Actions" tab in your GitHub repository
2. Select "Monitor Deep Dip 2 Progress"
3. Click "Run workflow"

## Notification Setup (Discord)

This project uses **Discord webhooks** for notifications. When fajoogaloo reaches floor 15, you'll receive a Discord notification with an embedded message showing the achievement.

### Setting Up Discord Notifications

1. **Create a Discord webhook:**
   - Open your Discord server
   - Right-click the channel you want notifications in (e.g., #dd2-alerts)
   - Click **Integrations** → **Webhooks** → **New Webhook**
   - Copy the webhook URL

2. **Add webhook to GitHub:**
   - Go to your repository **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: Paste your webhook URL
   - Click **Add secret**

3. **Done!** When floor 15 is reached, you'll get a notification like:
   ```
   @everyone
   🎉 FLOOR 15 REACHED! 🎉
   fajoogaloo has reached floor 15 in Deep Dip 2!
   Height Achieved: 1938m+
   Floor 15 Threshold: 1938m
   ```

---

## Alternative Notification Options

If you prefer a different notification method, here are some alternatives:

### Option 1: Discord Webhook
```yaml
- name: Send Discord notification
  if: steps.check_notification.outputs.floor_15_reached == 'true'
  run: |
    curl -H "Content-Type: application/json" \
         -d '{"content":"🎉 fajoogaloo has reached floor 15 in Deep Dip 2!"}' \
         ${{ secrets.DISCORD_WEBHOOK_URL }}
```

**Setup**:
1. Create a Discord webhook in your server settings
2. Add it as a repository secret: `DISCORD_WEBHOOK_URL`

### Option 2: Email via SendGrid
```yaml
- name: Send email notification
  if: steps.check_notification.outputs.floor_15_reached == 'true'
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.sendgrid.net
    server_port: 587
    username: apikey
    password: ${{ secrets.SENDGRID_API_KEY }}
    subject: fajoogaloo reached floor 15!
    body: Player fajoogaloo has reached floor 15 (1938m) in Deep Dip 2!
    to: your-email@example.com
    from: noreply@example.com
```

### Option 3: Slack Webhook
```yaml
- name: Send Slack notification
  if: steps.check_notification.outputs.floor_15_reached == 'true'
  run: |
    curl -X POST -H 'Content-type: application/json' \
         --data '{"text":"🎉 fajoogaloo has reached floor 15 in Deep Dip 2!"}' \
         ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Option 4: GitHub Issues
```yaml
- name: Create GitHub issue
  if: steps.check_notification.outputs.floor_15_reached == 'true'
  uses: actions/github-script@v7
  with:
    script: |
      await github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: '🎉 fajoogaloo reached floor 15!',
        body: 'Player fajoogaloo has reached floor 15 (1938m) in Deep Dip 2!'
      });
```

### Option 5: SMS via Twilio
Modify `monitor_player.py` to use the Twilio API when floor 15 is detected.

## API Information

- **Source**: [Deep Dip 2 GitHub Repository](https://github.com/littledivy/deepdip2)
- **Endpoint**: `https://deepdip2.live/leaderboard`
- **Plugin**: [Dips++ (official Deep Dip 2 plugin)](https://openplanet.dev/plugin/dips-plus-plus)

## Floor 15 Details

- **Height**: 1938 meters
- **Floor Name**: Floor 15

## Resources

- [Deep Dip 2 Tracker](https://deepdip2.com/)
- [Deep Dip 2 on Liquipedia](https://liquipedia.net/trackmania/Deep_Dip/2)
- [Dips++ Plugin](https://openplanet.dev/plugin/dips-plus-plus)
