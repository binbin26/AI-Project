from typing import Any, Dict, List


def safe_log(on_log, message: str) -> None:
    if on_log:
        on_log(message)


def safe_progress(on_progress, percent: int) -> None:
    if on_progress:
        on_progress(int(max(0, min(100, percent))))


def validate_problem_data(problem_data: Dict[str, Any]) -> None:
    jobs = int(problem_data['jobs'])
    machines = int(problem_data['machines'])
    processing = problem_data['processing_times']
    assert jobs > 0 and machines > 0
    assert isinstance(processing, list) and len(processing) == jobs
    for row in processing:
        assert isinstance(row, list) and len(row) == machines
        for v in row:
            assert int(v) > 0


def build_sequential_schedule(processing: List[List[int]]) -> List[Dict[str, int]]:
    jobs = len(processing)
    machines = len(processing[0]) if jobs > 0 else 0
    machine_avail = [0] * machines
    job_avail = [0] * jobs
    schedule: List[Dict[str, int]] = []
    for j in range(jobs):
        for m in range(machines):
            d = int(processing[j][m])
            s = max(machine_avail[m], job_avail[j])
            schedule.append({'job': j, 'machine': m, 'start': s, 'duration': d})
            machine_avail[m] = s + d
            job_avail[j] = s + d
    return schedule


def compute_makespan(schedule: List[Dict[str, int]]) -> int:
    if not schedule:
        return 0
    return int(max(item['start'] + item['duration'] for item in schedule))


