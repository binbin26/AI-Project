# gui/widgets.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel, 
    QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, 
    QTableWidget, QTableWidgetItem, QTextEdit, QProgressBar, QCheckBox,
    QFileDialog, QMessageBox, QScrollArea, QTableWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from gui.charts import GanttChart
import json
import numpy as np
import pandas as pd


class ResultsWidget(QWidget):
    """Widget hiển thị kết quả, lịch sử và biểu đồ Gantt"""
    def __init__(self):
        super().__init__()
        self.results_history = []
        self.algorithm_to_runs = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.summary_label = QLabel("Chưa có kết quả")
        layout.addWidget(self.summary_label)

        self.chart = GanttChart()
        layout.addWidget(self.chart)

        # Bảng so sánh
        self.table_group = QGroupBox("So sánh kết quả")
        table_layout = QVBoxLayout()
        self.comparison_table = QTableWidget(0, 5)
        self.comparison_table.setHorizontalHeaderLabels([
            "Thuật toán", "Lần chạy", "Makespan", "Runtime (s)", "Iterations"
        ])
        table_layout.addWidget(self.comparison_table)
        self.table_group.setLayout(table_layout)
        layout.addWidget(self.table_group)

        self.setLayout(layout)

    def update_results(self, result: dict):
        # Lưu lịch sử và cập nhật tóm tắt
        self.results_history.append(result)
        algo = result.get('algorithm', 'N/A')
        makespan = result.get('makespan', 'N/A')
        runtime = result.get('runtime', 'N/A')
        iterations = result.get('iterations', 'N/A')
        self.summary_label.setText(
            f"Thuật toán: {algo} | Makespan: {makespan} | Thời gian: {runtime}s | Vòng lặp: {iterations}"
        )

        schedule = result.get('schedule', [])
        self.chart.render(schedule)

    def update_comparison_table(self):
        # Cập nhật bảng từ results_history
        self.comparison_table.setRowCount(len(self.results_history))
        for row, result in enumerate(self.results_history):
            self.comparison_table.setItem(row, 0, QTableWidgetItem(str(result.get('algorithm', ''))))
            self.comparison_table.setItem(row, 1, QTableWidgetItem(str(result.get('run_index', 1))))
            self.comparison_table.setItem(row, 2, QTableWidgetItem(str(result.get('makespan', ''))))
            self.comparison_table.setItem(row, 3, QTableWidgetItem(str(result.get('runtime', ''))))
            self.comparison_table.setItem(row, 4, QTableWidgetItem(str(result.get('iterations', ''))))

    def add_result(self, result: dict):
        # Lưu thêm metadata cho so sánh
        algo = result.get('algorithm', 'Unknown')
        runs = self.algorithm_to_runs.get(algo, 0) + 1
        self.algorithm_to_runs[algo] = runs
        result_with_index = dict(result)
        result_with_index['run_index'] = runs
        self.update_results(result_with_index)
        self.update_comparison_table()

    def summarize_statistics(self):
        # Tính thống kê theo thuật toán: mean/std runtime, best/worst makespan
        import statistics
        lines = []
        if not self.results_history:
            return "Chưa có kết quả"
        by_algo = {}
        for r in self.results_history:
            by_algo.setdefault(r['algorithm'], []).append(r)
        for algo, rs in by_algo.items():
            runtimes = [float(x['runtime']) for x in rs]
            makespans = [int(x['makespan']) for x in rs]
            mean_rt = statistics.mean(runtimes)
            std_rt = statistics.pstdev(runtimes) if len(runtimes) > 1 else 0.0
            best = min(makespans)
            worst = max(makespans)
            lines.append(f"{algo}: makespan tốt nhất {best}, tệ nhất {worst}, runtime {mean_rt:.3f}±{std_rt:.3f}s (n={len(rs)})")
        return "\n".join(lines)


class ProblemInputWidget(QWidget):
    """Widget để nhập dữ liệu bài toán"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Điều khiển kích thước bài toán
        size_group = QGroupBox("Kích thước Bài toán")
        size_layout = QGridLayout()
        
        size_layout.addWidget(QLabel("Số lượng Công việc:"), 0, 0)
        self.jobs_spin = QSpinBox()
        self.jobs_spin.setRange(2, 20)
        self.jobs_spin.setValue(3)
        self.jobs_spin.valueChanged.connect(self.update_table)
        size_layout.addWidget(self.jobs_spin, 0, 1)
        
        size_layout.addWidget(QLabel("Số lượng Máy:"), 0, 2)
        self.machines_spin = QSpinBox()
        self.machines_spin.setRange(2, 10)
        self.machines_spin.setValue(3)
        self.machines_spin.valueChanged.connect(self.update_table)
        size_layout.addWidget(self.machines_spin, 0, 3)
        
        # Nút quản lý dữ liệu
        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Tạo Dữ liệu Ngẫu nhiên")
        self.generate_btn.clicked.connect(self.generate_random_data)
        btn_layout.addWidget(self.generate_btn)
        
        self.load_btn = QPushButton("Tải từ Tệp")
        self.load_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("Lưu vào Tệp")
        self.save_btn.clicked.connect(self.save_data)
        btn_layout.addWidget(self.save_btn)
        
        size_layout.addLayout(btn_layout, 1, 0, 1, 4)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        # Bảng thời gian xử lý
        table_group = QGroupBox("Ma trận Thời gian Xử lý (Công việc × Máy)")
        table_layout = QVBoxLayout()
        
        self.processing_table = QTableWidget()
        self.update_table()
        table_layout.addWidget(self.processing_table)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        self.setLayout(layout)
    
    def update_table(self):
        """Cập nhật bảng thời gian xử lý"""
        jobs = self.jobs_spin.value()
        machines = self.machines_spin.value()
        
        self.processing_table.setRowCount(jobs)
        self.processing_table.setColumnCount(machines)
        
        # Thiết lập tiêu đề
        job_headers = [f"Công việc {i+1}" for i in range(jobs)]
        machine_headers = [f"Máy {i+1}" for i in range(machines)]
        
        self.processing_table.setVerticalHeaderLabels(job_headers)
        self.processing_table.setHorizontalHeaderLabels(machine_headers)
        
        # Điền giá trị mặc định nếu trống
        for i in range(jobs):
            for j in range(machines):
                if not self.processing_table.item(i, j):
                    item = QTableWidgetItem("5")
                    self.processing_table.setItem(i, j, item)
    
    def generate_random_data(self):
        """Tạo dữ liệu ngẫu nhiên"""
        jobs = self.jobs_spin.value()
        machines = self.machines_spin.value()
        
        for i in range(jobs):
            for j in range(machines):
                random_time = np.random.randint(1, 11)
                item = QTableWidgetItem(str(random_time))
                self.processing_table.setItem(i, j, item)
    
    def get_problem_data(self):
        """Lấy dữ liệu bài toán từ giao diện"""
        jobs = self.jobs_spin.value()
        machines = self.machines_spin.value()
        
        processing_times = []
        for i in range(jobs):
            row = []
            for j in range(machines):
                item = self.processing_table.item(i, j)
                if item and item.text().isdigit():
                    row.append(int(item.text()))
                else:
                    row.append(5)  # giá trị mặc định
            processing_times.append(row)
        
        return {
            'jobs': jobs,
            'machines': machines,
            'processing_times': processing_times
        }
    
    def load_data(self):
        """Tải dữ liệu từ tệp"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Tải Dữ liệu Bài toán", "", "Tệp JSON (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.jobs_spin.setValue(data['jobs'])
                self.machines_spin.setValue(data['machines'])
                self.update_table()
                
                for i, row in enumerate(data['processing_times']):
                    for j, value in enumerate(row):
                        item = QTableWidgetItem(str(value))
                        self.processing_table.setItem(i, j, item)
                        
                QMessageBox.information(self, "Thành công", "Dữ liệu đã được tải thành công!")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
    
    def save_data(self):
        """Lưu dữ liệu ra tệp"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Lưu Dữ liệu Bài toán", "", "Tệp JSON (*.json)")
        if file_path:
            try:
                data = self.get_problem_data()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Thành công", "Dữ liệu đã được lưu thành công!")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể lưu dữ liệu: {str(e)}")


class AlgorithmParametersWidget(QWidget):
    """Widget để cấu hình tham số thuật toán"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Tham số Mô phỏng Tôi luyện
        sa_group = QGroupBox("Tham số Thuật toán Mô phỏng Tôi luyện")
        sa_layout = QGridLayout()
        
        sa_layout.addWidget(QLabel("Nhiệt độ Ban đầu:"), 0, 0)
        self.sa_temp_spin = QDoubleSpinBox()
        self.sa_temp_spin.setRange(1.0, 1000.0)
        self.sa_temp_spin.setValue(100.0)
        sa_layout.addWidget(self.sa_temp_spin, 0, 1)
        
        sa_layout.addWidget(QLabel("Tốc độ Làm lạnh (α):"), 0, 2)
        self.sa_alpha_spin = QDoubleSpinBox()
        self.sa_alpha_spin.setRange(0.8, 0.99)
        self.sa_alpha_spin.setSingleStep(0.01)
        self.sa_alpha_spin.setValue(0.95)
        sa_layout.addWidget(self.sa_alpha_spin, 0, 3)
        
        sa_layout.addWidget(QLabel("Nhiệt độ Tối thiểu:"), 1, 0)
        self.sa_min_temp_spin = QDoubleSpinBox()
        self.sa_min_temp_spin.setRange(0.0001, 10.0)
        self.sa_min_temp_spin.setDecimals(4)
        self.sa_min_temp_spin.setValue(0.001)
        sa_layout.addWidget(self.sa_min_temp_spin, 1, 1)

        sa_layout.addWidget(QLabel("Số vòng lặp tối đa:"), 1, 2)
        self.sa_max_iter_spin = QSpinBox()
        self.sa_max_iter_spin.setRange(1, 1000000)
        self.sa_max_iter_spin.setValue(1000)
        sa_layout.addWidget(self.sa_max_iter_spin, 1, 3)

        sa_group.setLayout(sa_layout)
        layout.addWidget(sa_group)

        # Tham số Đàn kiến (ACO)
        aco_group = QGroupBox("Tham số Thuật toán Đàn kiến")
        aco_layout = QGridLayout()

        aco_layout.addWidget(QLabel("Số lượng kiến:"), 0, 0)
        self.aco_ants_spin = QSpinBox()
        self.aco_ants_spin.setRange(1, 10000)
        self.aco_ants_spin.setValue(30)
        aco_layout.addWidget(self.aco_ants_spin, 0, 1)

        aco_layout.addWidget(QLabel("Alpha (ảnh hưởng pheromone):"), 0, 2)
        self.aco_alpha_spin = QDoubleSpinBox()
        self.aco_alpha_spin.setRange(0.0, 10.0)
        self.aco_alpha_spin.setValue(1.0)
        aco_layout.addWidget(self.aco_alpha_spin, 0, 3)

        aco_layout.addWidget(QLabel("Beta (ảnh hưởng heuristic):"), 1, 0)
        self.aco_beta_spin = QDoubleSpinBox()
        self.aco_beta_spin.setRange(0.0, 10.0)
        self.aco_beta_spin.setValue(2.0)
        aco_layout.addWidget(self.aco_beta_spin, 1, 1)

        aco_layout.addWidget(QLabel("Tỷ lệ bay hơi:"), 1, 2)
        self.aco_evap_spin = QDoubleSpinBox()
        self.aco_evap_spin.setRange(0.0, 1.0)
        self.aco_evap_spin.setSingleStep(0.01)
        self.aco_evap_spin.setValue(0.5)
        aco_layout.addWidget(self.aco_evap_spin, 1, 3)

        aco_layout.addWidget(QLabel("Số thế hệ tối đa:"), 2, 0)
        self.aco_max_gen_spin = QSpinBox()
        self.aco_max_gen_spin.setRange(1, 1000000)
        self.aco_max_gen_spin.setValue(200)
        aco_layout.addWidget(self.aco_max_gen_spin, 2, 1)

        aco_group.setLayout(aco_layout)
        layout.addWidget(aco_group)

        # Tham số Greedy (tối giản)
        greedy_group = QGroupBox("Tham số Thuật toán Tham lam")
        greedy_layout = QGridLayout()
        greedy_layout.addWidget(QLabel("Chiến lược:"), 0, 0)
        self.greedy_strategy_combo = QComboBox()
        self.greedy_strategy_combo.addItems(["SPT", "LPT", "Random"])  # ví dụ chiến lược
        greedy_layout.addWidget(self.greedy_strategy_combo, 0, 1)
        greedy_group.setLayout(greedy_layout)
        layout.addWidget(greedy_group)

        # Tham số chung
        general_group = QGroupBox("Thiết lập chung")
        general_layout = QGridLayout()
        general_layout.addWidget(QLabel("Seed ngẫu nhiên:"), 0, 0)
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 2_147_483_647)
        self.seed_spin.setValue(42)
        general_layout.addWidget(self.seed_spin, 0, 1)

        self.use_seed_check = QCheckBox("Sử dụng seed cố định")
        self.use_seed_check.setChecked(True)
        general_layout.addWidget(self.use_seed_check, 0, 2, 1, 2)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        self.setLayout(layout)

    # ==== Getters cho tham số ====
    def get_sa_parameters(self):
        return {
            'initial_temp': float(self.sa_temp_spin.value()),
            'cooling_rate': float(self.sa_alpha_spin.value()),
            'min_temp': float(self.sa_min_temp_spin.value()),
            'max_iterations': int(self.sa_max_iter_spin.value())
        }

    def get_aco_parameters(self):
        return {
            'num_ants': int(self.aco_ants_spin.value()),
            'alpha': float(self.aco_alpha_spin.value()),
            'beta': float(self.aco_beta_spin.value()),
            'evaporation_rate': float(self.aco_evap_spin.value()),
            'max_generations': int(self.aco_max_gen_spin.value())
        }

    def get_greedy_parameters(self):
        return {
            'strategy': self.greedy_strategy_combo.currentText()
        }