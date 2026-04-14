import concurrent.futures

# Global thread pool for processing resumes asynchronously without blocking the main Flask process
# For a huge enterprise app, this would be replaced by Celery + Redis, 
# but ThreadPoolExecutor serves perfectly as an in-memory async ATS task queue.
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def run_async_task(func, *args, **kwargs):
    """
    Submits a computationally heavy function (like BERT embeddings) 
    to be executed in the background thread pool.
    """
    future = executor.submit(func, *args, **kwargs)
    return future
