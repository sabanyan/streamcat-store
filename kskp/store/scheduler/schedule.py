from kskp.core import Datum, Constraints

class Schedule(Datum):

    __mapper_args__ = {
        'polymorphic_identity' : 'schedule'
    }

    # Flow Jsonの定義
    TRIGGER_JSON_SCHEMA = {
        "title" : "Trigger JSON Schema",
        "description" : "This is a schema that define a job launch time.",
        '$schema': 'http://json-schema.org/draft-07/schema#',
        '$ref': '#/definitions/Trigger',
        'definitions': {
            'Trigger': {
                'type': 'object',

                "if": {
                    "properties": { "type": { "const": "date" } }
                },
                "then": {
                    '$ref': '#/definitions/Date'
                },

                "if": {
                    "properties": { "type": { "const": "interval" } }
                },
                "then": {
                    '$ref': '#/definitions/Interval'
                },

                "if": {
                    "properties": { "type": { "const": "cron" } }
                },
                "then": {
                    '$ref': '#/definitions/Cron'
                }
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

    def __init__(self, session, parent:Datum, label:str, runnable_uuid:str, args={}, inputs={}, trigger={}):
        super().__init__(session, parent, Datum.SCHEDULE_TYPE, label)

        # 
        self._path = None
        
        # runnable: FlowまたはCommandを表す
        # TODO: Commandについては、UUIDでライブラリから取得できるまで対応しない
        self._data = {'runnable':runnable_uuid, 'args':args, 'inputs':inputs, 'trigger':trigger}


        self.valid_trigger_json_or_raise()

        self.conv_to_utc_datetime(trigger)

        # FlowはFlowCommandに統合するべきかも
        # そうすれば、CommandもFlowもrun()を持ち、かつDBに格納可能なDatumとして統一的に扱える

    def valid_trigger_json_or_raise(self):
        """
        JSONの書式に従っていない場合は例外を送出する
        """
        from jsonschema import validate, ValidationError
        try:
            validate(self.trigger, Schedule.TRIGGER_JSON_SCHEMA)
        except ValidationError as e:
            raise

    def conv_to_utc_datetime(self, trigger:dict):
        from kskp.core import SCatBaseModel

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
    def runnable(self):
        from kskp.store.factory import DatumFactory
        runnable_uuid = self._data.get('runnable')
        return DatumFactory(self._session).find_by_uuid(runnable_uuid)

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
        from kskp.store.factory import DatumFactory
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
        finally:
            self._session.commit()

    def update_data(self, label, runnable, args={}, inputs={}, trigger={}, modifier=None):
        """
        Scheduleのdata列を更新する
        """
        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        try:
            # レコードを更新する
            self._label = new_label
            self._data = {'runnable':runnable.uuid, 'args':args, 'inputs':inputs, 'trigger':trigger}
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

        return self

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
        finally:
            self._session.commit()

    def to_json(self):
        ret = super().to_json()
        # TODO: 後で必要な属性値を追加する
        return ret
