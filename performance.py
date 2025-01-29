from typing import NoReturn
import psutil
from time import perf_counter
from log4py import LoggerManager


logger = LoggerManager.get_logger('performance_metrics')


def get_performance_metric(func):
    def wrapper(*args, **kwargs):
        start_time = perf_counter()
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024 * 1024)

        try:
            return func(*args, **kwargs)
        except Exception as exception:
            logger.error("An error occurred in function (%s): %s", func.__name__, str(exception))
            raise exception
        finally:
            end_time = perf_counter()
            end_memory = process.memory_info().rss / (1024 * 1024)

            total_time = round(end_time - start_time, 2)
            memory_used = round(end_memory - start_memory, 2)

            log_message = (
                f"Process Time: {total_time} seconds | "
                f"Func Name: ({func.__name__}) | "
                f"Memory Used: {memory_used} MB"
            ).upper()

            if total_time > 10:
                logger.critical(log_message)
            elif 4 <= total_time <= 10:
                logger.warning(log_message)
            else:
                logger.info(log_message)

    return wrapper


if __name__ == '__main__':
    @get_performance_metric
    def example_function_short() -> NoReturn:
        sum(range(10**6))

    @get_performance_metric
    def example_function_medium() -> NoReturn:
        sum(range(10**7))


    @get_performance_metric
    def example_function_long() -> NoReturn:
        import time
        time.sleep(12)

    @get_performance_metric
    def example_function_error() -> NoReturn:
        print(0 / 0)

    example_function_short()
    example_function_medium()
    example_function_long()
    example_function_error()
