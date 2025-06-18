#!/usr/bin/env python3
"""
Простое исправление логики статистики задач
"""

def create_fixed_statistics_function():
    """Возвращает исправленную функцию статистики"""

    fixed_code = '''
            # 3. Анализируем открытые задачи для детальной статистики
            new_tasks = 0
            in_progress = 0
            completed_tasks = 0  # Завершенные среди открытых
            high_priority = 0
            overdue_tasks = 0

            # Отладочная информация - подсчет статусов
            status_counts = {}

            current_date = datetime.now().date()

            for issue in open_issues:
                # Подсчет по статусам - используем точные названия из вашей системы
                if hasattr(issue, 'status') and issue.status:
                    status_name = issue.status.name

                    # Ведем статистику всех статусов для отладки
                    status_counts[status_name] = status_counts.get(status_name, 0) + 1

                    # Новые задачи - РЕАЛЬНЫЕ русские названия статусов
                    if status_name in ['Новая', 'Открыта', 'В очереди']:
                        new_tasks += 1

                    # Завершенные - только статус "Выполнена" среди открытых задач
                    elif status_name == 'Выполнена':
                        completed_tasks += 1

                    # В работе - остальные активные статусы (исключая "Выполнена")
                    elif status_name in ['В работе', 'Запрошено уточнение',
                                       'Протестирована', 'На согласовании', 'На тестировании']:
                        in_progress += 1

                # Подсчет высокоприоритетных задач
                if hasattr(issue, 'priority') and issue.priority:
                    priority_name = issue.priority.name.lower()
                    if any(keyword in priority_name for keyword in [
                        'высокий', 'критический', 'срочный', 'high', 'urgent',
                        'critical', 'важный', 'немедленно', 'immediate'
                    ]):
                        high_priority += 1

                # Подсчет просроченных задач
                if hasattr(issue, 'due_date') and issue.due_date:
                    try:
                        if hasattr(issue.due_date, 'date'):
                            due_date = issue.due_date.date()
                        else:
                            due_date = issue.due_date

                        if due_date < current_date:
                            overdue_tasks += 1
                    except:
                        pass

            execution_time = time.time() - start_time

            statistics = {
                # Основная статистика для интерфейса
                'total_tasks': total_tasks,
                'open_tasks': len(open_issues),
                'new_tasks': new_tasks,
                'in_progress_tasks': in_progress,
                'closed_tasks': completed_tasks,  # ИСПРАВЛЕНО: только "Выполнена" из открытых
                'high_priority_tasks': high_priority,
                'overdue_tasks': overdue_tasks,

                # Дополнительная информация
                'user_info': {
                    'username': current_user.username,
                    'redmine_user_id': redmine_user.id,
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'performance': {
                    'execution_time': round(execution_time, 2),
                    'cache_used': cached_connection is not None,
                    'total_issues_analyzed': total_tasks,
                    'open_issues_analyzed': len(open_issues),
                    'closed_issues_found': len(closed_issues)
                },
                'debug_status_counts': status_counts
            }

            current_app.logger.info(f"Статистика получена за {execution_time:.2f} сек: "
                                 f"Всего={total_tasks}, Открытых={len(open_issues)}, "
                                 f"Новых={new_tasks}, В работе={in_progress}, Завершенных(Выполнена)={completed_tasks}")

            current_app.logger.info(f"Детальная статистика по статусам: {status_counts}")
    '''

    return fixed_code

if __name__ == "__main__":
    print("Исправленная логика статистики:")
    print("=" * 60)
    print("ИЗМЕНЕНИЯ:")
    print("1. completed_tasks вместо len(closed_issues)")
    print("2. Завершенные = только статус 'Выполнена' среди открытых")
    print("3. В работе = исключили 'Выполнена'")
    print("4. Убрана поломанная структура additional_stats")
    print("=" * 60)
    print("\nОжидаемые значения:")
    print("- Новые: 3 (Новая: 2 + Открыта: 1)")
    print("- В работе: 12 (без 'Выполнена')")
    print("- Завершенные: 7 (только 'Выполнена')")
    print("- Всего: 535")
    print("\nПроверка: 3 + 12 + 7 = 22 открытых + 4 паузы + 509 закрытых = 535 ✅")
