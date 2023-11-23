from sql import SQL

db = SQL("sqlite:///vedDB.db")


def get_vedomosti(id=None):
    if id:
        return db.execute(
            "SELECT vedomosti.id, vedomosti.group_id, vedomosti.discipline, vedomosti.control_type, vedomosti.name_of_ekzaminator, vedomosti.hours_total, vedomosti.control_date, groups.name as g_name, facultets.name as f_name FROM vedomosti LEFT JOIN groups on vedomosti.group_id = groups.id LEFT JOIN facultets ON groups.facultet = facultets.id WHERE vedomosti.id = ?;",
            id,
        )
    else:
        return db.execute(
            "SELECT vedomosti.id, vedomosti.group_id, vedomosti.discipline, vedomosti.control_type, vedomosti.name_of_ekzaminator, vedomosti.hours_total, vedomosti.control_date, groups.name as g_name, facultets.name as f_name FROM vedomosti LEFT JOIN groups on vedomosti.group_id = groups.id LEFT JOIN facultets ON groups.facultet = facultets.id;"
        )


def get_students(ved_id=None):
    return db.execute(
        "SELECT vedomosti.id, students.student_number, students.full_name, results.result FROM vedomosti LEFT JOIN groups ON groups.id = vedomosti.group_id LEFT JOIN students ON students.group_id = groups.id LEFT JOIN results ON students.id = results.student_id and vedomosti.id = results.vedomost_id WHERE vedomosti.id = ?;",
        ved_id,
    )


def get_sprav_result():
    return db.execute("SELECT name FROM sprav_result;")


def update_result(ved_id=None, stud_id=None, result=None):
    try:
        if (
            ved_id is not None
            and stud_id is not None
            and isinstance(ved_id, int)
            and isinstance(stud_id, int)
            and result is not None
            and len(result) > 0
        ):
            res = db.execute(
                "SELECT * FROM results WHERE vedomost_id = ? AND student_id = ?;",
                ved_id,
                stud_id,
            )
            if len(res) == 0:
                db.execute(
                    "INSERT INTO results (vedomost_id, student_id, result) VALUES (?,?,?);",
                    ved_id,
                    stud_id,
                    result,
                )
            else:
                db.execute(
                    "UPDATE results SET result = ? WHERE vedomost_id = ? AND student_id = ?;",
                    result,
                    ved_id,
                    stud_id,
                )
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def get_history():
    return db.execute('SELECT history.id, history.action, history.details, history.dt FROM history;')


def update_history(action, details, dt):
    try:
        db.execute('INSERT INTO history (action, details, dt) VALUES (?, ?, ?)', action, details, dt)
        return True
    except Exception as e:
        print(f"An error in update_history() occurred: {e}")
        return False
