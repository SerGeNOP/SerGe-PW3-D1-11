import sys
import requests


base_url = "https://api.trello.com/1/{}"
auth_params = {
    'key': "650c62368c7e07c043cc6967acf1dd5f",
    'token': "7b394e02b7a979489ff61faac8e77a004ccaf4f9b34f9e0ee24266470b6062f0", }
board_id = "7g9VidRl"


def read():
    # Получим данные всех колонок на доске:
    column_data = requests.get(base_url.format('boards') + '/' + board_id + '/lists', params=auth_params).json()

    # Теперь выведем название каждой колонки и всех заданий, которые к ней относятся:
    for column in column_data:
        print(column['name'])
        # Получим данные всех задач в колонке и перечислим все названия
        task_data = requests.get(base_url.format('lists') + '/' + column['id'] + '/cards', params=auth_params).json()
        if not task_data:
            print('\t' + 'Нет задач!')
            continue
        for task in task_data:
            print('\t' + task['name'])
    for column in column_data:
        task_in_title(column)
    repeated_tasks()


def create(name, column_name):
    # Получим данные всех колонок на доске
    column_data = requests.get(base_url.format('boards') + '/' + board_id + '/lists', params=auth_params).json()

    # Переберём данные обо всех колонках, пока не найдём ту колонку, которая нам нужна
    for column in column_data:
        if column['name'] == column_name:
            # Создадим задачу с именем _name_ в найденной колонке
            requests.post(base_url.format('cards'), data={'name': name, 'idList': column['id'], **auth_params})
            task_in_title(column)
            break


def move(name, column_name):
    # Получим данные всех колонок на доске
    column_data = requests.get(base_url.format('boards') + '/' + board_id + '/lists', params=auth_params).json()

    # Среди всех колонок нужно найти задачу по имени и получить её id
    task_id = None
    for column in column_data:
        column_tasks = requests.get(base_url.format('lists') + '/' + column['id'] + '/cards',
                                     params=auth_params).json()
        for task in column_tasks:
            if task['name'] == name:
                task_id = task['id']
                break
        if task_id:
            break

            # Теперь, когда у нас есть id задачи, которую мы хотим переместить
    # Переберём данные обо всех колонках, пока не найдём ту, в которую мы будем перемещать задачу
    for column in column_data:
        if column['name'] == column_name:
            # И выполним запрос к API для перемещения задачи в нужную колонку
            requests.put(base_url.format('cards') + '/' + task_id + '/idList',
                          data={'value': column['id'], **auth_params})
            break
    for column in column_data:
        task_in_title(column)


def clean_column_name(mixed_name):
    """ Функция принимает строку с именем, в котором может быть в конце число в скобках
        Определяем есть ли число, добываем его и возвращаем отдельно имя и отдельно число.
     """
    pos1 = mixed_name.find('(')
    number = 0
    if pos1 == -1:
        clean_name = mixed_name
    else:
        clean_name = mixed_name[:pos1].strip(' ')
        number = (mixed_name[(pos1 + 1):].strip(')')) * 1   # переводим строку в int
    return clean_name, number


def task_in_title(column_chng):
    """ Функция производит подсчет карточек в колонке и добавляет число к названию колонки"""

    # берем все карточки из запрашиваемой колонки
    column_tasks_ = requests.get(base_url.format('lists') + '/' + column_chng['id'] + '/cards',
                                 params=auth_params).json()
    # считаем количество задач в карточке
    task_counter = len(column_tasks_)
    clean_name, old_task_counter = clean_column_name(column_chng['name'])
    new_name = clean_name
    if not (old_task_counter == task_counter):
        new_name = clean_name + " (" + str(task_counter) + ")"
    if task_counter == 0:
        new_name = clean_name
    requests.put(base_url.format('lists') + '/' + column_chng['id'] + '/', data={'name': new_name, **auth_params})


def create_list(name_list):
    """ Функция создает новую колонку на текущей доске"""
    current_board = requests.get(base_url.format('boards') + '/' + board_id, params=auth_params).json()
    requests.post(base_url.format('lists'), data={'name': name_list, 'idBoard': current_board['id'], 'pos': "bottom", **auth_params})

def repeated_tasks():
    """ Функция проверяет задачи на совпадение на всей доске
        и при совпадении запрашивает перемещение или удаление
    """
    list_rep = []       #сюда поместим task_id, имя задачи и имя столбца, в котором задача
    # заполним list_rep
    column_data = requests.get(base_url.format('boards') + '/' + board_id + '/lists', params=auth_params).json()
    # Теперь выведем название каждой колонки и всех заданий, которые к ней относятся:
    for column in column_data:
        # Получим данные всех задач в колонке и перечислим все названия
        task_data = requests.get(base_url.format('lists') + '/' + column['id'] + '/cards', params=auth_params).json()
        if not task_data:
             continue
        for task in task_data:
            clean_name, _ = clean_column_name(column['name'])
            list_rep.append([task['id'], task['name'], clean_name])

        #удалим совпадения через запрос пользователю в консоль
        for task1 in list_rep:
            flag = 0 #опущенный флаг показывает необходимость перечитать эталонную задачу для сравнения (task1)
            for task2 in list_rep:
                if task1[0] == task2[0]:
                    continue
                elif task1[1] == task2[1]:
                    while True:
                        print(f"\nСовпадение задачи {task1[1]} в столбцах \n1: {task1[2]} \n2: {task2[2]}")
                        choice = int(input("\nВведите цифру из какого столбца удалить задачу:"))
                        if choice == 1:
                            requests.delete(base_url.format('cards') + '/' + task1[0], params=auth_params)
                            list_rep.remove(task1)
                            flag = 0            #внесено изменение в список задач - перечитываем этот список заново
                            break
                        elif choice == 2:
                            requests.delete(base_url.format('cards') + '/' + task2[0], params=auth_params)
                            list_rep.remove(task2)
                            flag = 0        #внесено изменение в список задач - перечитываем этот список заново
                            break
                else:
                    flag = 1
                if not flag:
                    break
    for column in column_data:
        task_in_title(column)

if __name__ == "__main__":
    if len(sys.argv) <= 2:
        read()
    elif sys.argv[1] == 'create':
        create(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'move':
        move(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'newlist':
        create_list(sys.argv[2])
