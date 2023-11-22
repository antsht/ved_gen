from sql import SQL


db = SQL("sqlite:///vedDB.db")

def get_vedomosti(id=None):
    if id:
        return db.execute("SELECT vedomosti.id, vedomosti.group_id, vedomosti.discipline, vedomosti.control_type, vedomosti.name_of_ekzaminator, vedomosti.hours_total, vedomosti.control_date, groups.name as g_name, facultets.name as f_name FROM vedomosti LEFT JOIN groups on vedomosti.group_id = groups.id LEFT JOIN facultets ON groups.facultet = facultets.id WHERE vedomosti.id = ?;", id)
    else:
        return db.execute("SELECT vedomosti.id, vedomosti.group_id, vedomosti.discipline, vedomosti.control_type, vedomosti.name_of_ekzaminator, vedomosti.hours_total, vedomosti.control_date, groups.name as g_name, facultets.name as f_name FROM vedomosti LEFT JOIN groups on vedomosti.group_id = groups.id LEFT JOIN facultets ON groups.facultet = facultets.id;")