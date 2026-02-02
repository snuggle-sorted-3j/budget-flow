# Database Management Manual

This guide covers how to access, monitor, and back up the BudgetFlow database.

## 1. Accessing pgAdmin (GUI)

I have added pgAdmin to the Docker configuration. You can now access the database through a web interface.

- **URL**: [http://localhost:5050](http://localhost:5050)
- **Login Email**: `admin@admin.com`
- **Login Password**: `admin`

### Connecting to the Database Server
Once logged into pgAdmin, you need to register the server:
1. Right-click on **Servers** > **Register** > **Server...**
2. **General Tab**:
   - **Name**: `BudgetFlow Local`
3. **Connection Tab**:
   - **Host name/address**: `postgres` (internal Docker network name)
   - **Port**: `5432`
   - **Maintenance database**: `budget_flow`
   - **Username**: `postgres`
   - **Password**: `%&GxkL66Z7pqUp66v!n5*4HWZfVKsH` (from your `.env`)
   - **Save Password?**: Yes
4. Click **Save**.

---

## 2. Data Persistence

### How data is kept safe
The database data is stored in a **Docker Volume** named `postgres_data`. This ensures that even if you restart or stop the containers, your data remains intact.

> [!TIP]
> Do NOT use `docker-compose down -v` unless you explicitly want to delete all your data. The `-v` flag removes volumes.

### In what cases could data be lost?
1. **Volume Deletion**: Deleting the Docker volume manually or using the `-v` flag with `docker-compose down`.
2. **Disk Corruption**: Physical or filesystem errors on your machine's drive.
3. **Database Drop**: Running a `DROP DATABASE` or `DROP TABLE` command inside pgAdmin or a script.
4. **Incorrect Migration**: Running database migrations that drop columns without a recovery plan.

---

## 3. Creating Backups

### Manual Backup (CLI)
To create a backup file of your current database, run this command from your terminal:

```bash
docker exec -t budget-flow-postgres pg_dump -U postgres budget_flow > budget_flow_backup_$(date +%Y%m%d).sql
```

### Restoring a Backup
To restore a backup into a fresh database:

```bash
cat your_backup_file.sql | docker exec -i budget-flow-postgres psql -U postgres -d budget_flow
```

### Automation Suggestion
For long-term safety, it is recommended to run the backup command daily via a `cron` job or a simple shell script.
