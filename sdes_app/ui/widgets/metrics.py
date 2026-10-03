from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


def elapsed_text(seconds):
    return f"{seconds * 1000:.3f} ms" if seconds < 1 else f"{seconds:.3f} s"


class MetricsRow(QWidget):
    def __init__(self, labels):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 4, 0, 12)
        row.setSpacing(16)
        self.values = []
        for text in labels:
            column = QVBoxLayout()
            value = QLabel("—")
            value.setObjectName("metric")
            label = QLabel(text)
            label.setObjectName("hint")
            column.addWidget(value)
            column.addWidget(label)
            row.addLayout(column, 1)
            self.values.append(value)

    def set_values(self, *values):
        for label, value in zip(self.values, values):
            label.setText(str(value))

    def reset(self):
        self.set_values(*("—" for _ in self.values))
