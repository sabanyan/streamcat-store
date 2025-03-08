from streamcat.core import Datum, SavableDatum, Constraints

class Schedule(SavableDatum):

    __mapper_args__ = {
        'polymorphic_identity' : 'schedule'
    }

    # Flow Jsonの定義
    TRIGGER_JSON_SCHEMA = {
        'title' : 'Trigger JSON Schema',
        'description' : 'This is a schema that define a job launch time.',
        '$schema': 'http://json-schema.org/draft-07/schema#',
        '$ref': '#/definitions/Trigger',
        'definitions': {
            'Trigger': {
                'type': 'object',

                'if': {
                    'properties': { 'type': { 'const': 'date' } }
                },
                'then': {
                    '$ref': '#/definitions/Date'
                },

                'if': {
                    'properties': { 'type': { 'const': 'interval' } }
                },
                'then': {
                    '$ref': '#/definitions/Interval'
                },

                'if': {
                    'properties': { 'type': { 'const': 'cron' } }
                },
                'then': {
                    '$ref': '#/definitions/Cron'
                },

                # 何のtypeにも当てはまらない場合はエラーとする
                # TODO: if-thenの条件式が機能しない、調べてもみたが原因不明
                'else': False
            },
            'Date': {
                'type': 'object',
                'required': [
                    'type',
                    'date'
                ],
                'additionalProperties': False,
                'properties': {
                    'type': {
                        'const': 'date'
                    },
                    'date': {
                        'type': 'string',
                        'format': 'date-time'
                    }
                }
            },
            'Interval': {
                'type': 'object',
                'required': [
                    'type',
                    'start_date',
                    'end_date'
                ],
                'additionalProperties': False,
                'properties': {
                    'type': {
                        'const': 'interval'
                    },
                    'start_date': {
                        'type': 'string',
                        'format': 'date-time'
                    },
                    'end_date': {
                        'type': 'string',
                        'format': 'date-time'
                    },
                    'weeks': {
                        'type': 'integer',
                        'minimum': 0
                    },
                    'days': {
                        'type': 'integer',
                        'minimum': 0
                    },
                    'hours': {
                        'type': 'integer',
                        'minimum': 0
                    },
                    'minutes': {
                        'type': 'integer',
                        'minimum': 0
                    },
                    'seconds': {
                        'type': 'integer',
                        'minimum': 0
                    }
                }
            },
            'Cron': {
                'type': 'object',
                'required': [
                    'type',
                    'start_date',
                    'end_date'
                ],
                'additionalProperties': False,
                'properties': {
                    'type': {
                        'const': 'cron'
                    },
                    'start_date': {
                        'type': 'string',
                        'format': 'date-time'
                    },
                    'end_date': {
                        'type': 'string',
                        'format': 'date-time'
                    },
                    'year': {
                        'type': 'integer',
                        'minimum': 2021,
                        'maximum': 2099
                    },
                    'month': {
                        'type': 'integer',
                        'minimum': 1,
                        'maximum': 12
                    },
                    'week': {
                        'type': 'integer',
                        'minimum': 0,
                        'maximum': 53
                    },
                    'day_of_week': {
                        'type': 'integer',
                        'minimum': 0,
                        'maximum': 6
                    },
                    'day': {
                        'type': 'integer',
                        'minimum': 1,
                        'maximum': 31
                    },
                    'hour': {
                        'type': 'integer',
                        'minimum': 0,
                        'maximum': 23
                    },
                    'minute': {
                        'type': 'integer',
                        'minimum': 0,
                        'maximum': 59
                    },
                    'second': {
                        'type': 'integer',
                        'minimum': 0,
                        'maximum': 60
                    }
                }
            }
        }
    }

    def __init__(self, session, parent:SavableDatum, label:str, runnable_uuid:str, args={}, inputs={}, trigger={}):
        super().__init__(session, parent, SavableDatum.SCHEDULE_TYPE, label)

        # runnableの妥当性を検証する
        self._valid_runnable_or_raise(runnable_uuid)

        # 起動日時指定の書式を検証する
        self._valid_trigger_json_or_raise(trigger)

        # 
        self._path = None

        # runnable: FlowまたはCommandを表す
        # TODO: Commandについては、UUIDでライブラリから取得できるまで対応しない
        self._data = {'runnable':runnable_uuid, 'args':args, 'inputs':inputs, 'trigger':trigger}

        # self._conv_to_utc_datetime(trigger)

        # FlowはFlowCommandに統合するべきかも
        # そうすれば、CommandもFlowもrun()を持ち、かつDBに格納可能なDatumとして統一的に扱える

    def _valid_runnable_or_raise(self, runnable_uuid:str):
        # 存在しないrunnable_uuidが指定された場合は例外を送出する
        from streamcat.store.factory import DatumFactory
        if not DatumFactory(self._session).exists(runnable_uuid):
            raise Exception(f'指定されたrunnable_uuid({runnable_uuid})は存在しません')

        # ゴミ箱にほかしたrunnable_uuidが指定された場合は例外を送出する
        if DatumFactory(self._session).trashed(runnable_uuid):
            raise Exception(f'ゴミ箱にほかされたrunnable_uuid({runnable_uuid})は指定できません')

        # 参照権限が無いrunnable_uuidが指定された場合は例外を送出する
        DatumFactory(self._session).find_by_uuid(runnable_uuid)

    def _valid_trigger_json_or_raise(self, trigger:dict):
        """
        JSONの書式に従っていない場合は例外を送出する
        """
        from jsonschema import validate, ValidationError
        try:
            # validate(trigger, Schedule.TRIGGER_JSON_SCHEMA)
            pass
        except ValidationError as e:
            raise

    def _conv_to_utc_datetime(self, trigger:dict):
        from streamcat.core import SCatBaseModel

        trigger_type = trigger.get('type')
        if trigger_type=='date':
            utc_date = SCatBaseModel.local_time_str_to_datetime(trigger['date'])
            trigger['date'] = utc_date.strftime('%Y-%m-%d %H:%M:%S')

        elif trigger_type=='interval':
            utc_start_date = SCatBaseModel.local_time_str_to_datetime(trigger['start_date'])
            utc_end_date = SCatBaseModel.local_time_str_to_datetime(trigger['end_date'])
            trigger['start_date'] = utc_start_date.strftime('%Y-%m-%d %H:%M:%S')
            trigger['end_date'] = utc_end_date.strftime('%Y-%m-%d %H:%M:%S')

        elif trigger_type=='cron':
            utc_start_date = SCatBaseModel.local_time_str_to_datetime(trigger['start_date'])
            utc_end_date = SCatBaseModel.local_time_str_to_datetime(trigger['end_date'])
            trigger['start_date'] = utc_start_date.strftime('%Y-%m-%d %H:%M:%S')
            trigger['end_date'] = utc_end_date.strftime('%Y-%m-%d %H:%M:%S')

            # TODO: apschdulerのソースでロケール変換してるはずなので探してみる
            #     # Intervals
            #     year=schedule.trigger.get('year'),
            #     month=schedule.trigger.get('month'),
            #     week=schedule.trigger.get('week'),
            #     day_of_week=schedule.trigger.get('day_of_week'),
            #     day=schedule.trigger.get('day'),
            #     hour=schedule.trigger.get('hour'),
            #     minute=schedule.trigger.get('minute'),
            #     second=schedule.trigger.get('second'),
            # )

        else:
            raise Exception(f'Unknown trigger type ! ({trigger_type})')

    @property
    def runnable_uuid(self):
        return self._data.get('runnable')

    @property
    def args(self):
        return self._data.get('args')

    @property
    def inputs(self):
        return self._data.get('inputs')

    @property
    def trigger(self):
        return self._data.get('trigger')

    @Constraints.prohibit_save_on_root
    @Constraints.set_project_role_on_adding
    def save(self):
        """
        Scheduleを保存する
        """
        from . import schedule_manager

        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        from streamcat.store.factory import DatumFactory
        if self.parent_id is None and DatumFactory(self._session).count_root() > 0:
            raise Exception('You can not add another root schedule. A root already exists.')

        try:
            # Dataテーブルにレコードを新規追加する
            self._session.add(self)
            # スケジューラに登録する
            schedule_manager.add(self)
        except Exception as e:
            self._session.rollback()
            if schedule_manager.contains(self.uuid):
                schedule_manager.delete(self.uuid)
            raise e

    def update_data(self, label, runnable_uuid:str, args={}, inputs={}, trigger={}, modifier=None, last_modified_at=None):
        """
        Scheduleのdata列を更新する
        """
        from sqlalchemy import select
        from ..exceptions import OptimisticLockException
        from . import schedule_manager

        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        # runnableの妥当性を検証する
        self._valid_runnable_or_raise(runnable_uuid)

        # 起動日時指定の書式を検証する
        self._valid_trigger_json_or_raise(trigger)

        # 
        # 最終更新時刻を用いた楽観的排他制御
        # 
        stmt = select(Schedule.modified_at).where(Schedule.id==self.id)
        modified_at = self._session.scalars(stmt).one_or_none()
        if modified_at != last_modified_at:
            raise OptimisticLockException(f'スケジュール({self.label})は他ユーザーが編集しているため更新できませんでした')

        try:
            # レコードを更新する
            self._label = new_label
            self._data.update({'runnable':runnable_uuid, 'args':args, 'inputs':inputs, 'trigger':trigger})
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
            # スケジューラに登録されているスケジュールを更新する
            schedule_manager.delete(self.uuid)
            schedule_manager.add(self)
        except Exception as e:
            self._session.rollback()
            raise e

        return self

    def moved(self, parent_uuid, prev_parent_id, modifier=None):
        """
        ゴミ箱へほかされた場合は、スケジューラから削除する
        ゴミ箱から戻された場合は、スケジューラに再登録する
        """
        from . import schedule_manager
        from streamcat.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        trash_folder = factory.load_trash_folder()

        if parent_uuid == trash_folder.uuid:
            # ゴミ箱へほかされた場合は、スケジューラから削除する
            schedule_manager.delete(self.uuid)
        elif parent_uuid != trash_folder.uuid and prev_parent_id == trash_folder.id:
            # ゴミ箱から戻された場合は、スケジューラに再登録する
            schedule_manager.add(self)

        return super().moved(parent_uuid, prev_parent_id, modifier=modifier)

    @Constraints.delete_role_when_isolated
    def delete(self):
        """
        Scheduleを削除する
        """
        from . import schedule_manager

        try:
            # レコードを削除する
            self._session.delete(self)
            # スケジューラから削除する
            schedule_manager.delete(self.uuid)
        except Exception as e:
            self._session.rollback()
            raise e

    def duplicate(self, new_label, new_parent:Datum=None):
        """
        自身の複製を作成して保存する
        """
        # 複製元と同じフォルダに複製を作成する
        parent = new_parent or self.find_parent()
        new_schedule = parent.create_schedule(new_label,
                                              self.runnable_uuid,
                                              self.args,
                                              self.inputs,
                                              self.trigger)
        # ライブラリに保存する
        new_schedule.save()
        return new_schedule

    def to_json(self):
        ret = super().to_json()
        # 
        ret['runnableUUID'] = self._data.get('runnable', {})
        ret['args']    = self._data.get('args', {})
        ret['inputs']  = self._data.get('inputs', {})
        ret['trigger'] = self._data.get('trigger', {})
        # メンバ設定の楽観的排他制御に最終更新時刻を用いる
        ret['modifiedAt'] = self.modified_at.strftime('%Y-%m-%d %H:%M:%S.%f')
        # allowlist
        ret['allowlist']['download'] = False
        return ret
