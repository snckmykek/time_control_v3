import sqlite3
from datetime import datetime

from kivy.clock import Clock


class Database(object):

    def __init__(self):
        self.con = sqlite3.connect('database_timecontrol.db')
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()
        self.sqlite_create_db()

    def sqlite_create_db(self):

        self.cur.execute('CREATE TABLE IF NOT EXISTS tasks('
                         'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                         'parent_id INTEGER DEFAULT 0,'
                         'name TEXT DEFAULT "",'
                         'search TEXT DEFAULT "",'
                         'FOREIGN  KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE)'
                         )
        # todo: РАзобраться почему не удаляются подчиненные, когда удаляется родитель

        self.cur.execute('CREATE TABLE IF NOT EXISTS task_labels('
                         'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                         'task_id INTEGER,'
                         'name TEXT DEFAULT "",'
                         'search TEXT DEFAULT "",'
                         'FOREIGN  KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE)'
                         )
        self.cur.execute('CREATE TABLE IF NOT EXISTS current_tasks('
                         'task_id INTEGER NOT NULL PRIMARY KEY,'
                         'label_id INTEGER DEFAULT 0,'
                         'date_start DATETIME,'
                         'is_active BOOLEAN DEFAULT False,'
                         'priority TINYINT DEFAULT 4,'
                         'duration INT DEFAULT 1800,'
                         'passed_time INT DEFAULT 1800,'
                         'time_on_breaks INT DEFAULT 0,'
                         'remind_time DATETIME DEFAULT NULL,'
                         'reminded BOOLEAN DEFAULT False,'
                         'FOREIGN  KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,'
                         'FOREIGN  KEY (label_id) REFERENCES task_labels(id) ON DELETE CASCADE)'
                         )
        self.cur.execute('CREATE TABLE IF NOT EXISTS completed_tasks('
                         'task_id INTEGER NOT NULL,'
                         'label_id INTEGER NOT NULL,'
                         'date_start DATETIME,'
                         'date_finish DATETIME,'
                         'time_on_breaks INT DEFAULT 0,'
                         'FOREIGN  KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,'
                         'FOREIGN  KEY (label_id) REFERENCES task_labels(id) ON DELETE CASCADE)'
                         )
        self.cur.execute('CREATE TABLE IF NOT EXISTS task_comments('
                         'task_id INTEGER NOT NULL,'
                         'label_id INTEGER NOT NULL,'
                         'comment TEXT,'
                         'completed BOOLEAN DEFAULT False,'
                         'FOREIGN  KEY (task_id) REFERENCES current_tasks(task_id) ON DELETE CASCADE,'
                         'FOREIGN  KEY (label_id) REFERENCES task_labels(id) ON DELETE CASCADE)'
                         )

        self.cur.execute('CREATE TABLE IF NOT EXISTS shorttasks('
                         'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                         'name TEXT DEFAULT "",'
                         'count INTEGER DEFAULT 0,'
                         'qty INTEGER DEFAULT 1,'
                         'priority TINYINT DEFAULT 4,'
                         'remind_time DATETIME,'
                         'reminded BOOLEAN,'
                         'search TEXT DEFAULT "")'
                         )

        self.cur.execute('CREATE TABLE IF NOT EXISTS completed_shorttasks('
                         'shorttask_id INTEGER PRIMARY KEY AUTOINCREMENT,'
                         'count INTEGER DEFAULT 0,'
                         'qty INTEGER DEFAULT 1,'
                         'priority TINYINT DEFAULT 4,'
                         'FOREIGN  KEY (shorttask_id) REFERENCES shorttasks(id) ON DELETE CASCADE)'
                         )

    def create_new_task(self, task_name, parent_id=0):
        if task_name == "":
            return

        self.cur.execute('SELECT id FROM tasks WHERE search = "{}"'.format(task_name.upper()))

        if len(self.cur.fetchall()) != 0:
            return

        self.cur.execute(f'INSERT INTO tasks VALUES(NULL, {parent_id}, "{task_name}", "{task_name.upper()}")')
        self.con.commit()

    def create_new_shorttask(self, task_name, qty=1, priority=0, remind_time=0):
        if task_name == "":
            return

        self.cur.execute('SELECT id FROM shorttasks WHERE search = "{}"'.format(task_name.upper()))

        if len(self.cur.fetchall()) != 0:
            return

        self.cur.execute(
            f"""
            INSERT INTO 
                shorttasks 
            VALUES(
                NULL, 
                "{task_name}", 
                0, 
                {qty}, 
                {priority}, 
                {remind_time}, 
                False, 
                "{task_name.upper()}")
            """)
        self.con.commit()

    def update_task(self, task_id, task_name, parent_id=0):
        if not task_id or not task_name:
            return

        self.cur.execute(
            f"""
            UPDATE 
                tasks 
            SET 
                name = "{task_name}",
                parent_id = {parent_id}
            WHERE
                id = {task_id}
            """
                         )
        self.con.commit()

    def update_shorttask(self, task_id, task_name):
        if not task_id or not task_name:
            return

        self.cur.execute(
            f"""
            UPDATE 
                shorttasks 
            SET 
                name = "{task_name}"
            WHERE
                id = {task_id}
            """
                         )
        self.con.commit()

    def tasks(self, search=""):
        self.cur.execute(
            """
            SELECT 
                tasks.id, 
                tasks.name, 
                tasks_parents.id as parent_id,
                tasks_parents.name as parent_name
            FROM
                tasks
            LEFT JOIN tasks as tasks_parents
                ON tasks.parent_id = tasks_parents.id
            """
            + ("" if not search else f"""
            WHERE 
                tasks.search LIKE "%{search.upper()}%"
            """)
            +
            """
            LIMIT 5
            """
        )

        return self.cur.fetchall()

    def tasks_by_parent_id(self, parent_id):
        self.cur.execute(
            """
            SELECT 
                tasks.id, 
                tasks.name, 
                tasks_parents.id as parent_id,
                tasks_parents.name as parent_name,
                tasks.id IN (SELECT task_id FROM current_tasks) as added
            FROM
                tasks
            LEFT JOIN tasks as tasks_parents
                ON tasks.parent_id = tasks_parents.id
            LEFT JOIN current_tasks as current_tasks
                ON tasks.id = current_tasks.task_id
            WHERE 
            """
            + (f"tasks.parent_id = {parent_id}" if parent_id is not None else "tasks.parent_id IS NULL")
        )

        return self.cur.fetchall()

    def current_tasks(self):
        self.cur.execute(
            """
            SELECT
                tasks_params.id,
                tasks_params.name,
                IFNULL(tasks_params.parent_name, "") as parent_name,
                current_tasks.label_id,
                current_tasks.date_start,
                current_tasks.is_active,
                current_tasks.priority,
                current_tasks.passed_time,
                current_tasks.duration,
                current_tasks.time_on_breaks,
                current_tasks.remind_time,
                current_tasks.reminded
            FROM
                current_tasks
            LEFT JOIN
                (SELECT 
                    tasks.id, 
                    tasks.name, 
                    tasks_parents.name as parent_name
                FROM
                    tasks
                LEFT JOIN tasks as tasks_parents
                    ON tasks.parent_id = tasks_parents.id) as tasks_params
                ON current_tasks.task_id = tasks_params.id
            ORDER BY
                current_tasks.priority
            """
        )
        return self.cur.fetchall()

    def get_task(self, task_id):
        self.cur.execute(
            f"""
            SELECT
                tasks.id as id, 
                tasks.name as name, 
                tasks.parent_id as parent_id,
                tasks_parents.name as parent_name,
                current_tasks.date_start as date_start,
                current_tasks.passed_time as passed_time,
                current_tasks.is_active as is_active,
                current_tasks.priority as priority,
                current_tasks.duration as duration,
                current_tasks.time_on_breaks as time_on_breaks,
                current_tasks.remind_time as remind_time,
                current_tasks.reminded as reminded
            FROM
                tasks
            LEFT JOIN tasks as tasks_parents
                ON tasks.parent_id = tasks_parents.id
            LEFT JOIN current_tasks
                ON tasks.id = current_tasks.task_id
            WHERE
                tasks.id = {task_id}
            LIMIT 1
            """
        )

        try:
            return self.cur.fetchall()[0]
        except IndexError:
            return None

    def get_shorttask(self, task_id):
        self.cur.execute(
            f"""
            SELECT
                id, 
                name,
                count,
                qty,
                priority,
                remind_time,
                reminded 
            FROM
                shorttasks
            WHERE
                id = {task_id}
            LIMIT 1
            """
        )

        try:
            return self.cur.fetchall()[0]
        except IndexError:
            return None

    def shorttasks(self):
        self.cur.execute(
            """
            SELECT
                id, 
                name,
                count,
                qty,
                priority,
                remind_time,
                reminded
            FROM
                shorttasks
            ORDER BY
                priority
            """
        )
        return self.cur.fetchall()

    def set_shorttasks_count(self, shorttask_id, value):
        self._set_values("shorttasks", {'count': value}, {'id': shorttask_id})

    def _set_values(self, table, values: dict, conditions: dict = None):
        """Отправляет UPDATE-запрос в БД.

        :param table: str
            Имя таблицы
        :param values: dict
            Словарь со значениями, которые надо установить {колонка: значение}
        :param conditions: dict
            Словарь с условиями для отбора строк {колонка: значение}
        :return:
        """

        if not table or not values:
            return
        if not conditions:
            conditions = dict()

        request = f"""
            UPDATE 
                {table}"""

        _ = False
        for key, val in values.items():
            if not _:
                _ = True
                request += f"""
            SET"""
            else:
                request += ","
            request += f'''
                {key} = "{val}"'''

        _ = False
        for key, val in conditions.items():
            if not _:
                _ = True
                request += f"""
            WHERE
                """
            else:
                request += """
                AND """

            request += f'{key} = "{val}"'

        self.cur.execute(request)
        Clock.schedule_once(lambda *args: self.con.commit())

    def set_active(self, task_id, label_id, is_active):
        self.cur.execute(
            f"""
            UPDATE
               current_tasks
            SET 
                is_active = {is_active}
            """
            + f', date_start = "{datetime.now()}"' if is_active else ""
            + f"""
            WHERE
                task_id = "{task_id}" AND label_id = "{label_id}"
            """
        )
        self.con.commit()

    def task_params(self, task_id):
        params = dict.fromkeys(['name', 'duration', 'comments'])

        self.cur.execute(
            f"""
            SELECT
                tasks.name,
                current_tasks.duration
            FROM
                tasks
            LEFT JOIN current_tasks
                ON tasks.id = current_tasks.task_id
            WHERE
                tasks.id = {task_id}
            """
        )

        task = self.cur.fetchall()[0]
        params['name'] = task[0]
        params['duration'] = task[1]

        self.cur.execute(
            f"""
            SELECT
                comment
            FROM
                task_comments
            WHERE
                task_id = {task_id}
            """
        )

        params['comments'] = [row[0] for row in self.cur.fetchall()]

        return params

    def add_task_to_current(self, task_id, label_id=0, date_start=datetime.now(), is_active=True, priority=1, duration=1800):

        self.cur.execute(
            f"""
            SELECT
                COUNT(*)
            FROM
                current_tasks
            WHERE
                task_id = {task_id}
            """
        )

        if self.cur.fetchall()[0][0]:
            pass
        else:
            self.cur.execute(
                f"""
                INSERT INTO
                    current_tasks
                VALUES({",".join([str(task_id),
                                  str(label_id),
                                  f'"{date_start}"',
                                  str(is_active),
                                  str(priority),
                                  str(duration),
                                  str(0),
                                  "NULL",
                                  "NULL",
                                  "NULL",
                                  ])})
                """)

            self.con.commit()

    def save_break_time(self, task_id, break_time, label_id=0):
        self.cur.execute(
            f"""
            UPDATE
                current_tasks
            SET
                time_on_breaks = IFNULL(time_on_breaks, 0) + {break_time}
            WHERE
                task_id = "{task_id}"
                AND label_id = "{label_id}"
            """
        )
        self.con.commit()

    def remove_current_task(self, task_id):

        self.cur.execute('DELETE FROM current_tasks WHERE task_id = "{}"'.format(task_id))
        self.con.commit()

    def delete_task(self, task_id):

        self.cur.execute(f'DELETE FROM tasks WHERE id = {task_id}')

        self.cur.execute(f'DELETE FROM current_tasks WHERE task_id = {task_id}')  # todo: понять поч не удаляет автоматом по ключу

        self.con.commit()

    def delete_shorttask(self, task_id):

        self.cur.execute(f'DELETE FROM shorttasks WHERE id = {task_id}')

        self.con.commit()

    def remove_completed_action(self, action, period_start, period_finish):

        self.cur.execute('DELETE FROM completed_tasks WHERE action = "{}" AND '
                         'date_start BETWEEN "{}" AND "{}"'.format(action, period_start, period_finish))

        self.con.commit()

    def save_completed_action(self, task_id, label_id=0):

        self.cur.execute(
            f"""
            UPDATE
                current_tasks
            SET
                is_active = "{False}",
                passed_time = passed_time + CAST( (julianday("now", "localtime") - julianday(date_start))*3600*24 AS int)
            WHERE
                task_id = "{task_id}"
                AND label_id = "{label_id}"
            """
        )

        self.cur.execute(f'SELECT date_start, time_on_breaks FROM current_tasks '
                         f'WHERE task_id = "{task_id}" AND label_id = "{label_id}"')

        try:
            result_row = self.cur.fetchall()[0]
            date_start = result_row['date_start']
            time_on_breaks = result_row['time_on_breaks']
        except IndexError:
            self.con.commit()
            return

        delta = (datetime.now() - datetime.strptime(date_start, '%Y-%m-%d %H:%M:%S.%f')).total_seconds()
        if delta < 5:
            return

        self.cur.execute(f'INSERT INTO completed_tasks VALUES("{task_id}", "{label_id}", '
                         f'"{date_start}", "{datetime.now()}", "{time_on_breaks}")')

        self.con.commit()

    def results(self, date_start, date_finish, show_variant):

        if show_variant == 'in total':
            self.cur.execute('SELECT task_id, SUM(CAST((JulianDay(date_finish) - JulianDay(date_start))'
                             '* 24 * 60 * 60 As Integer)) FROM completed_tasks '
                             'WHERE date_start BETWEEN "{}" AND "{}"'
                             'GROUP BY task_id'.format(date_start, date_finish))
        elif show_variant == 'in detail':
            self.cur.execute('SELECT action, CAST((JulianDay(date_finish) - JulianDay(date_start))'
                             '* 24 * 60 * 60 As Integer), date_start, date_finish FROM completed_tasks '
                             'WHERE date_start BETWEEN "{}" AND "{}"'.format(date_start, date_finish))
        else:
            print("Ошибка 1 db_requests.py")

        return self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.con.close()


db = Database()
# db.task_params(1)
