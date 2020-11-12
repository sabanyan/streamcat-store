class NothingToPutbackException(Exception):
    """
    ゴミ箱から0個のDatumを戻した場合にお知らせする
    """
    pass

class NoResultsException(Exception):
    """
    実行結果がなかった場合にお知らせする
    """
    pass

class OptimisticLockException(Exception):
    """
    楽観的排他制御によりDatumの更新に失敗したことを通知する例外
    """
    pass

class EditLockedException(Exception):
    """
    Datumが編集ロックされているため編集できないことを通知する
    """
    pass

class CommandException(Exception):
    """
    コマンドが送出する例外
    """
    def __init__(self, ex):
        self._ex = ex

    @property
    def innerException(self):
        return self._ex

    def __str__(self):
        return self._ex.__str__()

class GroupBy2Exception(CommandException):
    """
    class for unique exceptions in the GroupBy2 Command
    """
    pass

class ColumnNameException(CommandException):
    """
    class for unique exceptions in the Column Name Command
    """
    pass

class FieldNotFoundException(CommandException):
    """
    exception class for Field Not Found error
    
    inputs:
    not_found_field    field that was not found
    command_name       name of command (optional)
    option_id          input field id (optional)
    """
    def __init__(self, not_found_field, command_name = '', option_id = ''):
        self._not_found_field = not_found_field
        self._command_name = command_name
        self._option_id = option_id
        
    def __str__(self):
        msg = ''
        if self._command_name != '':
            msg +=  f'【コマンド：{self._command_name}】'
        if self._option_id != '':
            msg += f'【オプションID：{self._option_id}】'

        msg += f'指定した項目名は存在しません。{self._not_found_field}'
        return msg
    
class FieldConflictException(CommandException):
    """
    exception class for Field Conflict error
    
    inputs:
    conflict_field     field that was conflicted
    command_name       name of command (optional)
    option_id          input field id (optional)
    """
    def __init__(self, conflict_field, command_name = '', option_id = ''):
        self._conflict_field = conflict_field
        self._command_name = command_name
        self._option_id = option_id
        
    def __str__(self):
        msg = ''
        if self._command_name != '':
            msg +=  f'【コマンド：{self._command_name}】'
        if self._option_id != '':
            msg += f'【オプションID：{self._option_id}】'

        msg += f'同じ項目名が複数回指定されています。{self._conflict_field}'
        return msg

class EmptyFieldException(CommandException):
    """
    exception class for Empty Field error
    
    inputs:
    command_name       name of command (optional)
    option_id          input field id (optional)
    """
    def __init__(self, command_name = '', option_id = ''):
        self._command_name = command_name
        self._option_id = option_id
        
    def __str__(self):
        msg = ''
        if self._command_name != '':
            msg +=  f'【コマンド：{self._command_name}】'
        if self._option_id != '':
            msg += f'【オプションID：{self._option_id}】'

        msg += f'空文字列の項目名は指定できません。'
        return msg
    
class FieldForbiddenCharacterException(CommandException):
    """
    exception class for Forbidden Character (Field) Error
    Forbidden Characters for field setting are % & \ :
    
    inputs:
    bad_field          field setting with forbidden character
    command_name       name of command (optional)
    option_id          input field id (optional)
    """
    def __init__(self, bad_field, command_name = '', option_id = ''):
        self._bad_field = bad_field
        self._command_name = command_name
        self._option_id = option_id
        
    def __str__(self):
        msg = ''
        if self._command_name != '':
            msg +=  f'【コマンド：{self._command_name}】'
        if self._option_id != '':
            msg += f'【オプションID：{self._option_id}】'

        msg += f'半角の（ :　%　&　\\ ）は、項目名の指定に使用できません。{self._bad_field}'
        return msg

