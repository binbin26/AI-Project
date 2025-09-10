import time, random
from algorithms.common import validate_problem_data, safe_log, safe_progress, compute_makespan

def solve(problem_data, params, on_progress=None, on_log=None, should_stop=lambda: False):
    start = time.time()
    validate_problem_data(problem_data)
    jobs = int(problem_data['jobs']); machines = int(problem_data['machines'])
    processing = problem_data['processing_times']
    strategy = params.get('strategy', 'SPT')

    # Ví dụ: sắp xếp job theo tổng thời gian xử lý (SPT/LPT/Random)
    job_order = list(range(jobs))
    if strategy == 'SPT':
        job_order.sort(key=lambda j: sum(processing[j]))
    elif strategy == 'LPT':
        job_order.sort(key=lambda j: -sum(processing[j]))
    else:
        random.shuffle(job_order)

    # Dựng schedule từ thứ tự job
    machine_avail = [0] * machines
    job_avail = [0] * jobs
    schedule = []
    for idx, j in enumerate(job_order):
        if should_stop(): 
            safe_log(on_log, "Greedy: dừng theo yêu cầu."); break
        for m in range(machines):
            d = int(processing[j][m])
            s = max(machine_avail[m], job_avail[j])
            schedule.append({'job': j, 'machine': m, 'start': s, 'duration': d})
            machine_avail[m] = s + d; job_avail[j] = s + d
        safe_progress(on_progress, int((idx + 1) / max(len(job_order),1) * 100))

    ms = compute_makespan(schedule)
    return {
        'algorithm': 'Thuật toán Greedy',
        'makespan': int(ms),
        'runtime': round(time.time() - start, 3),
        'iterations': len(job_order),
        'schedule': schedule
    }