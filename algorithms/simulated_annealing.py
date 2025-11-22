import time
import math
import random
from algorithms.common import validate_problem_data, safe_log, safe_progress, build_sequential_schedule, compute_makespan


def solve(problem_data, params, on_progress=None, on_log=None, should_stop=lambda: False):
    """
    Giải bài toán Job Shop Scheduling bằng thuật toán Simulated Annealing
    
    Args:
        problem_data: Dữ liệu bài toán (jobs, machines, processing_times)
        params: Tham số thuật toán (initial_temp, cooling_rate, min_temp, max_iterations)
        on_progress: Callback để cập nhật tiến trình
        on_log: Callback để ghi log
        should_stop: Callback kiểm tra có nên dừng không
    
    Returns:
        Dictionary chứa kết quả: algorithm, makespan, runtime, iterations, schedule
    """
    start_time = time.time()
    validate_problem_data(problem_data)
    
    num_jobs = int(problem_data['jobs'])
    num_machines = int(problem_data['machines'])
    processing_times = problem_data['processing_times']

    # Khởi tạo nghiệm ban đầu (thứ tự các job)
    current_solution = generate_initial_solution(processing_times)
    current_makespan = calculate_makespan(current_solution, processing_times)
    
    # Lưu nghiệm tốt nhất
    best_solution = current_solution.copy()
    best_makespan = current_makespan

    # Thiết lập tham số SA
    temperature = float(params.get('initial_temp', 100.0))
    cooling_factor = float(params.get('cooling_rate', 0.95))
    min_temperature = float(params.get('min_temp', 0.001))
    max_iterations = int(params.get('max_iterations', 1000))

    # Vòng lặp chính của thuật toán SA
    iteration_count = 0
    for iteration in range(max_iterations):
        iteration_count = iteration + 1
        
        # Kiểm tra điều kiện dừng từ bên ngoài
        if should_stop():
            safe_log(on_log, "Thuật toán SA: Dừng theo yêu cầu người dùng.")
            break
        
        # Tạo nghiệm lân cận bằng cách hoán đổi ngẫu nhiên 2 job
        neighbor_solution = generate_neighbor(current_solution)
        neighbor_makespan = calculate_makespan(neighbor_solution, processing_times)
        
        # Tính độ chênh lệch makespan
        cost_difference = neighbor_makespan - current_makespan
        
        # Quyết định chấp nhận nghiệm mới (Metropolis criterion)
        accept_probability = math.exp(-cost_difference / max(temperature, 1e-12))
        should_accept = (cost_difference < 0) or (random.random() < accept_probability)
        
        if should_accept:
            current_solution = neighbor_solution
            current_makespan = neighbor_makespan
            
            # Cập nhật nghiệm tốt nhất nếu tìm được nghiệm tốt hơn
            if current_makespan < best_makespan:
                best_solution = current_solution.copy()
                best_makespan = current_makespan
        
        # Giảm nhiệt độ (cooling schedule)
        temperature = max(min_temperature, temperature * cooling_factor)
        
        # Cập nhật tiến trình
        progress_percent = int((iteration_count / max_iterations) * 100)
        safe_progress(on_progress, progress_percent)
        
        # Dừng sớm nếu nhiệt độ đã đạt ngưỡng tối thiểu
        if temperature <= min_temperature:
            safe_log(on_log, f"Thuật toán SA: Nhiệt độ đã đạt ngưỡng tối thiểu ({min_temperature:.6f}), dừng sớm.")
            break

    # Chuyển đổi nghiệm tốt nhất thành định dạng schedule
    final_schedule = build_schedule_from_order(best_solution, processing_times)
    
    elapsed_time = round(time.time() - start_time, 3)
    
    return {
        'algorithm': 'Thuật toán SA',
        'makespan': int(best_makespan),
        'runtime': elapsed_time,
        'iterations': iteration_count,
        'schedule': final_schedule
    }


def generate_initial_solution(processing_times):
    """
    Tạo nghiệm ban đầu bằng cách xáo trộn ngẫu nhiên thứ tự các job
    
    Args:
        processing_times: Ma trận thời gian xử lý
    
    Returns:
        List chứa thứ tự các job (nghiệm ban đầu)
    """
    num_jobs = len(processing_times)
    job_sequence = list(range(num_jobs))
    random.shuffle(job_sequence)
    return job_sequence


def generate_neighbor(job_order):
    """
    Tạo nghiệm lân cận bằng cách hoán đổi vị trí của 2 job ngẫu nhiên
    
    Args:
        job_order: Thứ tự hiện tại của các job
    
    Returns:
        Thứ tự mới sau khi hoán đổi
    """
    if len(job_order) < 2:
        return job_order.copy()
    
    # Chọn 2 vị trí ngẫu nhiên để hoán đổi
    pos1 = random.randrange(0, len(job_order))
    pos2 = random.randrange(0, len(job_order))
    
    # Đảm bảo 2 vị trí khác nhau
    if pos1 == pos2:
        pos2 = (pos2 + 1) % len(job_order)
    
    # Tạo bản sao và hoán đổi
    new_order = job_order.copy()
    new_order[pos1], new_order[pos2] = new_order[pos2], new_order[pos1]
    
    return new_order


def calculate_makespan(job_order, processing_times):
    """
    Tính makespan (thời gian hoàn thành tất cả job) cho một thứ tự job cụ thể
    
    Args:
        job_order: Thứ tự các job cần xử lý
        processing_times: Ma trận thời gian xử lý [job][machine]
    
    Returns:
        Makespan (thời gian hoàn thành)
    """
    if not job_order or not processing_times:
        return 0
    
    num_jobs = len(processing_times)
    num_machines = len(processing_times[0]) if num_jobs > 0 else 0
    
    # Theo dõi thời gian sẵn sàng của từng máy và từng job
    machine_ready_time = [0] * num_machines
    job_ready_time = [0] * num_jobs
    
    # Xử lý từng job theo thứ tự
    for job_idx in job_order:
        for machine_idx in range(num_machines):
            processing_duration = int(processing_times[job_idx][machine_idx])
            
            # Thời gian bắt đầu = max(thời gian máy sẵn sàng, thời gian job sẵn sàng)
            start_time = max(machine_ready_time[machine_idx], job_ready_time[job_idx])
            end_time = start_time + processing_duration
            
            # Cập nhật thời gian sẵn sàng
            machine_ready_time[machine_idx] = end_time
            job_ready_time[job_idx] = end_time
    
    # Makespan = thời gian kết thúc lớn nhất
    makespan = max(machine_ready_time) if machine_ready_time else 0
    return int(makespan)


def build_schedule_from_order(job_order, processing_times):
    """
    Xây dựng lịch trình chi tiết từ thứ tự job
    
    Args:
        job_order: Thứ tự các job
        processing_times: Ma trận thời gian xử lý
    
    Returns:
        List các dictionary chứa thông tin: job, machine, start, duration
    """
    if not job_order or not processing_times:
        return []
    
    num_jobs = len(processing_times)
    num_machines = len(processing_times[0]) if num_jobs > 0 else 0
    
    machine_ready_time = [0] * num_machines
    job_ready_time = [0] * num_jobs
    schedule_list = []
    
    # Xây dựng lịch trình cho từng job theo thứ tự
    for job_idx in job_order:
        for machine_idx in range(num_machines):
            processing_duration = int(processing_times[job_idx][machine_idx])
            
            # Tính thời gian bắt đầu
            start_time = max(machine_ready_time[machine_idx], job_ready_time[job_idx])
            
            # Thêm vào lịch trình
            schedule_list.append({
                'job': job_idx,
                'machine': machine_idx,
                'start': start_time,
                'duration': processing_duration
            })
            
            # Cập nhật thời gian sẵn sàng
            end_time = start_time + processing_duration
            machine_ready_time[machine_idx] = end_time
            job_ready_time[job_idx] = end_time
    
    return schedule_list
