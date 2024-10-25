
# PostgreSQLの置き換え

## 1. 環境変数の変更
- `api/.env.example`を基に新しい`api/.env`ファイルを作成し、PostgreSQLの部分をMySQLに置き換えます。
```bash
# PostgreSQLデータベース設定
DB_USERNAME=root
DB_PASSWORD=
DB_HOST=your db uri
DB_PORT=4000
DB_DATABASE=dify
SQLALCHEMY_DATABASE_URI_SCHEME=mysql+pymysql
SQLALCHEMY_TRACK_MODIFICATIONS=False
SQLALCHEMY_DATABASE_URI=mysql+pymysql://root:@4.241.26.23:4000/dify
```

## 2. データベーステーブルの変更
すべてのPostgreSQLテーブルのDDLをMySQLに変換し、新しいデータベースに書き込みます。例:

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

MySQL SQL に変換:
```sql
-- 自動生成された定義
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

このプロセスは約70個のテーブルに対して繰り返す必要があります。

## 3. PostgreSQL依存関係の削除とMySQL依存関係の追加
- `pyproject.toml` から以下を削除します:
```bash
psycopg2-binary = "~2.9.6"
```
- `pyproject.toml` に以下を追加します:
```bash
Flask-SQLAlchemy = "~3.1.1"
pymysql = "^1.1.1"
```

## 4. `models`内のデータベースオブジェクトのID列の変更
PostgreSQLはUUIDのカスタム生成をサポートしていますが、MySQL（古いバージョン）はサポートしていません。そのため、テーブルDDLと対応するコードを修正する必要があります。例えば:

```python
id = db.Column(StringUUID, default=lambda: str(uuid.uuid4()))
```
次のように修正します:
```python
id = db.Column(StringUUID, primary_key=True, default=lambda: str(uuid.uuid4()))
```

## 5. UUID関数の修正
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
        else: # PostgreSQL以外のダイアレクトの場合を修正
            return dialect.type_descriptor(CHAR(36))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return str(value)
```

## 6. 起動時に使用するURLの変更
PostgreSQLの接続URLにはMySQLがサポートしていないパラメータが含まれているため、該当するパラメータを削除する必要があります。
