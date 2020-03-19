import functools

class NotAuthorizedException(Exception):
    """
    処理する権限がないことを通知する例外
    """
    pass

# def authz_required(method):
#     """
#     デコレートするメソッドを処理する権限の有無を判定する
#     """
#     def _authz_required(func):
#         @functools.wraps(func)
#         def deco(**kwargs):
#             # 操作対象のオブジェクト
#             target = kwargs[0]

#             print(target)
#             # 
#             # kwargsからユーザIDと操作対象オブジェクトを取得するか？
#             # 

#             # if auth.has_authz(user_id, target, method):
#             #     return func(**kwargs)
#             # else:
#             #     raise NotAuthorizedException('許可されていない操作です')

#             return func(**kwargs)
#         return deco
#     return _authz_required

from inspect import signature

def add_print(pattern):
    """
    ファイルの作成前後に表示を行うデコレータ
    """
    def _add_print(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # print(args)
            # print(kwargs)

            sig = signature(func)
            
            parm_index = 0
            itr = sig.parameters.items()
            for item in itr:
                parm_name = item[0]

                print('NAME:', parm_name)
                print('VALUE:', args[parm_index])

                parm_index += 1


            return func(*args, **kwargs)
        return wrapper

    return _add_print