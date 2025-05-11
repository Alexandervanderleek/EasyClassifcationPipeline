from PySide6.QtCore import QObject, QRunnable, Signal, Slot, QThreadPool

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    started = Signal(str) 
    finished = Signal(str, bool, object)  
    error = Signal(str, str)  
    progress = Signal(int, int)

class ApiWorker(QRunnable):
    """Worker that handles API requests in a separate thread"""
    
    def __init__(self, api_service, endpoint, method_name, *args, **kwargs):
        super().__init__()
        self.api_service = api_service
        self.endpoint = endpoint
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
    
    @Slot()
    def run(self):
        """Execute the API request in a separate thread"""
        try:
            self.signals.started.emit(self.endpoint)
            
            method = getattr(self.api_service, self.method_name)
            
            result = method(*self.args, **self.kwargs)
            
            success = True
            if isinstance(result, dict) and result.get('error_type'):
                success = False
            
            self.signals.finished.emit(self.endpoint, success, result)
            
        except Exception as e:
            self.signals.error.emit(self.endpoint, str(e))

class ThreadManager:
    """
    Manages thread execution for background tasks
    """
    
    def __init__(self, max_threads=4):
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(max_threads)
    
    def start_worker(self, worker):
        """Start a worker in the thread pool"""
        self.thread_pool.start(worker)
    
    def clear(self):
        """Clear all pending tasks"""
        self.thread_pool.clear()
    
    def wait_for_done(self, msecs=None):
        """Wait for all tasks to complete"""
        return self.thread_pool.waitForDone(msecs)