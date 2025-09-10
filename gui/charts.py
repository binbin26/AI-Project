from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class GanttChart(QWidget):
    def __init__(self):
        super().__init__()
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def render(self, schedule):
        # schedule: list of {job, machine, start, duration}
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if not schedule:
            self.canvas.draw()
            return

        machines = sorted({item['machine'] for item in schedule})
        machine_to_y = {m: idx for idx, m in enumerate(machines)}
        colors = {}
        cmap = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
                '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

        for item in schedule:
            job = item['job']
            machine = item['machine']
            start = item['start']
            duration = item['duration']
            y = machine_to_y[machine]
            if job not in colors:
                colors[job] = cmap[job % len(cmap)]
            ax.broken_barh([(start, duration)], (y - 0.4, 0.8), facecolors=colors[job])
            ax.text(start + duration / 2, y, f"J{job+1}", va='center', ha='center', color='white', fontsize=8)

        ax.set_yticks(list(machine_to_y.values()))
        ax.set_yticklabels([f"Máy {m+1}" for m in machines])
        ax.set_xlabel("Thời gian")
        ax.set_ylabel("Máy")
        ax.grid(True, axis='x', linestyle='--', alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw()

    def save_image(self, file_path: str):
        try:
            self.figure.savefig(file_path, dpi=150, bbox_inches='tight')
            return True
        except Exception:
            return False


