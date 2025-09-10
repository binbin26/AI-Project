# gui/main_window.py
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QTabWidget, QGroupBox, QLabel, QLineEdit, QPushButton, 
    QComboBox, QSpinBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem,
    QTextEdit, QProgressBar, QCheckBox, QSplitter, QFrame, QMessageBox,
    QFileDialog, QSlider, QScrollArea, QMenuBar, QAction
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap

from gui.widgets import ProblemInputWidget, AlgorithmParametersWidget, ResultsWidget
from algorithms.optimization_thread import OptimizationThread
from utils.file_handling import attach_checksum, validate_loaded_project
import time
import json
import pandas as pd
import os
import logging


class JobShopSchedulingGUI(QMainWindow):
    """Ứng dụng GUI Chính"""
    
    def __init__(self):
        super().__init__()
        self.optimization_thread = None
        self.batch_algorithms = []
        self.current_batch_index = 0
        self.original_algorithm = ""
        self.init_ui()
        
    def init_ui(self):
        """Khởi tạo giao diện người dùng"""
        self.setWindowTitle("Bài toán Lập lịch Phân xưởng - So sánh Mô phỏng Tôi luyện, Tham lam, Đàn kiến")
        self.setGeometry(100, 100, 1400, 900)
        # Cấu hình logging
        logs_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(logs_dir, 'app.log'),
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
        )
        
        # Thiết lập style ứng dụng
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #2196F3;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        # Tạo widget trung tâm và layout chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Panel trái với các tab
        left_panel = QTabWidget()
        left_panel.setMaximumWidth(500)
        
        # Tab Nhập Dữ liệu Bài toán
        self.problem_input = ProblemInputWidget()
        left_panel.addTab(self.problem_input, "Nhập Dữ liệu Bài toán")
        
        # Tab Tham số Thuật toán
        self.algorithm_params = AlgorithmParametersWidget()
        left_panel.addTab(self.algorithm_params, "Tham số Thuật toán")
        
        # Tab Bảng Điều khiển
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # Lựa chọn thuật toán
        algo_group = QGroupBox("Lựa chọn Thuật toán & Điều khiển")
        algo_layout = QVBoxLayout()
        
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["Mô phỏng SA", "Thuật toán Greedy", "Thuật toán ACO"])
        algo_layout.addWidget(QLabel("Chọn Thuật toán:"))
        algo_layout.addWidget(self.algorithm_combo)
        
        # Lựa chọn số lần chạy
        runs_layout = QHBoxLayout()
        runs_layout.addWidget(QLabel("Số lần chạy:"))
        self.runs_spin = QSpinBox()
        self.runs_spin.setRange(1, 100)
        self.runs_spin.setValue(1)
        runs_layout.addWidget(self.runs_spin)
        algo_layout.addLayout(runs_layout)

        # Các nút điều khiển
        button_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("Chạy Thuật toán")
        self.run_btn.clicked.connect(self.run_algorithm)
        button_layout.addWidget(self.run_btn)
        
        self.run_all_btn = QPushButton("Chạy Tất cả & So sánh")
        self.run_all_btn.clicked.connect(self.run_all_algorithms)
        button_layout.addWidget(self.run_all_btn)
        
        self.stop_btn = QPushButton("Dừng")
        self.stop_btn.clicked.connect(self.stop_algorithm)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        algo_layout.addLayout(button_layout)
        
        # Thanh tiến trình
        self.progress_bar = QProgressBar()
        algo_layout.addWidget(QLabel("Tiến trình:"))
        algo_layout.addWidget(self.progress_bar)
        
        algo_group.setLayout(algo_layout)
        control_layout.addWidget(algo_group)
        
        # Nhật ký đầu ra
        log_group = QGroupBox("Nhật ký Thuật toán")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        control_layout.addWidget(log_group)
        
        left_panel.addTab(control_panel, "Bảng Điều khiển")

        # Tab Nhật ký (tìm kiếm/lọc)
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Tìm trong nhật ký:"))
        self.log_search = QLineEdit()
        self.log_search.textChanged.connect(self.apply_log_filter)
        search_row.addWidget(self.log_search)
        logs_layout.addLayout(search_row)
        self.logs_view = QTextEdit()
        self.logs_view.setReadOnly(True)
        logs_layout.addWidget(self.logs_view)
        left_panel.addTab(logs_tab, "Nhật ký")

        self._log_lines = []
        main_layout.addWidget(left_panel)
        
        # Panel phải - Kết quả
        self.results_widget = ResultsWidget()
        main_layout.addWidget(self.results_widget)
        
        # Thiết lập tỷ lệ layout
        main_layout.setStretch(0, 1)  # Panel trái
        main_layout.setStretch(1, 2)  # Panel phải (kết quả)
        
        # Menu bar
        self.create_menu_bar()
    
    def create_menu_bar(self):
        """Tạo thanh menu"""
        menubar = self.menuBar()
        
        # Menu Tệp
        file_menu = menubar.addMenu('Tệp')
        
        # Tải dự án
        load_project_action = file_menu.addAction('Tải Dự án')
        load_project_action.setShortcut('Ctrl+O')
        load_project_action.triggered.connect(self.load_project)
        
        # Lưu dự án
        save_project_action = file_menu.addAction('Lưu Dự án')
        save_project_action.setShortcut('Ctrl+S')
        save_project_action.triggered.connect(self.save_project)
        
        file_menu.addSeparator()
        
        # Xuất kết quả
        export_results_action = file_menu.addAction('Xuất Kết quả')
        export_results_action.setShortcut('Ctrl+E')
        export_results_action.triggered.connect(self.export_results)
        
        file_menu.addSeparator()
        
        # Thoát
        exit_action = file_menu.addAction('Thoát')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        
        # Menu Xuất
        export_menu = menubar.addMenu('Xuất')
        export_gantt_action = export_menu.addAction('Xuất biểu đồ Gantt...')
        export_gantt_action.triggered.connect(self.export_gantt_image)
        export_schedule_action = export_menu.addAction('Xuất Schedule (JSON)...')
        export_schedule_action.triggered.connect(self.export_schedule_json)

        # Menu Trợ giúp
        help_menu = menubar.addMenu('Trợ giúp')
        
        # Về chương trình
        about_action = help_menu.addAction('Về chương trình')
        about_action.triggered.connect(self.show_about)
        
        # Hướng dẫn sử dụng
        guide_action = help_menu.addAction('Hướng dẫn sử dụng')
        guide_action.setShortcut('F1')
        guide_action.triggered.connect(self.show_guide)
    
    def run_algorithm(self):
        """Chạy thuật toán được chọn"""
        if self.optimization_thread and self.optimization_thread.isRunning():
            QMessageBox.warning(self, "Cảnh báo", "Thuật toán đang chạy!")
            return
        
        # Lấy dữ liệu bài toán và tham số
        problem_data = self.problem_input.get_problem_data()
        algorithm = self.algorithm_combo.currentText()
        
        if algorithm == "Mô phỏng SA":
            params = self.algorithm_params.get_sa_parameters()
            algo_key = "SA"
        elif algorithm == "Thuật toán Greedy":
            params = self.algorithm_params.get_greedy_parameters()
            algo_key = "Greedy"
        else:  # Thuật toán ACO
            params = self.algorithm_params.get_aco_parameters()
            algo_key = "ACO"
        
        # Lưu cấu hình batch runs
        self._pending_runs = getattr(self, '_pending_runs', 0)
        if self._pending_runs == 0:
            self._pending_runs = max(1, int(self.runs_spin.value()))
        self._current_algo_key = algo_key
        self._current_problem = problem_data
        self._current_params = params

        # Thiết lập và bắt đầu thread tối ưu cho một lần chạy
        self.optimization_thread = OptimizationThread(self._current_algo_key, self._current_problem, self._current_params)
        self.optimization_thread.progress_updated.connect(self.progress_bar.setValue)
        self.optimization_thread.result_ready.connect(self.on_algorithm_finished)
        self.optimization_thread.log_updated.connect(self.update_log)
        
        # Cập nhật trạng thái UI
        self.run_btn.setEnabled(False)
        self.run_all_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        
        # Bắt đầu thuật toán
        self.optimization_thread.start()
    
    def run_all_algorithms(self):
        """Chạy tất cả thuật toán để so sánh"""
        # Xóa kết quả trước đó
        self.results_widget.results_history.clear()
        self.results_widget.update_comparison_table()
        
        # Hiển thị thông báo bắt đầu
        self.update_log("Bắt đầu chạy tất cả thuật toán để so sánh...")
        
        # Thiết lập danh sách thuật toán
        self.batch_algorithms = ["Mô phỏng SA", "Thuật toán Greedy", "Thuật toán ACO"]
        self.current_batch_index = 0
        
        # Lưu thuật toán hiện tại
        self.original_algorithm = self.algorithm_combo.currentText()
        
        # Bắt đầu với thuật toán đầu tiên
        self.algorithm_combo.setCurrentText(self.batch_algorithms[0])
        self.run_algorithm()
    
    def on_batch_algorithm_finished(self, result):
        """Xử lý khi một thuật toán trong batch hoàn thành"""
        self.results_widget.update_results(result)
        
        # Chuyển sang thuật toán tiếp theo nếu còn
        self.current_batch_index += 1
        if self.current_batch_index < len(self.batch_algorithms):
            # Delay ngắn trước khi chạy thuật toán tiếp theo
            QTimer.singleShot(1000, self.run_next_in_batch)
        else:
            # Hoàn thành tất cả
            self.update_log("Đã hoàn thành chạy tất cả thuật toán!")
            self.reset_ui_state()
    
    def run_next_in_batch(self):
        """Chạy thuật toán tiếp theo trong batch"""
        if self.current_batch_index < len(self.batch_algorithms):
            self.algorithm_combo.setCurrentText(self.batch_algorithms[self.current_batch_index])
            self.run_algorithm()
    
    def stop_algorithm(self):
        """Dừng thuật toán đang chạy"""
        if self.optimization_thread and self.optimization_thread.isRunning():
            self.optimization_thread.terminate()
            self.optimization_thread.wait()
            
            self.update_log("Thuật toán đã được dừng bởi người dùng.")
            self.reset_ui_state()
    
    def on_algorithm_finished(self, result):
        """Xử lý khi thuật toán hoàn thành"""
        # Lưu kết quả vào bảng và điều phối batch/loops
        self.results_widget.add_result(result)

        # Batch theo thuật toán khác nhau
        if len(self.batch_algorithms) > 0 and self.current_batch_index < len(self.batch_algorithms):
            self.on_batch_algorithm_finished(result)
            return

        # Multi-run cho cùng thuật toán
        self._pending_runs -= 1
        if self._pending_runs > 0:
            # chạy tiếp lần kế tiếp sau một nhịp ngắn
            QTimer.singleShot(200, self.run_algorithm)
            return

        self.update_log(f"Thuật toán hoàn thành! Thời gian hoàn thành tốt nhất: {result['makespan']}")
        self.reset_ui_state()
    
    def reset_ui_state(self):
        """Reset trạng thái UI sau khi thuật toán hoàn thành"""
        self.run_btn.setEnabled(True)
        self.run_all_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Khôi phục thuật toán gốc nếu có
        if self.original_algorithm:
            self.algorithm_combo.setCurrentText(self.original_algorithm)
            self.original_algorithm = ""
        
        # Xóa trạng thái batch
        self.batch_algorithms = []
        self.current_batch_index = 0
    
    def update_log(self, message):
        """Cập nhật nhật ký"""
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        self.log_text.append(line)
        self.log_text.ensureCursorVisible()
        self._log_lines.append(line)
        self.apply_log_filter()
        logging.info(message)

    def apply_log_filter(self):
        query = (self.log_search.text() or '').lower()
        buf = []
        for line in self._log_lines:
            if query in line.lower():
                buf.append(line)
        self.logs_view.setPlainText("\n".join(buf))
    
    def load_project(self):
        """Tải dự án từ tệp"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Tải Dự án", "", "Tệp Dự án (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                validate_loaded_project(project_data)
                
                # Tải dữ liệu bài toán
                if 'problem_data' in project_data:
                    data = project_data['problem_data']
                    self.problem_input.jobs_spin.setValue(data['jobs'])
                    self.problem_input.machines_spin.setValue(data['machines'])
                    self.problem_input.update_table()
                    
                    for i, row in enumerate(data['processing_times']):
                        for j, value in enumerate(row):
                            item = QTableWidgetItem(str(value))
                            self.problem_input.processing_table.setItem(i, j, item)
                
                # Tải tham số thuật toán
                if 'algorithm_params' in project_data:
                    params = project_data['algorithm_params']
                    
                    # SA params
                    if 'sa' in params:
                        sa_params = params['sa']
                        self.algorithm_params.sa_temp_spin.setValue(sa_params.get('initial_temp', 100.0))
                        self.algorithm_params.sa_alpha_spin.setValue(sa_params.get('cooling_rate', 0.95))
                        self.algorithm_params.sa_min_temp_spin.setValue(sa_params.get('min_temp', 0.001))
                        self.algorithm_params.sa_max_iter_spin.setValue(sa_params.get('max_iterations', 1000))
                    
                    # ACO params
                    if 'aco' in params:
                        aco_params = params['aco']
                        self.algorithm_params.aco_ants_spin.setValue(aco_params.get('num_ants', 30))
                        self.algorithm_params.aco_alpha_spin.setValue(aco_params.get('alpha', 1.0))
                        self.algorithm_params.aco_beta_spin.setValue(aco_params.get('beta', 2.0))
                        self.algorithm_params.aco_evap_spin.setValue(aco_params.get('evaporation_rate', 0.5))
                        self.algorithm_params.aco_max_gen_spin.setValue(aco_params.get('max_generations', 200))
                    
                    # General params
                    if 'general' in params:
                        gen_params = params['general']
                        self.algorithm_params.seed_spin.setValue(gen_params.get('seed', 42))
                        self.algorithm_params.use_seed_check.setChecked(gen_params.get('use_seed', True))
                
                QMessageBox.information(self, "Thành công", "Dự án đã được tải thành công!")
                self.update_log("Đã tải dự án từ tệp.")
                
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể tải dự án: {str(e)}")
    
    def save_project(self):
        """Lưu dự án ra tệp"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Lưu Dự án", "", "Tệp Dự án (*.json)")
        if file_path:
            try:
                project_data = {
                    'problem_data': self.problem_input.get_problem_data(),
                    'algorithm_params': {
                        'sa': self.algorithm_params.get_sa_parameters(),
                        'aco': self.algorithm_params.get_aco_parameters(),
                        'greedy': self.algorithm_params.get_greedy_parameters(),
                        'general': {
                            'seed': self.algorithm_params.seed_spin.value(),
                            'use_seed': self.algorithm_params.use_seed_check.isChecked()
                        }
                    },
                    'results_history': self.results_widget.results_history
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(attach_checksum(project_data), f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Thành công", "Dự án đã được lưu thành công!")
                self.update_log("Đã lưu dự án vào tệp.")
                
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể lưu dự án: {str(e)}")
    
    def export_results(self):
        """Xuất kết quả ra tệp CSV"""
        if not self.results_widget.results_history:
            QMessageBox.warning(self, "Cảnh báo", "Không có kết quả để xuất!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Xuất Kết quả", "", "Tệp CSV (*.csv)")
        if file_path:
            try:
                # Tạo DataFrame từ kết quả
                data = []
                for result in self.results_widget.results_history:
                    data.append({
                        'Thuật toán': result['algorithm'],
                        'Thời gian Hoàn thành': result['makespan'],
                        'Thời gian Chạy (giây)': result['runtime'],
                        'Số Vòng lặp': result['iterations']
                    })
                
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                
                QMessageBox.information(self, "Thành công", "Kết quả đã được xuất thành công!")
                self.update_log("Đã xuất kết quả ra tệp CSV.")
                
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể xuất kết quả: {str(e)}")

    def export_gantt_image(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Xuất biểu đồ Gantt", "", "Hình ảnh (*.png *.svg)")
        if file_path:
            ok = self.results_widget.chart.save_image(file_path)
            if ok:
                QMessageBox.information(self, "Thành công", "Đã lưu biểu đồ Gantt!")
                self.update_log(f"Đã xuất biểu đồ Gantt: {file_path}")
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể lưu biểu đồ Gantt.")

    def export_schedule_json(self):
        if not self.results_widget.results_history:
            QMessageBox.warning(self, "Cảnh báo", "Chưa có kết quả để xuất!")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Xuất Schedule (JSON)", "", "Tệp JSON (*.json)")
        if file_path:
            try:
                data = self.results_widget.results_history[-1]
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Thành công", "Đã xuất schedule JSON!")
                self.update_log(f"Đã xuất schedule JSON: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể xuất schedule: {str(e)}")
    
    def show_about(self):
        """Hiển thị thông tin về chương trình"""
        QMessageBox.about(self, "Về chương trình", 
                         """
                         <h3>Bài toán Lập lịch Phân xưởng</h3>
                         <p><b>Phiên bản:</b> 1.0</p>
                         <p><b>Mô tả:</b> Chương trình so sánh hiệu suất của các thuật toán:</p>
                         <ul>
                         <li>Mô phỏng Tôi luyện (Simulated Annealing)</li>
                         <li>Thuật toán Tham lam (Greedy Algorithm)</li>  
                         <li>Thuật toán Đàn kiến (Ant Colony Optimization)</li>
                         </ul>
                         <p><b>Phát triển bởi:</b> Nhóm AI Project - UEH</p>
                         <p><b>Ngôn ngữ:</b> Python với PyQt5 & Matplotlib</p>
                         """)
    
    def show_guide(self):
        """Hiển thị hướng dẫn sử dụng"""
        guide_text = """
        <h3>HƯỚNG DẪN SỬ DỤNG</h3>
        
        <h4>1. NHẬP DỮ LIỆU BÀI TOÁN:</h4>
        <ul>
        <li>Thiết lập số lượng công việc và máy</li>
        <li>Tạo dữ liệu ngẫu nhiên hoặc nhập thủ công</li>
        <li>Có thể lưu/tải dữ liệu từ tệp JSON</li>
        </ul>
        
        <h4>2. CẤU HÌNH THAM SỐ:</h4>
        <ul>
        <li>Điều chỉnh các tham số cho từng thuật toán</li>
        <li>Thiết lập seed để đảm bảo kết quả lặp lại</li>
        </ul>
        
        <h4>3. CHẠY THUẬT TOÁN:</h4>
        <ul>
        <li>Chọn thuật toán muốn chạy</li>
        <li>Nhấn "Chạy Thuật toán" hoặc "Chạy Tất cả"</li>
        <li>Theo dõi tiến trình và nhật ký</li>
        </ul>
        
        <h4>4. PHÂN TÍCH KẾT QUẢ:</h4>
        <ul>
        <li>Xem biểu đồ Gantt và kết quả tóm tắt</li>
        <li>So sánh các thuật toán trong bảng</li>
        <li>Xuất kết quả ra tệp CSV</li>
        </ul>
        
        <h4>5. QUẢN LÝ DỰ ÁN:</h4>
        <ul>
        <li>Lưu toàn bộ dự án để sử dụng sau (Ctrl+S)</li>
        <li>Tải dự án đã lưu (Ctrl+O)</li>
        <li>Xuất kết quả CSV (Ctrl+E)</li>
        </ul>
        
        <p><b>Phím tắt:</b> F1 - Trợ giúp, Ctrl+Q - Thoát</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Hướng dẫn sử dụng")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()