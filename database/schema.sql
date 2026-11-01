-- Canonical schema is maintained by SQLAlchemy models and Alembic migrations.
-- Create the MySQL database and grant the application user access:
CREATE DATABASE helpdesk_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- Configure DATABASE_URL in .env; never place credentials in this file.
