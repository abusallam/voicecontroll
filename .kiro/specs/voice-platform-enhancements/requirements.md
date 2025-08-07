# Requirements Document

## Introduction

This feature enhances the Voxtral Agentic Voice Platform to resolve startup conflicts, add global hotkey support, and improve cursor-aware typing functionality. The platform currently has duplicate autostart services causing conflicts, lacks global hotkey activation, and needs better cursor positioning for transcribed text.

## Requirements

### Requirement 1: Fix Duplicate Autostart Services

**User Story:** As a system administrator, I want only one instance of the voice platform to start automatically, so that there are no conflicts or duplicate tray icons.

#### Acceptance Criteria

1. WHEN the system starts THEN only one voice platform service SHALL be running
2. WHEN I check running processes THEN there SHALL be exactly one voxtral tray process
3. IF both systemd and desktop autostart are configured THEN the system SHALL prioritize one method and disable the other
4. WHEN the service starts THEN it SHALL check for existing instances and prevent duplicates

### Requirement 2: Global Hotkey Activation

**User Story:** As a user, I want to press Ctrl+Alt to start voice transcription, so that I can quickly activate voice input without clicking the tray icon.

#### Acceptance Criteria

1. WHEN I press Ctrl+Alt simultaneously THEN the system SHALL start listening for voice input
2. WHEN voice transcription is active THEN the system SHALL provide visual feedback
3. WHEN I press Ctrl+Alt while already listening THEN the system SHALL stop listening
4. WHEN the hotkey is pressed THEN the system SHALL work regardless of which window has focus
5. WHEN the system starts THEN the global hotkey SHALL be automatically registered

### Requirement 3: Enhanced Cursor-Aware Typing

**User Story:** As a user, I want transcribed text to appear exactly where my cursor is positioned, so that I can seamlessly integrate voice input into my workflow.

#### Acceptance Criteria

1. WHEN voice transcription completes THEN the text SHALL be typed at the current cursor position
2. WHEN the cursor is in a text field THEN the system SHALL detect the active application and window
3. WHEN typing at cursor position fails THEN the system SHALL fall back to clipboard method
4. WHEN text is ready for insertion THEN the system SHALL provide clear feedback to the user
5. WHEN using Wayland THEN the system SHALL use wtype for direct text injection
6. WHEN using X11 THEN the system SHALL use xdotool for direct text injection

### Requirement 4: Service Management Improvements

**User Story:** As a user, I want reliable service management, so that the voice platform starts correctly and can be easily controlled.

#### Acceptance Criteria

1. WHEN the system boots THEN the voice platform SHALL start automatically using the most reliable method
2. WHEN I want to restart the service THEN I SHALL have clear commands to do so
3. WHEN the service fails THEN it SHALL automatically restart with exponential backoff
4. WHEN multiple instances are detected THEN the system SHALL terminate duplicates gracefully
5. WHEN I check service status THEN I SHALL see clear information about running components

### Requirement 5: Hotkey Configuration and Feedback

**User Story:** As a user, I want to configure hotkey behavior and receive clear feedback, so that I can customize the voice activation to my preferences.

#### Acceptance Criteria

1. WHEN I configure hotkeys THEN the settings SHALL be persisted in the configuration file
2. WHEN hotkey activation occurs THEN I SHALL receive visual and/or audio feedback
3. WHEN hotkey registration fails THEN the system SHALL log the error and provide fallback options
4. WHEN the hotkey conflicts with other applications THEN the system SHALL detect and warn about conflicts
5. WHEN I want to disable hotkeys THEN I SHALL be able to do so through configuration