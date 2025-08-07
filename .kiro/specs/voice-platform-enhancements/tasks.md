# Implementation Plan

- [x] 1. Create service management system to prevent duplicate instances
  - Implement process detection utilities to find existing Voxtral instances
  - Create instance termination logic with graceful shutdown
  - Add startup method detection and cleanup for conflicting autostart configurations
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Implement global hotkey system with Ctrl+Alt activation
  - Install and integrate pynput library for global key listening
  - Create hotkey manager class with background key monitoring
  - Implement voice activation callback integration with existing voice system
  - Add hotkey configuration options to voxtral.yaml
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Enhance cursor typing system with better window detection
  - Improve window detection algorithms for active application identification
  - Implement application-specific typing strategies for better compatibility
  - Add cursor position detection capabilities where supported
  - Create fallback mechanism cascade (direct typing → clipboard → notification)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Create unified tray application replacing duplicate implementations
  - Merge functionality from both tray_icon.py and voxtral_tray_gtk.py
  - Integrate service manager, hotkey manager, and enhanced cursor typing
  - Add status indicators for hotkey activation and service state
  - Implement user notifications for feedback and error reporting
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 5. Update autostart configuration system
  - Modify setup_autostart.sh to use only one startup method (systemd preferred)
  - Add cleanup logic to remove conflicting desktop autostart entries
  - Create service management commands for easy user control
  - Add configuration option for preferred startup method
  - _Requirements: 1.1, 1.3, 4.1, 4.2_

- [ ] 6. Add hotkey configuration and feedback systems
  - Extend configuration schema with hotkey settings
  - Implement visual feedback for hotkey activation (tray icon changes)
  - Add audio feedback option with system sound integration
  - Create hotkey conflict detection and resolution
  - _Requirements: 2.1, 2.2, 5.1, 5.2, 5.3, 5.4_

- [ ] 7. Implement comprehensive error handling and recovery
  - Add error handling for hotkey registration failures
  - Implement automatic service restart with exponential backoff
  - Create graceful degradation when components fail
  - Add detailed logging for troubleshooting service and hotkey issues
  - _Requirements: 4.3, 5.3, 5.4_

- [ ] 8. Create installation and migration scripts
  - Update installation scripts to handle existing configurations
  - Create migration script to move from old dual-service setup to new unified system
  - Add dependency installation for pynput and other new requirements
  - Update documentation with new hotkey and service management features
  - _Requirements: 1.1, 1.4, 2.5_

- [ ] 9. Write comprehensive tests for new functionality
  - Create unit tests for service manager, hotkey manager, and cursor typing components
  - Implement integration tests for hotkey → voice → typing workflow
  - Add system tests for service startup and duplicate prevention
  - Create manual testing procedures for different desktop environments
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 10. Update configuration system and user interface
  - Add new configuration options to voxtral.yaml with validation
  - Update tray menu with hotkey status and configuration options
  - Implement configuration validation and error reporting
  - Add user-friendly configuration management through tray interface
  - _Requirements: 5.1, 5.2, 5.5_