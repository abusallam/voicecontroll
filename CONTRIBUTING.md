# Contributing to Voxtral Agentic Voice Platform

Thank you for your interest in contributing to the Voxtral Agentic Voice Platform! This project is a community-driven effort to create the best open-source voice assistant for Linux.

## 🤝 How to Contribute

### Reporting Issues
- Use GitHub Issues to report bugs or request features
- Provide detailed information about your system (OS, desktop environment, hardware)
- Include logs and error messages when reporting bugs
- Test with the latest version before reporting

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/voxtral-agentic-voice-platform.git
   cd voxtral-agentic-voice-platform
   ```

2. **Install Dependencies**
   ```bash
   # Install UV package manager
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install project dependencies
   ./scripts/install_uv.sh
   ```

3. **Run Tests**
   ```bash
   uv run scripts/test_system.py
   uv run scripts/test_cursor_typing.py
   ```

### Code Style

- Follow PEP 8 Python style guidelines
- Use Black for code formatting: `uv run black .`
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep line length to 100 characters

### Testing

- Test on multiple Linux distributions (Debian, Ubuntu, Fedora, Arch)
- Test on both Wayland and X11
- Test with different desktop environments (GNOME, KDE, XFCE)
- Test with both GPU and CPU-only systems
- Add unit tests for new functionality

### Pull Request Process

1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Make your changes and test thoroughly
3. Update documentation if needed
4. Commit with clear, descriptive messages
5. Push to your fork: `git push origin feature/amazing-feature`
6. Create a Pull Request with:
   - Clear description of changes
   - Testing performed
   - Screenshots/videos if UI changes
   - Reference to related issues

## 🎯 Areas for Contribution

### High Priority
- **Multi-language support** - Add support for languages other than English
- **Custom wake words** - Implement trainable wake word detection
- **Voice synthesis** - Add text-to-speech responses
- **Performance optimization** - Reduce memory usage and latency
- **Better Wayland integration** - Improve cursor typing on different compositors

### Medium Priority
- **Additional tools** - File management, calendar integration, email
- **Plugin system** - Allow third-party extensions
- **Configuration GUI** - Visual configuration editor
- **Voice training** - User-specific voice model fine-tuning
- **Context awareness** - Better understanding of user intent

### Low Priority
- **Mobile support** - Android/iOS companion apps
- **Cloud sync** - Optional cloud backup of settings
- **Voice analytics** - Usage statistics and insights
- **Multi-user support** - Different profiles for different users

## 🏗️ Architecture Guidelines

### Code Organization
- `agent/` - Core voice processing and AI logic
- `tools/` - Individual tool implementations
- `langraph/` - Workflow orchestration
- `models/` - AI model interfaces
- `config/` - Configuration management
- `scripts/` - Installation and utility scripts

### Adding New Tools
1. Create tool in `tools/` directory
2. Use `@tool` decorator from LangChain
3. Add proper error handling and logging
4. Update tool registry in `langraph/workflows.py`
5. Add tests and documentation

### Adding New Models
1. Create handler in `models/` directory
2. Implement standard interface
3. Add fallback mechanisms
4. Test with different hardware configurations

## 🐛 Bug Reports

When reporting bugs, please include:

- **System Information**
  - OS and version
  - Desktop environment
  - Display server (Wayland/X11)
  - Hardware specs (CPU, GPU, RAM)

- **Steps to Reproduce**
  - Exact steps that trigger the bug
  - Expected vs actual behavior
  - Frequency of occurrence

- **Logs and Output**
  - Relevant log entries
  - Error messages
  - Console output

- **Configuration**
  - Modified settings
  - Custom configurations
  - Installed packages

## 📝 Documentation

- Update README.md for user-facing changes
- Update technical documentation in `docs/`
- Add inline code comments for complex logic
- Update configuration examples
- Create tutorials for new features

## 🎨 Design Principles

- **Privacy First** - All processing should be local by default
- **Linux Native** - Embrace Linux desktop conventions
- **Accessible** - Work on low-end hardware
- **Secure** - Sandbox dangerous operations
- **Extensible** - Easy to add new capabilities
- **User-Friendly** - Simple setup and configuration

## 📄 License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation
- Special thanks in major releases

## 💬 Community

- **GitHub Discussions** - General questions and ideas
- **GitHub Issues** - Bug reports and feature requests
- **Pull Requests** - Code contributions

## 🚀 Release Process

1. **Development** - Feature branches and pull requests
2. **Testing** - Automated and manual testing
3. **Documentation** - Update docs and changelog
4. **Packaging** - Build .deb packages and releases
5. **Distribution** - GitHub releases and package repositories

Thank you for helping make Voxtral the best voice assistant for Linux! 🎙️🐧