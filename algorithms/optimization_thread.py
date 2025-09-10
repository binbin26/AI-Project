from PyQt5.QtCore import QThread, pyqtSignal
import time
import random
from algorithms import simulated_annealing as sa
from algorithms import greedy as gr
from algorithms import ant_colony as aco


class OptimizationThread(QThread):
    progress_updated = pyqtSignal(int)
    result_ready = pyqtSignal(dict)
    log_updated = pyqtSignal(str)

    def __init__(self, algorithm_key, problem_data, params):
        super().__init__()
        self.algorithm_key = algorithm_key
        self.problem_data = problem_data
        self.params = params
        self._should_stop = False

    def run(self):
        try:
            start_time = time.time()
            def on_progress(p): self.progress_updated.emit(int(p))
            def on_log(msg): self.log_updated.emit(msg)
            def should_stop(): return self._should_stop

            key = self.algorithm_key
            if key == 'SA':
                result = sa.solve(self.problem_data, self.params, on_progress, on_log, should_stop)
            elif key == 'Greedy':
                result = gr.solve(self.problem_data, self.params, on_progress, on_log, should_stop)
            elif key == 'ACO':
                result = aco.solve(self.problem_data, self.params, on_progress, on_log, should_stop)
            else:
                # fallback hiện có (nếu muốn)
                result = self._fallback_result()

            self.result_ready.emit(result)
        except Exception as exc:
            self.log_updated.emit(f"Lỗi trong quá trình tối ưu: {exc}")

    def terminate(self):
        # Đánh dấu dừng mềm, sau đó gọi terminate gốc để đảm bảo thoát nếu cần
        self._should_stop = True
        return super().terminate()

    @staticmethod
    def _algo_name_from_key(key):
        mapping = {
            'SA': 'Thuật toán SA',
            'Greedy': 'Thuật toán Greedy',
            'ACO': 'Thuật toán ACO'
        }
        return mapping.get(key, key)

    def _build_naive_schedule(self):
        try:
            jobs = int(self.problem_data.get('jobs', 0))
            machines = int(self.problem_data.get('machines', 0))
            processing = self.problem_data.get('processing_times', [])
            if not jobs or not machines or not processing:
                return []

            # Lập lịch tuần tự theo máy, mỗi job qua tất cả máy cùng thứ tự
            machine_available = [0] * machines
            job_available = [0] * jobs
            schedule = []
            for job in range(jobs):
                for machine in range(machines):
                    duration = int(processing[job][machine])
                    start = max(machine_available[machine], job_available[job])
                    schedule.append({
                        'job': job,
                        'machine': machine,
                        'start': start,
                        'duration': duration
                    })
                    machine_available[machine] = start + duration
                    job_available[job] = start + duration
            return schedule
        except Exception:
            return []


