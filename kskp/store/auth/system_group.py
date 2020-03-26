# import os
# from sqlalchemy import Column, String, text
# from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, ENUM
# from kskp.store import BaseModel

# class SystemGroup(BaseModel):
#     ADMIN_TYPE = 'admin'
#     EVERYONE_TYPE = 'everyone'

#     # テーブル名の定義
#     __tablename__ = 'system_groups'

#     # 定義先スキーマ
#     if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
#         # テスト環境用のスキーマ
#         __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

#     # 列名と列のデータ型等の定義
#     type        = Column(ENUM(ADMIN_TYPE, EVERYONE_TYPE, name='group_type'), primary_key=True, nullable=False)
#     group_id    = Column(INTEGER, nullable=False)
#     creator     = Column(INTEGER)
#     modifier    = Column(INTEGER)
#     created_at  = Column(TIMESTAMP, default=text('statement_timestamp()'))
#     modified_at = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

#     def __init__(self, type, group_id, creator=None):
#         """
#         コンストラクタ
#         """
#         self.type = type
#         self.group_id = group_id

#         # creator, modifier
#         self.creator = creator
#         self.modifier = creator

#     def save(self):
#         from kskp.store import ss as session
#         # Groupsテーブルにレコードを新規追加する
#         session.add(self)
#         session.commit()
