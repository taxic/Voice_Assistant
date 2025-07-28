# Spotify Integration Setup Guide

This guide will help you set up Spotify integration with your voice assistant.

## Prerequisites

1. A Spotify account (Premium subscription required for playback control)
2. Python environment with all requirements installed

## Setup Steps

### 1. Install Dependencies

First, install the required Python package:

```bash
pip install spotipy==2.23.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 2. Create a Spotify App

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create an App"
4. Fill in the app details:
   - **App name**: "Voice Assistant" (or any name you prefer)
   - **App description**: "Personal voice assistant with Spotify control"
   - **Website**: You can leave this blank or put a placeholder
   - **Redirect URI**: `http://localhost:8888/callback`
5. Check the box to agree to the terms
6. Click "Create"

### 3. Get Your Credentials

1. On your app's dashboard, you'll see:
   - **Client ID**: Copy this value
   - **Client Secret**: Click "Show Client Secret" and copy this value

### 4. Set Environment Variables

You need to set these as environment variables for security. On Windows PowerShell:

```powershell
$env:SPOTIFY_CLIENT_ID="your_client_id_here"
$env:SPOTIFY_CLIENT_SECRET="your_client_secret_here"
$env:SPOTIFY_REDIRECT_URI="http://localhost:8888/callback"
```

On Windows Command Prompt:
```cmd
set SPOTIFY_CLIENT_ID=your_client_id_here
set SPOTIFY_CLIENT_SECRET=your_client_secret_here
set SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

For a permanent solution, add these to your system environment variables:
1. Open System Properties → Advanced → Environment Variables
2. Add the three variables above to your user environment variables

### 5. First-Time Authentication

When you first run the assistant and try to use a music command:

1. The system will automatically open your web browser
2. You'll be redirected to Spotify to authorize the app
3. After clicking "Agree", you'll be redirected to a localhost URL
4. Copy the entire URL from your browser's address bar
5. Paste it back into the terminal when prompted
6. The authentication token will be saved for future use

### 6. Spotify Device Requirements

For music playback to work, you need:
1. Spotify app running on at least one device (computer, phone, smart speaker, etc.)
2. The device should be logged into the same Spotify account
3. For best results, start playing something briefly in the Spotify app first

## Available Voice Commands

Once set up, you can use these voice commands:

### Playing Music
- "Play [song name]"
- "Play [song name] by [artist]"
- "Play music by [artist]"
- "Spotify play [song name]"

### Queue Management
- "Queue [song name]"
- "Add [song name] to queue"
- "Queue up [song name] by [artist]"

### Playback Control
- "Pause music"
- "Resume music" / "Continue playing"
- "Next song" / "Skip"
- "Previous song" / "Go back"

### Information
- "What song is playing?"
- "What's currently playing?"

### Volume Control
- "Set volume to 50"
- "Volume 80"
- "Turn volume to 25"

## Troubleshooting

### "Spotify is not connected" Error
- Check that environment variables are set correctly
- Restart your terminal/PowerShell session
- Ensure Spotify app credentials are correct

### "No Spotify devices are available" Error
- Open the Spotify app on any device
- Make sure you're logged into the same account
- Try playing something briefly in the Spotify app

### Authentication Issues
- Delete the `.spotify_cache` file and try again
- Check that the redirect URI in your Spotify app matches exactly: `http://localhost:8888/callback`
- Ensure your Spotify account has the necessary permissions

### Premium Account Required
- Most playback control features require Spotify Premium
- Free accounts have limited API access for playback control

## Security Notes

- Never commit your Client ID and Client Secret to version control
- Use environment variables or a secure configuration file
- The `.spotify_cache` file contains your access token - keep it secure
- Consider adding `.spotify_cache` to your `.gitignore` file

## Example Usage

After setup, you can say:
- "Play Bohemian Rhapsody by Queen"
- "Queue some jazz music"
- "Pause music"
- "What's playing?"
- "Set volume to 60"

The assistant will search Spotify for the requested song and control playback accordingly.
