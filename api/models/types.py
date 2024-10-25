from sqlalchemy import CHAR, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID


class StringUUID(TypeDecorator):
    impl = CHAR
    cache_ok = True  # 设置 cache_ok 属性

    def __init__(self, length=36, **kwargs):
        super().__init__(**kwargs)
        self.length = length

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return str(uuid.UUID(value))