
# Replacing PostgreSQL

## 1. Modify Environment Variables
- Create a new `api/.env` file based on `api/.env.example` and modify the PostgreSQL section to replace it with MySQL.
```bash
# PostgreSQL database configuration
DB_USERNAME=root
DB_PASSWORD=
DB_HOST=your db uri
DB_PORT=4000
DB_DATABASE=dify
SQLALCHEMY_DATABASE_URI_SCHEME=mysql+pymysql
SQLALCHEMY_TRACK_MODIFICATIONS=False
SQLALCHEMY_DATABASE_URI=mysql+pymysql://root:@4.241.26.23:4000/dify
```

## 2. Modify Database Tables
Convert all PostgreSQL table DDL to MySQL and write them into the new database. For example:

```sql
# PostgreSQL
create table workflow_app_logs
(
    id              uuid      default uuid_generate_v4()   not null
        constraint workflow_app_log_pkey
            primary key,
    tenant_id       uuid                                   not null,
    app_id          uuid                                   not null,
    workflow_id     uuid                                   not null,
    workflow_run_id uuid                                   not null,
    created_from    varchar(255)                           not null,
    created_by_role varchar(255)                           not null,
    created_by      uuid                                   not null,
    created_at      timestamp default CURRENT_TIMESTAMP(0) not null
);

alter table workflow_app_logs
    owner to postgres;

create index workflow_app_log_app_idx
    on workflow_app_logs (tenant_id, app_id);
```

Convert it to MySQL SQL:
```sql
-- auto-generated definition
create table workflow_app_logs
(
    id              char(36)                            not null
        primary key,
    tenant_id       char(36)                            not null,
    app_id          char(36)                            not null,
    workflow_id     char(36)                            not null,
    workflow_run_id char(36)                            not null,
    created_from    varchar(255)                        not null,
    created_by_role varchar(255)                        not null,
    created_by      char(36)                            not null,
    created_at      timestamp default CURRENT_TIMESTAMP not null
);

create index workflow_app_log_app_idx
    on workflow_app_logs (tenant_id, app_id);
```

This process needs to be repeated for about 70 tables.

## 3. Remove PostgreSQL Dependencies and Import MySQL Dependencies
- Remove the following from `pyproject.toml`:
```bash
psycopg2-binary = "~2.9.6"
```
- Add the following to `pyproject.toml`:
```bash
Flask-SQLAlchemy = "~3.1.1"
pymysql = "^1.1.1"
```

## 4. Modify the Database Object's ID Column in the `models`
Since PostgreSQL supports custom UUID generation but MySQL (older versions) does not, we need to modify both the table DDL and the corresponding code. For example:

```python
id = db.Column(StringUUID, default=lambda: str(uuid.uuid4()))
```
Modify it to:
```python
id = db.Column(StringUUID, primary_key=True, default=lambda: str(uuid.uuid4()))
```

## 5. Modify the UUID Function Used
```python
class StringUUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            return value.hex

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else: # Modify for non-PostgreSQL dialects
            return dialect.type_descriptor(CHAR(36))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return str(value)
```

## 6. Modify the URL Used at Startup
Since the PostgreSQL connection URL contains parameters not supported by MySQL, you need to remove the corresponding parameters.
