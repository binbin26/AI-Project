import time, math, random
from algorithms.common import validate_problem_data, safe_log, safe_progress, build_sequential_schedule, compute_makespan

def solve(problem_data, params, on_progress=None, on_log=None, should_stop=lambda: False):
    start = time.time()
    validate_problem_data(problem_data)
    jobs = int(problem_data['jobs']); machines = int(problem_data['machines'])
    processing = problem_data['processing_times']

    # Biểu diễn nghiệm: thứ tự job (list[int])
    current = initial_solution(processing)
    current_cost = makespan_of(current, processing)
    best = list(current)
    best_cost = current_cost

    T = float(params.get('initial_temp', 100.0))
    alpha = float(params.get('cooling_rate', 0.95))
    min_T = float(params.get('min_temp', 0.001))
    max_iter = int(params.get('max_iterations', 1000))

    for it in range(max_iter):
        if should_stop(): 
            safe_log(on_log, "SA: dừng theo yêu cầu."); break
        # Tạo lân cận bằng cách hoán đổi 2 vị trí
        candidate = neighbor_of(current)
        cand_cost = makespan_of(candidate, processing)
        delta = cand_cost - current_cost
        if delta < 0 or random.random() < math.exp(-delta / max(T, 1e-12)):
            current, current_cost = candidate, cand_cost
            if current_cost < best_cost:
                best, best_cost = current[:], current_cost
        T = max(min_T, T * alpha)
        safe_progress(on_progress, int((it + 1) / max_iter * 100))

    # Chuyển nghiệm → schedule
    schedule = to_schedule(best, processing)
    return {
        'algorithm': 'Mô phỏng SA',
        'makespan': int(best_cost),
        'runtime': round(time.time() - start, 3),
        'iterations': it + 1,
        'schedule': schedule
    }

# TODO: hiện thực 4 hàm dưới theo thiết kế của bạn:
def initial_solution(processing):
    jobs = len(processing)
    order = list(range(jobs))
    random.shuffle(order)
    return order

def neighbor_of(order):
    if len(order) < 2:
        return list(order)
    i = random.randrange(0, len(order))
    j = random.randrange(0, len(order))
    if i == j:
        j = (j + 1) % len(order)
    new_order = list(order)
    new_order[i], new_order[j] = new_order[j], new_order[i]
    return new_order

def makespan_of(order, processing):
    # Dựng lịch theo thứ tự job và tính makespan
    jobs = len(processing)
    machines = len(processing[0]) if jobs > 0 else 0
    machine_avail = [0] * machines
    job_avail = [0] * jobs
    max_end = 0
    for j in order:
        for m in range(machines):
            d = int(processing[j][m])
            s = max(machine_avail[m], job_avail[j])
            e = s + d
            machine_avail[m] = e
            job_avail[j] = e
            if e > max_end:
                max_end = e
    return int(max_end)

def to_schedule(order, processing):
    jobs = len(processing)
    machines = len(processing[0]) if jobs > 0 else 0
    machine_avail = [0] * machines
    job_avail = [0] * jobs
    schedule = []
    for j in order:
        for m in range(machines):
            d = int(processing[j][m])
            s = max(machine_avail[m], job_avail[j])
            schedule.append({'job': j, 'machine': m, 'start': s, 'duration': d})
            machine_avail[m] = s + d
            job_avail[j] = s + d
    return schedule