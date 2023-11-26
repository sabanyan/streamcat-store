import sqlalchemy.types
from sqlalchemy import String
from sqlalchemy.sql import operators

class QueryableString(sqlalchemy.types.TypeDecorator):
    """
    SQLAlchemyにおいてString列のlike/ilike演算で検索語をエスケープする
    """
    impl = sqlalchemy.types.String
    # キャッシュを許可する
    cache_ok = True

    class comparator_factory(String.Comparator):

        # LIKE検索語のエスケープ変換テーブル
        ESCAPE_TABLE = str.maketrans({
                            '%' : '\%',
                            '_' : '\_',
                            '\\': '\\\\'
                        })

        def icontains(self, other, **kw):
            """
            検索語を含むか否か判定する(大文字小文字の違いを無視する)
            """
            # 検索語をエスケープする
            escaped_search_str = other.translate(self.ESCAPE_TABLE)
            return self.operate(operators.ilike_op, '%' + escaped_search_str + '%', escape='\\')
