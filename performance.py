import psutil
from time import perf_counter


def get_performance_metric(func):
    def wrapper(*args, **kwargs):
        start_time = perf_counter()
        process = psutil.Process()  # Aktif işlemi alır
        start_memory = process.memory_info().rss / (1024 * 1024)  # Başlangıç RAM kullanımını MB cinsinden alır

        try:
            return func(*args, **kwargs)
        except Exception as exception:
            raise exception
        finally:
            end_time = perf_counter()
            end_memory = process.memory_info().rss / (1024 * 1024)  # Bitiş RAM kullanımını MB cinsinden alır

            total_time = round(end_time - start_time, 2)
            memory_used = round(end_memory - start_memory, 2)
            print("Process Time: {} seconds | Func Name: ({}) | Memory Used: {} MB".format(total_time, func.__name__, memory_used).upper())
    return wrapper
