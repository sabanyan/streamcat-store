"""
便利関数
"""

class Util:

    @staticmethod
    def datetime_to_local_time_str(d):
        import datetime
        if d is None:
            return ''
        # DBに格納されている日時はUTCなので、タイムゾーンをUTCに設定する
        d_at_utc = d.replace(tzinfo=datetime.timezone.utc)
        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        d_at_local = d_at_utc.astimezone()
        return d_at_local.strftime('%Y-%m-%d %H:%M:%S')
