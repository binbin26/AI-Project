#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Job Shop Scheduling Problem GUI - Vietnamese Version
Bài toán Lập lịch Phân xưởng - Phiên bản Tiếng Việt

Author: AI Project Team - UEH
Version: 1.0
"""

import sys
from gui.main_window import JobShopSchedulingGUI


def main():
    """Hàm chính để chạy ứng dụng"""
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt
    
    app = QApplication(sys.argv)
    
    # Thiết lập thuộc tính ứng dụng
    app.setApplicationName("Giải Bài toán Lập lịch Phân xưởng")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("UEH - Dự án AI")
    
    # Áp dụng style hiện đại
    app.setStyle('Fusion')
    
    # Cấu hình matplotlib backend
    import matplotlib
    matplotlib.use('Qt5Agg')
    
    try:
        # Tạo và hiển thị cửa sổ chính
        window = JobShopSchedulingGUI()
        window.show()
        
        # Hiển thị thông báo khởi động
        QMessageBox.information(None, "Chào mừng", 
                               "Chào mừng bạn đến với chương trình Giải bài toán Lập lịch Phân xưởng!\n\n"
                               "Nhấn F1 để xem hướng dẫn sử dụng.")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        QMessageBox.critical(None, "Lỗi khởi động", f"Không thể khởi động ứng dụng:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()