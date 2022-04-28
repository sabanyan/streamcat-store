import warnings
from streamcat.core import Datum
from .schedule import Schedule

class ScheduleManager():
    """
    スケジュールを管理する
    """
    def __init__(self):
        import pytz
        from apscheduler.jobstores.memory import MemoryJobStore
        from apscheduler.executors.pool import ThreadPoolExecutor
        from apscheduler.schedulers.background import BackgroundScheduler

        jobstores = {
            # NOTE:
            # SQLAlchemyJobStoreを用いるとエラーになるので、MemoryJobStoreを用いる、
            # 'default': SQLAlchemyJobStore(engine, tableschema=SCHEMA_NAME, tablename='schedules', metadata=BaseModel.metadata)
            'default': MemoryJobStore()
        }

        executors = {
            'default': ThreadPoolExecutor(20)
        }

        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }

        # スケジューラを作成する
        self.scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=pytz.utc)

        # スケジューラを起動する
        self.scheduler.start()

    def load_from_library(self, datumFactory):
        """
        ライブラリにある全てのスケジュールをスケジューラに登録する
        """
        # ゴミ箱の中を除く全てのスケジュールを取得する
        schedules = datumFactory.find_all(type=Datum.SCHEDULE_TYPE, except_trash=True)
        for schedule in schedules:
            if not self.contains(schedule.uuid):
                try:
                    self.add(schedule)
                    import pprint
                    pprint.pprint(schedule._data) 
                except Exception as e:
                    # スケジュールの登録に失敗しても処理を続行する
                    warnings.warn(f'Failed to load Schedule({schedule.label}). {e}')

    def add(self, schedule:Schedule):
        """
        スケジューラにスケジュールを登録する
        """
        # スケジュール起動時に、その処理内でFactoryを作成する(トランザクションを開く)必要がある
        def run(args:dict, inputs:dict):
            from streamcat.store.factory import Factory
            # Scheduleの作成者の権限でrunnableを実行する
            with Factory(user=schedule.creator) as factory:
                runnable = factory.data.find_by_uuid(schedule.runnable_uuid)
                if runnable.type == Datum.FLOW_TYPE:
                    # TODO: streamcat-storeとstreamcat-engineの循環参照になってしまう
                    # Flowはengineへ引っ越した方がいいのだろうか?
                    # それともScheduleManagerがengineへ引っ越した方がいいのだろうか?
                    from streamcat.engine import FlowCommand
                    command = FlowCommand(runnable)
                else:
                    command = runnable
                # コマンドを実行する
                return command.run(args, inputs)

        trigger_type = schedule.trigger.get('type')
        if trigger_type=='date':
            self.scheduler.add_job(
                run,
                kwargs={'args':schedule.args,'inputs':schedule.inputs},
                id=schedule.uuid,
                # Tirggers: date, interval, cron
                trigger='date',
                run_date=schedule.trigger['date']
            )

        elif trigger_type=='interval':
            self.scheduler.add_job(
                run,
                kwargs={'args':schedule.args,'inputs':schedule.inputs},
                id=schedule.uuid,
                # Tirggers: date, interval, cron
                trigger='interval',
                # start and end times
                start_date=schedule.trigger['start_date'],
                end_date=schedule.trigger['end_date'],
                # Intervals
                weeks=schedule.trigger.get('weeks', 0),
                days=schedule.trigger.get('days', 0),
                hours=schedule.trigger.get('hours', 0),
                minutes=schedule.trigger.get('minutes', 0),
                seconds=schedule.trigger.get('seconds', 0)
            )

        elif trigger_type=='cron':
            self.scheduler.add_job(
                run,
                kwargs={'args':schedule.args,'inputs':schedule.inputs},
                id=schedule.uuid,
                # Tirggers: date, interval, cron
                trigger='cron',
                # start and end times
                start_date=schedule.trigger['start_date'],
                end_date=schedule.trigger['end_date'],
                # datetime
                year=schedule.trigger.get('year'),
                month=schedule.trigger.get('month'),
                week=schedule.trigger.get('week'),
                day_of_week=schedule.trigger.get('day_of_week'),
                day=schedule.trigger.get('day'),
                hour=schedule.trigger.get('hour'),
                minute=schedule.trigger.get('minute'),
                second=schedule.trigger.get('second'),
                timezone=schedule.trigger.get('timezone')
            )

        else:
            raise Exception(f'Unknown trigger type ({trigger_type})')

    def contains(self, schedule_uuid):
        return self.scheduler.get_job(schedule_uuid) is not None

    def delete(self, schedule_uuid):
        """
        スケジューラからスケジュールを削除する
        """
        if self.contains(schedule_uuid):
            self.scheduler.remove_job(schedule_uuid)
