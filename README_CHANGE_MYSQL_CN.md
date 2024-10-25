# 替换PostgreSQL
## 1.修改环境变量 
- 基于 `api/.env.example`创建一个新的  `api/.env` 并且修改postgresql的部分替换成Mysql
```
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
## 2.修改数据库表
将所有的postgresql的表DDL转换成MySQL并且写入到新的数据库, 比如
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
修改成Mysql SQL
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
需要替换每一张表 总量大概70张

## 3.移除PostgreSQL依赖并导入Mysql依赖
- 在pyproject.toml移除
`psycopg2-binary = "~2.9.6"`
- 在pyproject.toml中添加
```
Flask-SQLAlchemy = "~3.1.1"
pymysql = "^1.1.1"
```
## 4.替换`models`下的数据库对象的ID列的语义
由于`dify`使用的Postgresql可以自定义生成uuid，但是Mysql低版本不支持，
所以我们不仅要修改表的DDL还要修改对应的代码，例如

```
id = db.Column(StringUUID,default=lambda: str(uuid.uuid4()))
```
修改成
```
 id = db.Column(StringUUID, primary_key=True, default=lambda: str(uuid.uuid4()))
```
## 5. 修改用到的UUID函数
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
        else: # 主要修改非postgresql 的情况
            return dialect.type_descriptor(CHAR(36))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return str(value)

```
## 6.修改启动时使用的url 
因为postgresql的链接url中含有MySQL不支持的参数，所以要删除对应参数