# Asabaal Music Business - Project Management System

A comprehensive project management system designed specifically for managing multiple aspects of a music business, including music production, trading/investment, content creation, technology development, and business partnerships.

## Features

- **Dashboard** with key metrics and visualizations
- **Project Management** with categorization, status tracking, and progress monitoring
- **Task Management** with priorities, deadlines, and assignments
- **Timeline View** for visualizing your 2025 business roadmap
- **Automated Reminders** for upcoming and overdue deadlines
- **Web Interface** for easy access from any device
- **Command Line Interface** for quick updates and queries

## System Requirements

- Node.js 14.x or higher
- NPM 6.x or higher

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/asabaal/asabaal-utils.git
   cd asabaal-utils
   git checkout project-management-system
   cd project-management
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Initialize the system:
   ```
   node start.js --seed
   ```
   The `--seed` flag will populate the system with your 2025 business timeline data.

4. Access the web interface:
   ```
   http://localhost:3000
   ```

## Command Line Usage

The system includes a CLI tool for quick updates and queries:

```
# Initialize the system
node src/cli/index.js init

# Show dashboard
node src/cli/index.js dashboard

# List all projects
node src/cli/index.js project --list

# Create a new project
node src/cli/index.js project --create

# Get project details
node src/cli/index.js project --get <project-id>

# List all tasks
node src/cli/index.js task --list

# List overdue tasks
node src/cli/index.js task --overdue

# List upcoming tasks
node src/cli/index.js task --upcoming 7

# Mark a task as complete
node src/cli/index.js task --mark-complete <task-id>

# Export data
node src/cli/index.js export backup.json

# Import data
node src/cli/index.js import backup.json
```

## System Architecture

The system is built with a modular architecture:

1. **Core Data Models** - Projects, Tasks, Timelines
2. **Storage Layer** - File-based storage (can be extended to databases)
3. **Repositories** - CRUD operations for projects and tasks
4. **Services** - Business logic and coordination between repositories
5. **Web API** - RESTful endpoints for frontend access
6. **CLI Interface** - Command line tools for system management
7. **Web Interface** - Browser-based UI for visualization and management

## Folder Structure

```
project-management/
├── data/                  # Data storage directory
├── scripts/               # Scripts for data seeding and utility functions
├── src/                   # Source code
│   ├── models/            # Data models
│   ├── repositories/      # Data access repositories
│   ├── services/          # Business logic services
│   ├── utils/             # Utility functions
│   ├── cli/               # Command line interface
│   ├── web/               # Web interface
│   │   ├── public/        # Static files (HTML, CSS, JS)
│   │   └── server.js      # Express server
│   ├── app.js             # Main application class
│   └── index.js           # Module exports
├── package.json           # NPM package definition
├── README.md              # This documentation
└── start.js               # Application starter script
```

## Customization

The system is designed to be easily customizable:

### Adding New Categories

Edit `src/models/index.js` to add new project categories:

```javascript
const PROJECT_CATEGORIES = {
  MUSIC_PRODUCTION: 'music_production',
  TRADING: 'trading',
  CONTENT_CREATION: 'content_creation',
  TECHNOLOGY: 'technology',
  BUSINESS: 'business',
  // Add your custom category:
  NEW_CATEGORY: 'new_category'
};
```

### Extending Storage

The system uses file-based storage by default, but you can extend it to use a database:

1. Create a new storage implementation that follows the same interface as `src/utils/storage.js`
2. Update the `ProjectManagementApp` constructor to use your custom storage

### Adding Notification Channels

The notification service supports multiple channels:

1. Edit `src/services/notificationService.js` to add new notification channels
2. Implement the channel-specific sending logic
3. Configure the channels in `start.js`

## Timeline for 2025

The system is pre-seeded with your 2025 business timeline:

- **APRIL/MAY**: Trading program evaluation, business registration
- **MAY**: Business infrastructure setup, InvestFest preparation
- **JUNE/JULY**: "Dapper Demos Vol. 3" content cycle, trading strategy refinement
- **AUGUST/SEPTEMBER**: InvestFest, "4-D(emos)" EP preparation
- **OCTOBER**: "4-D(emos)" EP release, advanced trading strategies
- **NOVEMBER/DECEMBER**: Post-release cycle, 2026 planning

## License

MIT License

## Author

Asabaal
