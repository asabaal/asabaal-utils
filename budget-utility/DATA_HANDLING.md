# Data Handling Guidelines

## Data Storage

This utility stores all data locally in the following directory:

```
budget-utility/data/
```

The main data file is `budget-data.json`, which contains all your budget entries, categories, notes, and projections.

## Data Privacy

Your financial data remains **private** and **local** to your computer. The application:

- Does not upload data to any server
- Does not include any tracking or analytics
- Stores all data on your local filesystem only

## Keep Data Out of Git

We use `.gitignore` rules to ensure your financial data is **not committed to Git**. This is important for privacy and security reasons. The following patterns are excluded:

```
**/data/
budget-utility/data/
*.json
!package.json
!package-lock.json
```

## Backup Recommendations

Since your data is not stored in Git, we recommend:

1. Regularly use the backup command: `npm run backup`
2. Store backups in a secure location
3. Consider encrypting sensitive financial data backups

## Data Migration

If you need to move your data to another computer:

1. Run `npm run backup` on your current system
2. Copy the backup file from `budget-utility/data/backups/` 
3. On the new system, place the backup file in the same directory
4. Rename it to `budget-data.json`

## Data Format

Your data is stored in a structured JSON format. If you need to edit it manually:

1. Make sure to maintain the proper JSON structure
2. Create a backup before making manual changes
3. The application validates the structure when loading

## Troubleshooting

If you encounter data corruption:

1. Try restoring from a backup
2. If no backup exists, the application will create a new empty database
3. You can run `npm run clean` to reset your data if needed
